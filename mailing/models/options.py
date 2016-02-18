# -*- coding: utf-8 -*-
# Copyright (c) 2016 Aladom SAS & Hosting Dvpt SAS
import mimetypes
import os

from django.core.validators import MaxLengthValidator
from django.core.mail.message import DEFAULT_ATTACHMENT_MIME_TYPE
from django.db import models
from django.utils.translation import ugettext_lazy as __

from ..conf import ATTACHMENTS_DIR, ATTACHMENTS_UPLOAD_DIR
from .manager import MailHeaderManager

__all__ = [
    'AbstractBaseMailHeader', 'AbstractBaseStaticAttachment',
    'AbstractBaseDynamicAttachment',
]


class AbstractBaseMailHeader(models.Model):

    class Meta:
        abstract = True
        verbose_name = __("mail header")
        verbose_name_plural = __("mail headers")

    name = models.SlugField(
        max_length=70, verbose_name=__("name"))
    value = models.TextField(
        verbose_name=__("value"), validators=[
            MaxLengthValidator(998),
        ])

    objects = MailHeaderManager()

    def __str__(self):
        return '{}: {}'.format(self.name, self.value)


class AbstractBaseAttachment(models.Model):

    class Meta:
        abstract = True
        verbose_name = __("attachment")
        verbose_name_plural = __("attachments")

    filename = models.CharField(
        max_length=100, verbose_name=__("filename"),
        blank=True)
    mime_type = models.CharField(
        max_length=100, verbose_name=__("mime type"),
        blank=True)

    @property
    def attachment(self):
        raise NotImplementedError(
            "Subclasses of 'AbstractBaseAttachment' must implement an "
            "'attachment' attribute.")

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
            mime_type, _ = mimetypes.guess_type(filename)
            if not mime_type:
                mime_type = DEFAULT_ATTACHMENT_MIME_TYPE
        basetype, _ = mime_type.split('/', 1)
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
        verbose_name = __("static attachment")
        verbose_name_plural = __("static attachments")

    attachment = models.FilePathField(
        path=ATTACHMENTS_DIR, recursive=True, verbose_name=__("file"))

    def get_file_path(self):
        return self.attachment


class AbstractBaseDynamicAttachment(AbstractBaseAttachment):

    class Meta:
        abstract = True
        verbose_name = __("dynamic attachment")
        verbose_name_plural = __("dynamic attachments")

    attachment = models.FileField(
        upload_to=ATTACHMENTS_UPLOAD_DIR, verbose_name=__("file"))

    def get_file_path(self):
        return self.attachment.path
