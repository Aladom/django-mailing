# -*- coding: utf-8 -*-
# Copyright (c) 2016 Aladom SAS & Hosting Dvpt SAS
from datetime import datetime
import os

from django.db import models
from django.template import Template
from django.template.loader import get_template
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from ..conf import StringConfRef, TEMPLATES_UPLOAD_DIR, SUBJECT_PREFIX
from .options import (
    AbstractBaseMailHeader, AbstractBaseStaticAttachment,
    AbstractBaseDynamicAttachment,
)

__all__ = [
    'Campaign', 'CampaignMailHeader', 'CampaignStaticAttachment',
    'Mail', 'MailHeader', 'MailStaticAttachment', 'MailDynamicAttachment',
]


def templates_upload_to(instance, filename):
    if callable(TEMPLATES_UPLOAD_DIR):
        return TEMPLATES_UPLOAD_DIR(instance, filename)
    else:
        return os.path.join(format(datetime.now(), TEMPLATES_UPLOAD_DIR),
                            filename)


class Campaign(models.Model):

    class Meta:
        ordering = ['name']
        verbose_name = _("e-mail campaign")
        verbose_name_plural = _("e-mail campaigns")

    key = models.SlugField(
        max_length=50, unique=True, verbose_name=_("key"),
        help_text=_(
            "The key will be used to reference this campaign from your "
            "scripts."
        ))
    name = models.CharField(
        max_length=255, verbose_name=_("name"))
    subject = models.CharField(
        max_length=255, verbose_name=_("e-mail subject"),
        help_text=_("May contain template variables."))
    prefix_subject = models.BooleanField(
        default=True, verbose_name=_("prefix subject"),
        help_text=StringConfRef('SUBJECT_PREFIX', within=_(
            "Wheter to prefix the subject with \"{}\" or not."
        )))
    is_enabled = models.BooleanField(
        default=True, verbose_name=_("enabled"),
        help_text=_(
            "E-mails won't be sent for campaigns that are not enabled. "
            "Even if a script requests for sending. This is a way to turn off "
            "some campaigns temporarily without changing the source code."
        ))
    template_file = models.FileField(
        upload_to=templates_upload_to, blank=True,
        verbose_name=_("template file"),
        help_text=_(
            "Leave blank to use mailing/{key}.html "
            "from within your template directories."
        ))

    def __str__(self):
        return self.key

    def get_template(self):
        if self.template_file:
            with open(self.template_file.path, 'r') as f:
                template = Template(f.read())
        else:
            template = get_template('mailing/{key}.html'.format(key=self.key))
        return template

    def get_subject(self):
        if self.prefix_subject and SUBJECT_PREFIX:
            return '{} {}'.format(SUBJECT_PREFIX, self.subject)
        else:
            return self.subject


class CampaignMailHeader(AbstractBaseMailHeader):

    class Meta:
        verbose_name = _("extra header")
        verbose_name_plural = _("extra headers")

    campaign = models.ForeignKey(
        'Campaign', models.CASCADE, related_name='extra_headers')


class CampaignStaticAttachment(AbstractBaseStaticAttachment):

    campaign = models.ForeignKey(
        'Campaign', models.CASCADE, related_name='static_attachments')


class Mail(models.Model):

    class Meta:
        ordering = ['-scheduled_on']
        verbose_name = _("e-mail")
        verbose_name_plural = _("e-mails")

    STATUS_PENDING = 1
    STATUS_SENT = 2
    STATUS_CANCELED = 3
    STATUS_FAILURE = 4
    STATUS_CHOICES = [
        (STATUS_PENDING, _("Pending")),
        (STATUS_SENT, _("Sent")),
        (STATUS_CANCELED, _("Canceled")),
        (STATUS_FAILURE, _("Failure")),
    ]

    campaign = models.ForeignKey(
        'Campaign', models.SET_NULL, blank=True, null=True,
        verbose_name=_("campaign"))
    status = models.PositiveSmallIntegerField(
        choices=STATUS_CHOICES, default=STATUS_PENDING,
        verbose_name=_("status"))
    scheduled_on = models.DateTimeField(
        default=timezone.now, verbose_name=_("scheduled on"))
    sent_on = models.DateTimeField(
        blank=True, null=True, editable=False, verbose_name=_("sent on"))
    subject = models.CharField(
        max_length=255, verbose_name=_("subject"))
    html_body = models.TextField(
        verbose_name=_("HTML body"))
    text_body = models.TextField(
        blank=True, verbose_name=_("text body"),
        help_text=_("Leave blank to generate from HTML body."))
    failure_reason = models.TextField(
        blank=True, editable=False, verbose_name=_("failure reason"))

    def __str__(self):
        return '[{}] {}'.format(self.scheduled_on, self.subject)

    def get_headers(self):
        return dict(self.headers.items())


class MailHeader(AbstractBaseMailHeader):

    class Meta:
        verbose_name = _("header")
        verbose_name_plural = _("headers")

    mail = models.ForeignKey(
        'Mail', models.CASCADE, related_name='headers')


class MailStaticAttachment(AbstractBaseStaticAttachment):

    mail = models.ForeignKey(
        'Mail', models.CASCADE, related_name='static_attachments')


class MailDynamicAttachment(AbstractBaseDynamicAttachment):

    mail = models.ForeignKey(
        'Mail', models.CASCADE, related_name='dynamic_attachments')
