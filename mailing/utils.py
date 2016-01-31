# -*- coding: utf-8 -*-
# Copyright (c) 2016 Aladom SAS & Hosting Dvpt SAS
import re

from django.core.mail import EmailMultiAlternatives
from django.template import Template
from django.utils.html import strip_tags

from .conf import SUBJECT_PREFIX
from .models import Mail, Campaign


__all__ = [
    'render_mail', 'queue_mail', 'send_mail', 'html_to_text',
]


script_tags_regex = re.compile('<script.*>.*</script>', re.I | re.S)


def html_to_text(html):
    text = script_tags_regex.sub('', html)
    text = strip_tags(text)
    return text


def render_mail(campaign, context={}):
    subject = Template(campaign.subject).render(context)
    if campaign.prefix_subject and SUBJECT_PREFIX:
        subject = '{} {}'.format(SUBJECT_PREFIX, subject)

    try:
        with open(campaign.template_file, 'r') as f:
            html_body = Template(f.read()).render(context)
    except:
        pass  # TODO

    mail = Mail(campaign=campaign, subject=subject, html_body=html_body)

    for header in campaign.additional_headers.all():
        mail.headers.add(
            name=header['name'],
            value=Template(header['value']).render(context))

    return mail


def queue_mail(campaign_key, context):
    campaign = Campaign.objects.get(key=campaign_key)
    mail = render_mail(campaign, context)
    mail.save()
    return mail


def send_mail(mail):
    subject = mail.subject
    html_body = mail.html_body
    text_body = mail.text_body or html_to_text(html_body)
    headers = mail.get_headers()

    msg = EmailMultiAlternatives(subject, text_body, headers=headers)
    msg.attach_alternative(html_body, 'text/html')
    msg.send()
