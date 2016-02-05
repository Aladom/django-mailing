# -*- coding: utf-8 -*-
# Copyright (c) 2016 Aladom SAS & Hosting Dvpt SAS
import re
import warnings

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template import Template, Context
from django.utils import timezone
from django.utils.html import strip_tags

from .conf import SUBJECT_PREFIX, UNEXISTING_CAMPAIGN_FAIL_SILENTLY
from .models import Mail, Campaign


__all__ = [
    'render_mail', 'queue_mail', 'send_mail', 'html_to_text',
]


script_tags_regex = re.compile('<script.*>.*</script>', re.I | re.S)


def html_to_text(html):
    """Strip scripts and HTML tags."""
    # TODO keep href attribute of <a> tags.
    text = script_tags_regex.sub('', html)
    text = strip_tags(text)
    return text


def render_mail(campaign, context={}, extra_headers={}):
    """Create and return a Mail instance from a Campaign and given context.
    May raise IOError or OSError if reading the template file failed. It's up
    to you to catch these exceptions and handle them properly.
    """
    if not isinstance(context, Context):
        context = Context(context)

    subject = Template(campaign.subject).render(context)

    mailing_ctx = {
        'subject': subject,
        'campaign': campaign.name,
    }

    context.update({'mailing': mailing_ctx})

    if campaign.prefix_subject and SUBJECT_PREFIX:
        subject = '{} {}'.format(SUBJECT_PREFIX, subject)

    with open(campaign.template_file.path, 'r') as f:
        html_body = Template(f.read()).render(context)

    headers = {}
    for name, value in campaign.extra_headers.items():
        headers[name] = Template(value).render(context)
    for name, value in extra_headers.items():
        headers[name] = Template(value).render(context)

    mailing_ctx['headers'] = headers
    context.update({'mailing': mailing_ctx})

    mail = Mail(campaign=campaign, subject=subject, html_body=html_body)
    mail.save()

    for name, value in headers.items():
        mail.headers.create(name=name, value=value)

    return mail


def queue_mail(campaign_key, context={}, extra_headers={}, fail_silently=None):
    """Create and save a Mail instance from a Campaign and given context.

    If fail_silently is True and the requested campaign does not exist, emit a
    warning and return None.
    If fail_silently is False and the requested campaign does not exist, raise
    Campaign.DoesNotExist.
    If fail_silently is not passed (or None), the default value will be
    retrived from the app config (See conf.UNEXISTING_CAMPAIGN_FAIL_SILENTLY).

    If the campaign is not enabled, the mail is not queued and None is
    returned. (See Campaign.is_enabled).

    May raise IOError or OSError if reading the template file failed. It's up
    to you to catch these exceptions and handle them properly.

    Return the saved Mail instance.
    """
    if fail_silently is None:
        fail_silently = UNEXISTING_CAMPAIGN_FAIL_SILENTLY
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
    mail = render_mail(campaign, context, extra_headers)
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
