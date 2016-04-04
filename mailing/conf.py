# -*- coding: utf-8 -*-
# Copyright (c) 2016 Aladom SAS & Hosting Dvpt SAS
import os

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.deconstruct import deconstructible

__all__ = [
    'TEMPLATES_UPLOAD_DIR', 'ATTACHMENTS_DIR', 'ATTACHMENTS_UPLOAD_DIR',
    'SUBJECT_PREFIX',
    'TextConfRef', 'StrConfRef', 'pytz_is_available',
]


def get_setting(key, *args):
    """Retrieve a mailing specific setting from django settings.
    Accept a default value as second argument.
    Raise ImproperlyConfigured if the requested setting is not set and no
    default value is provided.
    """
    try:
        value = settings.MAILING[key]
    except (AttributeError, KeyError):
        if len(args) > 0:
            value = args[0]
        else:
            message = "Please define MAILING['{}'] in your settings.py"
            raise ImproperlyConfigured(message.format(key))
    return value


TEMPLATES_UPLOAD_DIR = get_setting('TEMPLATES_UPLOAD_DIR', 'mailing/templates')
"""The directory where mail template files will be stored.

This will be passed as `upload_to` argument of Campaign.template_file. This
means it can either be a relative path from MEDIA_ROOT or a callback taking
`instance` and `filename` as arguments.

See https://docs.djangoproject.com/en/1.9/ref/models/fields/\
#django.db.models.FileField.upload_to

Defaults to "mailing/templates"
"""

ATTACHMENTS_DIR = get_setting('ATTACHMENTS_DIR',
                              os.path.join(settings.STATIC_ROOT,
                                           'mailing', 'attachments'))
"""The path where mail static attachments may be found.

This will be passed as `path` argument of
AbstractBaseStaticAttachment.attachment.

Defaults to "<STATIC_ROOT>/mailing/attachments"
"""

ATTACHMENTS_UPLOAD_DIR = get_setting('ATTACHMENTS_UPLOAD_DIR',
                                     'mailing/attachments')
"""The directory where mail attachments will be stored.

This will be passed as `upload_to` argument of
AbstractBaseDynamicAttachment.attachment. This means it can either be a
relative path from MEDIA_ROOT or a callback taking `instance` and
`filename` as arguments.

See https://docs.djangoproject.com/en/1.9/ref/models/fields/\
#django.db.models.FileField.upload_to

Defaults to "mailing/attachments"
"""

SUBJECT_PREFIX = get_setting('SUBJECT_PREFIX', None)
"""A prefix to prepend to e-mail subjects when Campaign.prefix_subject is True.

If set, it must be a string.

Defaults to None, which means "no prefix". In which case 'prefix_subject' field
won't be available on Campaign admin.
"""

UNEXISTING_CAMPAIGN_FAIL_SILENTLY = get_setting(
    'UNEXISTING_CAMPAIGN_FAIL_SILENTLY', True)
"""Set this to False to raise Campaign.DoesNotExist when
`queue_mail(campaign_key, ...)` is called with an unexisting campaign_key.

When set to True, a warning is emitted and the mail is not queued.

Defaults to True.
"""

MIRROR_SIGNING_SALT = get_setting(
    'MIRROR_SIGNING_SALT', "Django Mailing says it is the mail ID")
"""This salt is used for mirror links signing.
If you change it, all mirror links from e-mails queued formerly will be broken
and return a 400 Bad Request HTTP status.
"""

SUBSCRIPTION_SIGNING_SALT = get_setting(
    'SUBSCRIPTION_SIGNING_SALT', "Django Mailing says it is the e-mail")
"""This salt is used for subscriptions management links signing.
If you change it, all subscriptions management links generated formerly will be
broken and return a 400 Bad Request HTTP status.
"""


@deconstructible
class TextConfRef(object):

    def __init__(self, name, within=None):
        self.name = name
        self.within = within

    def __str__(self):
        value = globals()[self.name]
        if self.within:
            value = self.within.format(value)
        return value


class StrConfRef(str):

    def __new__(cls, name, within=None):
        value = globals()[name]
        if within:
            value = within.format(value)
        self = str.__new__(cls, value)
        self.name = name
        self.within = within
        return self

    def deconstruct(self):
        return ('{}.{}'.format(__name__, self.__class__.__name__),
                (self.name,), {'within': self.within})


StringConfRef = TextConfRef
# TODO DEPRECATED: remove when squashing migrations


try:
    import pytz  # noqa
except ImportError:
    pytz_is_available = False
else:
    pytz_is_available = True
