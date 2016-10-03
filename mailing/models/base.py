# -*- coding: utf-8 -*-
# Copyright (c) 2016 Aladom SAS & Hosting Dvpt SAS
from datetime import datetime
import os
import re

from django.core.signing import Signer
from django.core.urlresolvers import reverse
from django.db import models
from django.template import Template
from django.template.loader import get_template
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from ..conf import (
    TextConfRef, TEMPLATES_UPLOAD_DIR, SUBJECT_PREFIX, MIRROR_SIGNING_SALT,
)
from .options import (
    AbstractBaseMailHeader, AbstractBaseStaticAttachment,
    AbstractBaseDynamicAttachment,
)

__all__ = [
    'Campaign', 'CampaignMailHeader', 'CampaignStaticAttachment',
    'Mail', 'MailHeader', 'MailStaticAttachment', 'MailDynamicAttachment',
    'SubscriptionType', 'Subscription', 'Blacklist',
]


def templates_upload_to(instance, filename):
    if callable(TEMPLATES_UPLOAD_DIR):
        return TEMPLATES_UPLOAD_DIR(instance, filename)
    else:
        return os.path.join(format(datetime.now(), TEMPLATES_UPLOAD_DIR),
                            filename)


class SubscriptionType(models.Model):

    class Meta:
        verbose_name = _("subscription type")
        verbose_name_plural = _("subscription types")

    name = models.CharField(
        max_length=200, unique=True, verbose_name=_("name"))
    description = models.TextField(verbose_name=_("description"))
    subscribed_by_default = models.BooleanField(
        default=True, verbose_name=_("subscribed by default"),
        help_text=_(
            "Whether potential recipients are subscribed or not to "
            "this type by default"
        ))

    def __str__(self):
        return self.name

    def is_subscribed(self, email):
        match = re.match(r'.*\s<([^<> ]+)>', email)
        if match:
            email = match.group(1)

        try:
            return self.subscriptions.get(email=email).subscribed
        except Subscription.DoesNotExist:
            return self.subscribed_by_default


class Subscription(models.Model):

    class Meta:
        verbose_name = _("subscription")
        verbose_name_plural = _("subscriptions")
        unique_together = [
            ('email', 'subscription_type'),
        ]

    email = models.EmailField(
        db_index=True, verbose_name=_("e-mail"))
    subscription_type = models.ForeignKey(
        SubscriptionType, models.CASCADE,
        related_name='subscriptions', related_query_name='subscriptions',
        verbose_name=_("subscription type"))
    subscribed = models.BooleanField(
        default=True, verbose_name=_("subscribed"))


class Campaign(models.Model):

    class Meta:
        ordering = ['name']
        verbose_name = _("e-mail campaign")
        verbose_name_plural = _("e-mail campaigns")

    key = models.SlugField(
        max_length=50, unique=True, verbose_name=_("key"),
        help_text=_(
            "The key will be used to reference this campaign from your "
            "scripts."
        ))
    name = models.CharField(
        max_length=255, verbose_name=_("name"))
    subject = models.CharField(
        max_length=255, verbose_name=_("e-mail subject"),
        help_text=_("May contain template variables."))
    prefix_subject = models.BooleanField(
        default=True, verbose_name=_("prefix subject"),
        help_text=TextConfRef('SUBJECT_PREFIX', within=_(
            "Wheter to prefix the subject with \"{}\" or not."
        )))
    is_enabled = models.BooleanField(
        default=True, verbose_name=_("enabled"),
        help_text=_(
            "E-mails won't be sent for campaigns that are not enabled. "
            "Even if a script requests for sending. This is a way to turn off "
            "some campaigns temporarily without changing the source code."
        ))
    template_file = models.FileField(
        upload_to=templates_upload_to, blank=True,
        verbose_name=_("template file"),
        help_text=_(
            "Leave blank to use mailing/{key}.html "
            "from within your template directories."
        ))
    subscription_type = models.ForeignKey(
        SubscriptionType, models.SET_NULL, blank=True, null=True,
        verbose_name=_("subscription type"))

    def __str__(self):
        return self.key

    def get_template(self):
        if self.template_file:
            with open(self.template_file.path, 'r') as f:
                template = Template(f.read())
        else:
            template = get_template('mailing/{key}.html'.format(key=self.key))
        return template

    def get_subject(self):
        if self.prefix_subject and SUBJECT_PREFIX:
            return '{} {}'.format(SUBJECT_PREFIX, self.subject)
        else:
            return self.subject

    def is_subscribed(self, email):
        return (not self.subscription_type or
                self.subscription_type.is_subscribed(email))


class CampaignMailHeader(AbstractBaseMailHeader):

    class Meta:
        verbose_name = _("extra header")
        verbose_name_plural = _("extra headers")

    campaign = models.ForeignKey(
        'Campaign', models.CASCADE, related_name='extra_headers')


class CampaignStaticAttachment(AbstractBaseStaticAttachment):

    campaign = models.ForeignKey(
        'Campaign', models.CASCADE, related_name='static_attachments')


class Mail(models.Model):

    class Meta:
        ordering = ['-scheduled_on']
        verbose_name = _("e-mail")
        verbose_name_plural = _("e-mails")

    STATUS_PENDING = 1
    STATUS_SENT = 2
    STATUS_CANCELED = 3
    STATUS_FAILURE = 4
    STATUS_DRAFT = 5
    STATUS_CHOICES = [
        (STATUS_PENDING, _("Pending")),
        (STATUS_SENT, _("Sent")),
        (STATUS_CANCELED, _("Canceled")),
        (STATUS_FAILURE, _("Failure")),
        (STATUS_DRAFT, _("Draft")),
    ]

    campaign = models.ForeignKey(
        'Campaign', models.SET_NULL, blank=True, null=True,
        verbose_name=_("campaign"))
    status = models.PositiveSmallIntegerField(
        choices=STATUS_CHOICES, default=STATUS_DRAFT,
        verbose_name=_("status"))
    scheduled_on = models.DateTimeField(
        default=timezone.now, verbose_name=_("scheduled on"))
    sent_on = models.DateTimeField(
        blank=True, null=True, editable=False, verbose_name=_("sent on"))
    subject = models.CharField(
        max_length=255, verbose_name=_("subject"))
    html_body = models.TextField(
        verbose_name=_("HTML body"))
    text_body = models.TextField(
        blank=True, verbose_name=_("text body"),
        help_text=_("Leave blank to generate from HTML body."))
    failure_reason = models.TextField(
        blank=True, editable=False, verbose_name=_("failure reason"))

    def __str__(self):
        return "[{}] {}".format(self.scheduled_on, self.subject)

    def get_headers(self):
        return dict(self.headers.items())

    def get_attachments(self):
        return []

    def get_absolute_url(self):
        signer = Signer(salt=MIRROR_SIGNING_SALT)
        signed_pk = signer.sign(str(self.pk))
        return reverse('mailing:mirror', kwargs={'signed_pk': signed_pk})


class MailHeader(AbstractBaseMailHeader):

    class Meta:
        verbose_name = _("header")
        verbose_name_plural = _("headers")

    mail = models.ForeignKey(
        'Mail', models.CASCADE, related_name='headers')


class MailStaticAttachment(AbstractBaseStaticAttachment):

    mail = models.ForeignKey(
        'Mail', models.CASCADE, related_name='static_attachments')


class MailDynamicAttachment(AbstractBaseDynamicAttachment):

    mail = models.ForeignKey(
        'Mail', models.CASCADE, related_name='dynamic_attachments')


class Blacklist(models.Model):

    class Meta:
        verbose_name = _("blacklisted address")
        verbose_name_plural = _("blacklisted addresses")
        ordering = ['-reported_on']

    REASON_OTHER = 1
    REASON_SPAM = 2
    REASON_BLOCKED = 3
    REASON_HARDBOUNCE = 4
    REASON_CHOICES = [
        (REASON_SPAM, _("SPAM")),
        (REASON_BLOCKED, _("Blocked")),
        (REASON_HARDBOUNCE, _("Hard bounce")),
        (REASON_OTHER, _("Other")),
    ]

    email = models.EmailField(
        unique=True, verbose_name=_("e-mail address"))
    reason = models.PositiveSmallIntegerField(
        choices=REASON_CHOICES, default=REASON_OTHER,
        verbose_name=_("reason"))
    verbose_reason = models.CharField(
        max_length=250, blank=True, verbose_name=_("verbose reason"))
    reported_on = models.DateTimeField(
        verbose_name=_("reported on"), auto_now_add=True)

    def __str__(self):
        return "{} ({})".format(self.email, self.get_reason_display())
