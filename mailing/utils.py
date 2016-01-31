# -*- coding: utf-8 -*-
# Copyright (c) 2016 Aladom SAS & Hosting Dvpt SAS
import re
import warnings

from django.core.mail import EmailMultiAlternatives
from django.template import Template
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


def render_mail(campaign, context={}):
    """Create and return a Mail instance from a Campaign and given context.
    May raise IOError or OSError if reading the template file failed. It's up
    to you to catch these exceptions and handle them properly.
    """
    subject = Template(campaign.subject).render(context)
    if campaign.prefix_subject and SUBJECT_PREFIX:
        subject = '{} {}'.format(SUBJECT_PREFIX, subject)

    with open(campaign.template_file, 'r') as f:
        html_body = Template(f.read()).render(context)

    mail = Mail(campaign=campaign, subject=subject, html_body=html_body)

    for header in campaign.additional_headers.all():
        mail.headers.add(
            name=header['name'],
            value=Template(header['value']).render(context))

    return mail


def queue_mail(campaign_key, context, fail_silently=None):
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
    mail = render_mail(campaign, context)
    mail.status = Mail.STATUS_PENDING
    mail.save()
    return mail


def send_mail(mail):
    """Send a Mail instance."""
    subject = mail.subject
    html_body = mail.html_body
    text_body = mail.text_body or html_to_text(html_body)
    headers = mail.get_headers()

    msg = EmailMultiAlternatives(subject, text_body, headers=headers)
    msg.attach_alternative(html_body, 'text/html')
    msg.send()
