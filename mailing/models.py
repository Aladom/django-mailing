# -*- coding: utf-8 -*-
# Copyright (c) 2016 Aladom SAS & Hosting Dvpt SAS
from django.conf import settings
from django.core.validators import MaxLengthValidator
from django.db import models
from django.utils.translation import ugettext_lazy as _

from .settings import TEMPLATES_DIR


class AbstractBaseMailHeader(models.Model):

    class Meta:
        abstract = True
        verbose_name = _("additional header")
        verbose_name_plural = _("additional headers")

    name = models.SlugField(
        max_length=70, verbose_name=_("name"))
    value = models.TextField(
        verbose_name=_("value"), validators=[
            MaxLengthValidator(998),
        ])

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
    is_enabled = models.BooleanField(
        default=True, verbose_name=_("enabled"),
        help_text=_(
            "E-mails won't be sent for campaigns that are not enabled. "
            "Even if a script requests for sending. This is a way to turn off "
            "some campaigns temporarily without changing the source code."
        ))
    from_email = models.CharField(
        max_length=255, blank=True, verbose_name=_("sender email"),
        help_text=_("Leave blank to use default ({}).").format(
            settings.DEFAULT_FROM_EMAIL))
    template_file = models.FileField(
        upload_to=TEMPLATES_DIR, verbose_name=_("template file"))

    def __str__(self):
        return self.key


class CampaignMailHeader(AbstractBaseMailHeader):

    campaign = models.ForeignKey(
        'Campaign', models.CASCADE, related_name='headers')
