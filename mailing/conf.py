# -*- coding: utf-8 -*-
# Copyright (c) 2016 Aladom SAS & Hosting Dvpt SAS
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


__all__ = [
    'TEMPLATES_DIR', 'SUBJECT_PREFIX',
    'pytz_is_available',
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


TEMPLATES_DIR = get_setting('TEMPLATES_DIR', 'mailing/templates')
"""The directory where mail template files will be stored.

This will be passed as `upload_to` argument of Campaign.template_file. This
means it can either be a relative path from MEDIA_ROOT or a callback taking
`instance` and `filename` as arguments.

See https://docs.djangoproject.com/en/1.9/ref/models/fields/\
#django.db.models.FileField.upload_to

Defaults to "mailing/templates"
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
`queue_mail(campaign_key, context)` is called with an unexisting campaign_key.

When set to True, a warning is emitted and the mail is not queued.

Defaults to True.
"""


try:
    import pytz  # noqa
except ImportError:
    pytz_is_available = False
else:
    pytz_is_available = True
