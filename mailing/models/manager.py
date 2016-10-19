# -*- coding: utf-8 -*-
# Copyright (c) 2016 Aladom SAS & Hosting Dvpt SAS
from functools import reduce
from io import BytesIO, StringIO
import re
from uuid import uuid4

from django.core.files import File, ContentFile
from django.db.models import Manager

__all__ = [
    'MailHeaderManager', 'BlacklistManager', 'DynamicAttachmentManager',
]


class MailHeaderManager(Manager):

    def items(self):
        """Return headers as a list of tuples (name, value)."""
        for header in self.get_queryset():
            yield header.name, header.value


class DynamicAttachmentManager(Manager):

    def create(self, **kwargs):
        attachment = kwargs['attachment']
        if isinstance(attachment, (str, bytes)):
            attachment = ContentFile(attachment)
        elif isinstance(attachment, (BytesIO, StringIO)):
            attachment = File(attachment)
        if not issubclass(attachment, File):
            raise TypeError(
                "attachment must be a subclass of 'django.core.files.File'.")
        filename = kwargs.get('filename')
        if not filename:
            filename = str(uuid4())
        obj = self.model(**kwargs)
        obj.attachment.save(filename, attachment, save=False)
        obj.save()
        return obj


class BlacklistManager(Manager):

    raw_email_re = re.compile(r'.*\s<([^<> ]+)>')

    @staticmethod
    def _split_recipients(recipients):
        if isinstance(recipients, str):
            return list(filter(None, recipients.split(',')))
        else:
            return recipients

    @classmethod
    def _to_raw_email(cls, email):
        email = email.strip()
        match = cls.raw_email_re.match(email)
        if match:
            email = match.group(1)
        return email

    def filter_blacklisted(self, *args, **kwargs):
        recipients = list(map(self._split_recipients, args))
        ignore = kwargs.get('ignore')
        if ignore is True:
            return
        flatten = map(self._to_raw_email,
                      reduce(lambda x, y: x+y if y else x, recipients, []))
        queryset = self.get_queryset().filter(email__in=flatten)
        if ignore:
            queryset = queryset.exclude(reason__in=ignore)
        blacklisted = queryset.values_list('email', flat=True)
        filtered = []
        for recipient_list in recipients:
            if recipient_list:
                filtered.append(', '.join(
                    r for r in recipient_list
                    if self._to_raw_email(r) not in blacklisted
                ))
            else:
                filtered.append(None)
        return filtered
