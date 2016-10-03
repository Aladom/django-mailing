# -*- coding: utf-8 -*-
# Copyright (c) 2016 Aladom SAS & Hosting Dvpt SAS
from functools import reduce
import re

from django.db.models import Manager

__all__ = [
    'MailHeaderManager',
]


class MailHeaderManager(Manager):

    def items(self):
        """Return headers as a list of tuples (name, value)."""
        for header in self.get_queryset():
            yield header.name, header.value


class BlacklistManager(Manager):

    raw_email_re = re.compile(r'.*\s<([^<> ]+)>')

    @classmethod
    def _to_raw_email(cls, email):
        match = cls.raw_email_re.match(email)
        if match:
            email = match.group(1)
        return email

    def filter_blacklisted(self, *args, **kwargs):
        ignore = kwargs.get('ignore')
        if ignore is True:
            return
        flatten = map(self._to_raw_email,
                      reduce(lambda x, y: x+y if y else x, args, []))
        queryset = self.get_queryset().filter(email__in=flatten)
        if ignore:
            queryset = queryset.exclude(reason__in=ignore)
        blacklisted = queryset.values_list('email', flat=True)
        filtered = (None,) * len(args)
        for i, recipient_list in enumerate(args):
            if not recipient_list:
                continue
            filtered[i] = [
                r for r in recipient_list
                if self._to_raw_email(r) not in blacklisted
            ]
        return filtered
