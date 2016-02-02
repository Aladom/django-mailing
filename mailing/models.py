# -*- coding: utf-8 -*-
# Copyright (c) 2016 Aladom SAS & Hosting Dvpt SAS
from django.core.validators import MaxLengthValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from .conf import TEMPLATES_DIR, SUBJECT_PREFIX


class MailHeaderManager(models.Manager):

    def items(self):
        """Return headers as a list of tuples (name, value)."""
        for header in self.get_queryset():
            yield header.name, header.value


class AbstractBaseMailHeader(models.Model):

    class Meta:
        abstract = True
        verbose_name = _("mail header")
        verbose_name_plural = _("mail headers")

    name = models.SlugField(
        max_length=70, verbose_name=_("name"))
    value = models.TextField(
        verbose_name=_("value"), validators=[
            MaxLengthValidator(998),
        ])

    objects = MailHeaderManager()

    def __str__(self):
        return '{}: {}'.format(self.name, self.value)


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
        help_text=_(
            "Wheter to prefix the subject with \"{}\" or not."
        ).format(SUBJECT_PREFIX))
    is_enabled = models.BooleanField(
        default=True, verbose_name=_("enabled"),
        help_text=_(
            "E-mails won't be sent for campaigns that are not enabled. "
            "Even if a script requests for sending. This is a way to turn off "
            "some campaigns temporarily without changing the source code."
        ))
    template_file = models.FileField(
        upload_to=TEMPLATES_DIR, verbose_name=_("template file"))

    def __str__(self):
        return self.key


class CampaignMailHeader(AbstractBaseMailHeader):

    class Meta:
        verbose_name = _("extra header")
        verbose_name_plural = _("extra headers")

    campaign = models.ForeignKey(
        'Campaign', models.CASCADE, related_name='extra_headers')


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

    objects = MailHeaderManager()
