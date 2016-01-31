# -*- coding: utf-8 -*-
# Copyright (c) 2016 Aladom SAS & Hosting Dvpt SAS
from django.template import Template

from .conf import SUBJECT_PREFIX
from .models import Mail


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
