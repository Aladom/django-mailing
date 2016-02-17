# -*- coding: utf-8 -*-
# Copyright (c) 2016 Aladom SAS & Hosting Dvpt SAS
import re
import warnings

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template import Template, Context
from django.utils import timezone
from django.utils.html import strip_tags

from .conf import UNEXISTING_CAMPAIGN_FAIL_SILENTLY
from .models import Mail, Campaign


__all__ = [
    'render_mail', 'queue_mail', 'send_mail', 'html_to_text',
]


script_tags_regex = re.compile('<script.*>.*</script>', re.I | re.S)


def AutoescapeTemplate(value):
    return Template('{% autoescape off %}{}{% endautoescape %}'.format(value))


def html_to_text(html):
    """Strip scripts and HTML tags."""
    # TODO keep href attribute of <a> tags. (See #1)
    text = script_tags_regex.sub('', html)
    text = strip_tags(text)
    return text


def render_mail(subject, html_template, headers, context={}, **kwargs):
    """Create and return a Mail instance.

    - `subject`: The subject of the mail, may contain template variables.
    - `html_template`: The template of the HTML body. May be a Template
      instance or a string.
    - `headers`: A dictionary of mail headers. Values may contain template
      variables. You must at least set the 'To' header. If you don't set the
      'From' header, DEFAULT_FROM_EMAIL from your settings.py will be used.
    - `context`: Context to pass when rendering templates. May be a Context
      instance or a dictionary.

    You can also pass the following extra keyword arguments:

        - `text_template`: The template of the plain text body. May be a
          Template instance or a string. If you don't set it, it will be
          automatically generated from the HTML when the mail will be sent.
        - `campaign`: The Campaign instance of the mail if any.
        - `scheduled_on`: A `datetime.datetime` instance representing the date
          when the mail must be sent.
    """
    if 'To' not in headers:
        raise ValueError("You must set the 'To' header.")
    if not isinstance(context, Context):
        context = Context(context)
    if not hasattr(html_template, 'render'):
        # Check Template instance (see #10)
        html_template = Template(html_template)

    headers.setdefault('From', settings.DEFAULT_FROM_EMAIL)
    campaign = kwargs.get('campaign', None)

    subject = AutoescapeTemplate(subject).render(context)

    mailing_ctx = {'subject': subject}
    if campaign:
        mailing_ctx['campaign'] = campaign.name
    context.update({'mailing': mailing_ctx})

    html_body = html_template.render(context)

    text_body = ""
    if 'text_template' in kwargs:
        text_template = kwargs['text_template']
        if not isinstance(text_template, Template):
            text_template = AutoescapeTemplate(text_template)
        text_body = text_template.render(context)

    rendered_headers = dict((name, AutoescapeTemplate(value).render(context))
                            for name, value in headers.items())
    mailing_ctx['headers'] = rendered_headers
    context.update({'mailing': mailing_ctx})

    mail = Mail(subject=subject, html_body=html_body, text_body=text_body)
    if 'campaign' in kwargs:
        mail.campaign = kwargs['campaign']
    if 'scheduled_on' in kwargs:
        mail.scheduled_on = kwargs['scheduled_on']
    mail.save()

    for name, value in rendered_headers.items():
        mail.headers.create(name=name, value=value)

    return mail


def render_campaign_mail(campaign, context={}, **kwargs):
    """Create and return a Mail instance from a Campaign and given context.
    May raise IOError or OSError if reading the template file failed. It's up
    to you to catch these exceptions and handle them properly.
    """
    subject = kwargs.pop('subject', campaign.get_subject())
    html_template = kwargs.pop('html_template', campaign.get_template())
    headers = dict(campaign.extra_headers.items())
    headers.update(kwargs.pop('extra_headers', {}))
    kwargs['campaign'] = campaign
    return render_mail(subject, html_template, headers, context, **kwargs)


def queue_mail(campaign_key=None, context={}, extra_headers={}, **kwargs):
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

    from_email = headers.get('From', settings.DEFAULT_FROM_EMAIL)
    to_emails = map(str.strip, headers.get('To', '').split(','))

    msg = EmailMultiAlternatives(subject, text_body, from_email, to_emails,
                                 headers=headers)
    msg.attach_alternative(html_body, 'text/html')
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
