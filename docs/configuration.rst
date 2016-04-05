Configuration
=============

Django Mailing Campaign ships with reasonable default settings and was designed
to let you try it out without having to spend time to configure it.

You likely don't need to bother with configuring Django Mailing Campaign.
However, we don't want to force you use our default settings. So, here is the
list of configurable settings.

All these settings will be defined within a ``MAILING`` dictionary in your
settings.py. For instance::

    MAILING = {
        'TEMPLATES_UPLOAD_DIR': "mail_templates",
        'ATTACHMENTS_DIR': os.path.join(STATIC_ROOT, 'mail_attachments'),
    }


TEMPLATES_UPLOAD_DIR
--------------------

The directory where mail template files will be stored.

This will be passed as ``upload_to`` argument of Campaign.template_file. This
means it can either be a relative path from MEDIA_ROOT or a callback taking
``instance`` and ``filename`` as arguments.

See https://docs.djangoproject.com/en/1.9/ref/models/fields/#django.db.models.FileField.upload_to

Defaults to "mailing/templates"


ATTACHMENTS_DIR
---------------

The path where mail static attachments may be found.

This will be passed as ``path`` argument of
AbstractBaseStaticAttachment.attachment.

Defaults to "<STATIC_ROOT>/mailing/attachments"


ATTACHMENTS_UPLOAD_DIR
----------------------

The directory where mail attachments will be stored.

This will be passed as ``upload_to`` argument of
AbstractBaseDynamicAttachment.attachment. This means it can either be a
relative path from MEDIA_ROOT or a callback taking ``instance`` and
``filename`` as arguments.

See https://docs.djangoproject.com/en/1.9/ref/models/fields/#django.db.models.FileField.upload_to

Defaults to "mailing/attachments"


SUBJECT_PREFIX
--------------

A prefix to prepend to e-mail subjects when Campaign.prefix_subject is True.

If set, it must be a string.

Defaults to None, which means "no prefix". In which case 'prefix_subject' field
won't be available on Campaign admin.


UNEXISTING_CAMPAIGN_FAIL_SILENTLY
---------------------------------

Set this to False to raise Campaign.DoesNotExist when
``queue_mail(campaign_key, ...)`` is called with an unexisting campaign_key.

When set to True, a warning is emitted and the mail is not queued.

Defaults to True.


MIRROR_SIGNING_SALT
-------------------

This salt is used for mirror links signing.

If you change it, all mirror links from e-mails queued formerly will be broken
and return a 400 Bad Request HTTP status.

Defaults to "Django Mailing says it is the mail ID"


SUBSCRIPTION_SIGNING_SALT
-------------------------

This salt is used for subscriptions management links signing.

If you change it, all subscriptions management links generated formerly will be
broken and return a 400 Bad Request HTTP status.

Defaults to "Django Mailing says it is the e-mail"
