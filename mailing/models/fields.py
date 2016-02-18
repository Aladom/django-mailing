# -*- coding: utf-8 -*-
# Copyright (c) 2016 Aladom SAS & Hosting Dvpt SAS
from django.db.models import BooleanField

__all__ = [
    'VariableHelpTextBooleanField',
]


class VariableHelpTextBooleanField(BooleanField):
    """Fixes an issue with help_text depending on a variable.

    See https://github.com/Aladom/django-mailing/issues/2 for details.
    """

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if 'help_text' in kwargs:
            del kwargs['help_text']
        return name, path, args, kwargs
