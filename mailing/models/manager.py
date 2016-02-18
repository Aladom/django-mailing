# -*- coding: utf-8 -*-
# Copyright (c) 2016 Aladom SAS & Hosting Dvpt SAS
from django.db.models import Manager

__all__ = [
    'MailHeaderManager',
]


class MailHeaderManager(Manager):

    def items(self):
        """Return headers as a list of tuples (name, value)."""
        for header in self.get_queryset():
            yield header.name, header.value
