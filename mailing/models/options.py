# -*- coding: utf-8 -*-
# Copyright (c) 2016 Aladom SAS & Hosting Dvpt SAS
from datetime import datetime
import mimetypes
import os

from django.core.validators import MaxLengthValidator
from django.core.mail.message import DEFAULT_ATTACHMENT_MIME_TYPE
from django.db import models
from django.utils.translation import ugettext_lazy as _

from ..conf import ATTACHMENTS_DIR, ATTACHMENTS_UPLOAD_DIR
from .manager import (
    MailHeaderManager, DynamicAttachmentManager, StaticAttachmentManager,
)

__all__ = [
    'AbstractBaseMailHeader', 'AbstractBaseStaticAttachment',
    'AbstractBaseDynamicAttachment',
]


def attachments_upload_to(instance, filename):
    if callable(ATTACHMENTS_UPLOAD_DIR):
        return ATTACHMENTS_UPLOAD_DIR(instance, filename)
    else:
        return os.path.join(format(datetime.now(), ATTACHMENTS_UPLOAD_DIR),
                            filename)


class FilePathField(models.FilePathField):
    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if 'path' in kwargs:
            del kwargs['path']
        return name, path, args, kwargs


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

    def get_file_path(self):
        raise NotImplementedError(
            "Subclasses of 'AbstractBaseAttachment' must implement a "
            "'get_file_path' method.")

    def get_file_content(self):
        path = self.get_file_path()
        filename = self.filename
        mime_type = self.mime_type
        if not filename:
            filename = os.path.basename(path)
        if not mime_type:
            mime_type = mimetypes.guess_type(filename)[0]
            if not mime_type:
                mime_type = DEFAULT_ATTACHMENT_MIME_TYPE
        basetype = mime_type.split('/', 1)[0]
        read_mode = 'r' if basetype == 'text' else 'rb'
        content = None

        with open(path, read_mode) as f:
            try:
                content = f.read()
            except UnicodeDecodeError:
                # If mimetype suggests the file is text but it's actually
                # binary, read() will raise a UnicodeDecodeError on Python 3.
                pass

        # If the previous read in text mode failed, try binary mode.
        if content is None:
            with open(path, 'rb') as f:
                content = f.read()

        return content


class AbstractBaseStaticAttachment(AbstractBaseAttachment):

    class Meta:
        abstract = True
        verbose_name = _("static attachment")
        verbose_name_plural = _("static attachments")

    attachment = FilePathField(
        path=ATTACHMENTS_DIR, recursive=True,
        verbose_name=_("file"))

    objects = StaticAttachmentManager()

    def get_file_path(self):
        return self.attachment


class AbstractBaseDynamicAttachment(AbstractBaseAttachment):

    class Meta:
        abstract = True
        verbose_name = _("dynamic attachment")
        verbose_name_plural = _("dynamic attachments")

    attachment = models.FileField(
        upload_to=attachments_upload_to, verbose_name=_("file"))

    objects = DynamicAttachmentManager()

    def get_file_path(self):
        return self.attachment.path
