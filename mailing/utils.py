# -*- coding: utf-8 -*-
# Copyright (c) 2016 Aladom SAS & Hosting Dvpt SAS
from functools import lru_cache
import logging
import re
import warnings

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.mail import EmailMultiAlternatives
from django.core.signing import Signer
from django.urls import reverse
from django.db import transaction
from django.template.backends.django import DjangoTemplates
from django.utils import timezone
from django.utils.html import strip_tags

from .conf import UNEXISTING_CAMPAIGN_FAIL_SILENTLY, SUBSCRIPTION_SIGNING_SALT
from .models import Mail, Campaign, Blacklist

__all__ = [
    'render_mail', 'queue_mail', 'send_mail', 'html_to_text', 'mail_logger',
    'get_template_backend',
]

mail_logger = logging.getLogger('mailing.mail')

script_tags_regex = re.compile(r'<script(\s.*)?>.*</script>', re.I | re.S)
style_tags_regex = re.compile(r'<style(\s.*)?>.*</style>', re.I | re.S)
a_tags_regex = re.compile(
   r'''<a\s([^>]*\s)?href=(?P<url>("[^"]+"|'[^']+'))[^>]*>(?P<text>.*?)</a>''',
   re.I | re.S)
img_tags_regex = re.compile(
   r'''<img\s([^>]*\s)?alt=(?P<alt>("[^"]+"|'[^']+'))[^>]*>''',
   re.I | re.S)


@lru_cache()
def get_template_backend():
    from django.template import engines
    for engine in engines.all():
        if isinstance(engine, DjangoTemplates):
            return engine
    raise ImproperlyConfigured("No DjangoTemplates backend is configured")


class NoMoreRecipients(ValueError):
    pass


def AutoescapeTemplate(value):
    return get_template_backend().from_string(
        '{% autoescape off %}' + value + '{% endautoescape %}')


def _a_to_text(m):
    text = m.group('text')
    url = m.group('url')[1:-1]
    if url == text:
        return text
    return '{text} ({url})'.format(
        url=url,
        text=text,
    )


def _img_to_text(m):
    return m.group('alt')[1:-1]


def html_to_text(html):
    """Convert an HTML content to readable plain text content.
    - Remove <script></script> contents
    - Remove HTML tags
    """
    text = a_tags_regex.sub(_a_to_text, html)
    text = img_tags_regex.sub(_img_to_text, text)
    text = style_tags_regex.sub('', text)
    text = script_tags_regex.sub('', text)
    text = strip_tags(text)
    return text


@transaction.atomic
def render_mail(subject, html_template, headers, context=None, **kwargs):
    """Create and return a Mail instance.

    - `subject`: The subject of the mail, may contain template variables.
    - `html_template`: The template of the HTML body. May be a Template
      instance or a string.
    - `headers`: A dictionary of mail headers. Values may contain template
      variables. You must at least set the 'To' header. If you don't set the
      'From' header, DEFAULT_FROM_EMAIL from your settings.py will be used.
    - `context`: Context dictionnary to pass when rendering templates.

    You can also pass the following extra keyword arguments:

        - `text_template`: The template of the plain text body. May be a
          Template instance or a string. If you don't set it, it will be
          automatically generated from the HTML when the mail will be sent.
        - `campaign`: The Campaign instance of the mail if any.
        - `scheduled_on`: A `datetime.datetime` instance representing the date
          when the mail must be sent.
    """
    headers = headers or {}
    if 'To' not in headers:
        raise ValueError("You must set the 'To' header.")
    if not hasattr(html_template, 'render'):
        # Check Template instance (see #10)
        html_template = get_template_backend().from_string(html_template)

    ignore_blacklist = kwargs.get('ignore_blacklist')

    headers.setdefault('From', settings.DEFAULT_FROM_EMAIL)
    campaign = kwargs.get('campaign')

    subject = AutoescapeTemplate(subject).render(context)

    mail = Mail(subject=subject, status=Mail.STATUS_DRAFT)
    if 'campaign' in kwargs:
        mail.campaign = kwargs['campaign']
    if 'scheduled_on' in kwargs:
        mail.scheduled_on = kwargs['scheduled_on']
    mail.save()

    mailing_ctx = {
        'subject': subject,
        'mirror': mail.get_absolute_url(),
    }
    if campaign:
        mailing_ctx['campaign'] = campaign
    context.update({'mailing': mailing_ctx})

    rendered_headers = dict((name, AutoescapeTemplate(value).render(context))
                            for name, value in headers.items())

    rendered_headers['To'], rendered_headers['Cc'], rendered_headers['Bcc'] = \
        Blacklist.objects.filter_blacklisted(
            rendered_headers.get('To'),
            rendered_headers.get('Cc'),
            rendered_headers.get('Bcc'),
            ignore=ignore_blacklist)
    if not rendered_headers['To']:
        mail.delete()
        raise NoMoreRecipients("All main recipients are blacklisted")
    if not rendered_headers['Cc']:
        del rendered_headers['Cc']
    if not rendered_headers['Bcc']:
        del rendered_headers['Bcc']

    if campaign:
        actual_to = []
        for email in rendered_headers['To'].split(','):
            email = email.strip()
            if campaign.is_subscribed(email):
                actual_to.append(email)
        if not actual_to:
            mail.delete()
            raise NoMoreRecipients("All main recipients left are unsubscribed")
        rendered_headers['To'] = ', '.join(actual_to)
        email = actual_to[0]
        match = re.match(r'.*\s<([^<> ]+)>', email)
        if match:
            email = match.group(1)
        mailing_ctx['subscriptions_management_url'] = \
            get_subscriptions_management_url(email)

    mailing_ctx['headers'] = rendered_headers
    context.update({'mailing': mailing_ctx})

    html_body = html_template.render(context)

    text_body = ""
    if 'text_template' in kwargs:
        text_template = kwargs['text_template']
        if not hasattr(text_template, 'render'):
            text_template = AutoescapeTemplate(text_template)
        text_body = text_template.render(context)

    mail.html_body = html_body
    mail.text_body = text_body
    mail.save()

    for name, value in rendered_headers.items():
        mail.headers.create(name=name, value=value)

    for attachments in ['static_attachments', 'dynamic_attachments']:
        """Handle both static and dynamic attachments with the same logic."""
        for attachment in kwargs.get(attachments, []):
            mail_attachments = getattr(mail, attachments)
            if isinstance(attachment, dict):
                mail_attachments.create(**attachment)
            else:
                mail_attachments.create(attachment=attachment)

    return mail


def render_campaign_mail(campaign, context=None, **kwargs):
    """Create and return a Mail instance from a Campaign and given context.
    May raise IOError or OSError if reading the template file failed. It's up
    to you to catch these exceptions and handle them properly.
    """
    subject = kwargs.pop('subject', campaign.get_subject())
    html_template = kwargs.pop('html_template', campaign.get_template())
    headers = dict(campaign.extra_headers.items())
    headers.update(kwargs.pop('extra_headers', None) or {})
    static_attachments = kwargs.pop('static_attachments', [])
    for attachment in campaign.static_attachments.all():
        static_attachments.append({
            'filename': attachment.filename,
            'mime_type': attachment.mime_type,
            'attachment': attachment.attachment
        })
    kwargs['campaign'] = campaign
    kwargs['static_attachments'] = static_attachments
    return render_mail(subject, html_template, headers, context, **kwargs)


def queue_mail(campaign_key=None, context=None, extra_headers=None, **kwargs):
    """Create and save a Mail instance from a Campaign and given context.

    You may omit `campaign_key` (or set it to None) to send a mail that not
    realted to any campaign. In this case, you must set `subject` and
    `html_template` keyword arguments or it will raise a KeyError. Please also
    think about filling in the 'To' header in `extra_headers`.

    If fail_silently is True and the requested campaign does not exist, emit a
    warning and return None.
    If fail_silently is False and the requested campaign does not exist, raise
    Campaign.DoesNotExist.
    If fail_silently is not passed, the default value will be retrieved from
    the app config (See conf.UNEXISTING_CAMPAIGN_FAIL_SILENTLY).

    If the campaign is not enabled, the mail is not queued and None is
    returned. (See Campaign.is_enabled).

    May raise IOError or OSError if reading the template file failed. It's up
    to you to catch these exceptions and handle them properly.

    Return the saved Mail instance.
    """
    fail_silently = kwargs.pop('fail_silently',
                               UNEXISTING_CAMPAIGN_FAIL_SILENTLY)
    try:
        if campaign_key is None:
            subject = kwargs.pop('subject')
            html_template = kwargs.pop('html_template')
            mail = render_mail(subject, html_template, extra_headers, context,
                               **kwargs)
        else:
            try:
                campaign = Campaign.objects.get(key=campaign_key)
            except Campaign.DoesNotExist as e:
                if fail_silently:
                    warnings.warn(
                        ("Skip sending campaign '{}' because it "
                         "does not exist.").format(campaign_key))
                    return None
                else:
                    raise e
            if not campaign.is_enabled:
                return None
            kwargs['extra_headers'] = extra_headers
            mail = render_campaign_mail(campaign, context, **kwargs)
    except NoMoreRecipients as e:
        mail_logger.debug(
            "Email not queued because of empty recipients list.", exc_info=e)
        return None
    mail.status = Mail.STATUS_PENDING
    mail.save()
    return mail


def send_mail(mail):
    """Send a Mail instance.
    Note that this does not alter the mail instance.
    It is the responsibility of the caller to set `status` to Mail.STATUS_SENT
    and `sent_on` to the current datetime.

    Return the `EmailMultiAlternatives` instance of the sent mail.
    """
    subject = mail.subject
    html_body = mail.html_body
    text_body = mail.text_body or html_to_text(html_body)
    headers = mail.get_headers()

    from_email = headers.pop('From', settings.DEFAULT_FROM_EMAIL)
    to_emails = filter(None, map(
        str.strip, headers.pop('To', '').split(',')))
    cc_emails = filter(None, map(
        str.strip, headers.pop('Cc', '').split(',')))
    bcc_emails = filter(None, map(
        str.strip, headers.pop('Bcc', '').split(',')))

    msg = EmailMultiAlternatives(subject, text_body, from_email, to_emails,
                                 cc=cc_emails, bcc=bcc_emails, headers=headers)
    msg.attach_alternative(html_body, 'text/html')

    for attachment in mail.get_attachments():
        msg.attach(attachment.get_file_name(), attachment.get_file_content(),
                   attachment.get_mime_type())

    msg.send()
    return msg


def send_queued_mails():
    """Send Mail objects with `status` Mail.STATUS_PENDING and having
    `scheduled_on` set on a past date.

    Set `status` Mail.STATUS_SENT and `sent_on` to current datetime for each
    mail successfully sent.
    Set `status` Mail.STATUS_FAILURE and appropriate `failure_reason` for each
    mail that failed.

    Return a 2-tuple (nb_successes, nb_failures) representing the number of
    mails successfully sent and failures.
    """
    now = timezone.now()
    mails = Mail.objects.filter(status=Mail.STATUS_PENDING,
                                scheduled_on__lte=now)
    successes = []

    for mail in mails:
        try:
            send_mail(mail)
        except Exception as e:
            mail.status = Mail.STATUS_FAILURE
            mail.failure_reason = str(e)
            mail.save()
        else:
            successes.append(mail.pk)

    if successes:
        mails.filter(pk__in=successes).update(status=Mail.STATUS_SENT,
                                              sent_on=now)

    nb_successes = len(successes)
    nb_failures = len(mails) - nb_successes

    return nb_successes, nb_failures


def get_subscriptions_management_url(email):
    signer = Signer(salt=SUBSCRIPTION_SIGNING_SALT)
    signed_email = signer.sign(email)
    return reverse('mailing:subscriptions',
                   kwargs={'signed_email': signed_email})
