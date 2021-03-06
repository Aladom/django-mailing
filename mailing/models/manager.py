# -*- coding: utf-8 -*-
# Copyright (c) 2017 Aladom SAS & Hosting Dvpt SAS
from functools import reduce
from io import BytesIO, StringIO
import os.path
import re
from uuid import uuid4

from django.core.files import File
from django.core.files.base import ContentFile
from django.db import IntegrityError
from django.db.models import Manager
from django.utils import timezone

__all__ = [
    'MailHeaderManager', 'BlacklistManager', 'DynamicAttachmentManager',
    'StaticAttachmentManager', 'SubscriptionManager',
]


class MailHeaderManager(Manager):

    def items(self):
        """Return headers as a list of tuples (name, value)."""
        for header in self.get_queryset():
            yield header.name, header.value


class DynamicAttachmentManager(Manager):

    def create(self, **kwargs):
        attachment = kwargs.pop('attachment')
        if isinstance(attachment, (str, bytes)):
            attachment = ContentFile(attachment)
        elif isinstance(attachment, (BytesIO, StringIO)):
            attachment = File(attachment)
        if not isinstance(attachment, File):
            raise TypeError(
                "'attachment' must be a 'django.core.files.File'.")
        filename = kwargs.get('filename')
        if not filename:
            filename = str(uuid4())
        obj = self.model(**kwargs)
        obj.attachment.save(filename, attachment, save=False)
        obj.save()
        return obj


class StaticAttachmentManager(Manager):

    def create(self, **kwargs):
        base_path = self.model._meta.get_field('attachment').path
        attachment = kwargs.pop('attachment')
        if not attachment.startswith(base_path + '/'):
            attachment = os.path.join(base_path, attachment)
        kwargs['attachment'] = attachment
        obj = self.model(**kwargs)
        obj.save()
        return obj


class BlacklistManager(Manager):

    raw_email_re = re.compile(r'.*<\s*([^<> ]+)\s*>')

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
            return args
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


class SubscriptionManager(Manager):

    def create_or_update(self, **kwargs):
        filter_kwargs = {'email': kwargs['email']}
        if 'subscription_type_id' in kwargs:
            filter_kwargs['subscription_type_id'] = kwargs['subscription_type_id']
        elif 'subscription_type' in kwargs:
            filter_kwargs['subscription_type'] = kwargs['subscription_type']
        else:
            raise KeyError("Missing subscription type")
        try:
            self.create(**kwargs)
        except IntegrityError:
            self.get_queryset().filter(**filter_kwargs).update(
                subscribed=kwargs['subscribed'], last_modified=timezone.now())
