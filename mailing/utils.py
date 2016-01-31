# -*- coding: utf-8 -*-
# Copyright (c) 2016 Aladom SAS & Hosting Dvpt SAS
from django.template import Template

from .conf import SUBJECT_PREFIX

def render_mail(campaign, context):
    subject = Template(self.subject).render(context)
    if self.prefix_subject and SUBJECT_PREFIX:
        subject = '{} {}'.format(SUBJECT_PREFIX, subject)

    try:
        with open(self.template_file, 'r') as f:
            html_body = Template(f.read()).render(context)
    except:
        pass  # TODO

    mail = Mail(campaign=self, subject=subject, html_body=html_body)

    for header in self.additional_headers.all():
        mail.headers.add(
            name=header['name'],
            value=Template(header['value']).render(context))

    return mail
