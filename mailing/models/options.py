# -*- coding: utf-8 -*-
# Copyright (c) 2016 Aladom SAS & Hosting Dvpt SAS
from django.core.validators import MaxLengthValidator
from django.db import models
from django.utils.translation import ugettext_lazy as _

from ..conf import ATTACHMENTS_DIR, ATTACHMENTS_UPLOAD_DIR
from .manager import MailHeaderManager

__all__ = [
    'AbstractBaseMailHeader', 'AbstractBaseStaticAttachment',
    'AbstractBaseDynamicAttachment',
]


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


class AbstractBaseAttachment(models.Model):

    class Meta:
        abstract = True
        verbose_name = _("attachment")
        verbose_name_plural = _("attachments")

    filename = models.CharField(
        max_length=100, verbose_name=_("filename"),
        blank=True)
    mime_type = models.CharField(
        max_length=100, verbose_name=_("mime type"),
        blank=True)

    @property
    def attachment(self):
        raise NotImplementedError(
            "Subclasses of 'AbstractBaseAttachment' should implement an "
            "'attachment' attribute.")


class AbstractBaseStaticAttachment(AbstractBaseAttachment):

    class Meta:
        abstract = True
        verbose_name = _("static attachment")
        verbose_name_plural = _("static attachments")

    attachment = models.FilePathField(
        path=ATTACHMENTS_DIR, recursive=True, verbose_name=_("file"))


class AbstractBaseDynamicAttachment(AbstractBaseAttachment):

    class Meta:
        abstract = True
        verbose_name = _("dynamic attachment")
        verbose_name_plural = _("dynamic attachments")

    attachment = models.FileField(
        upload_to=ATTACHMENTS_UPLOAD_DIR, verbose_name=_("file"))
