# -*- coding: utf-8 -*-
# Copyright (c) 2016 Aladom SAS & Hosting Dvpt SAS
from django.conf import settings
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from .conf import pytz_is_available, SUBJECT_PREFIX
from .forms import CampaignMailHeaderForm, MailHeaderForm
from .models import (
    Campaign, CampaignMailHeader, CampaignStaticAttachment,
    Mail, MailHeader, MailStaticAttachment, MailDynamicAttachment,
)


class CampaignMailHeaderInline(admin.TabularInline):
    model = CampaignMailHeader
    extra = 1
    form = CampaignMailHeaderForm


class MailHeaderInline(admin.TabularInline):
    model = MailHeader
    extra = 1
    form = MailHeaderForm


class CampaignStaticAttachmentInline(admin.TabularInline):
    model = CampaignStaticAttachment
    extra = 1


class MailStaticAttachmentInline(admin.TabularInline):
    model = MailStaticAttachment
    extra = 1


class MailDynamicAttachmentInline(admin.TabularInline):
    model = MailDynamicAttachment
    extra = 1


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):

    list_display = ['key', 'name', 'subject', 'is_enabled']
    list_display_links = ['key', 'name']
    list_filter = ['is_enabled']
    search_fields = ['key', 'name', 'subject']
    actions = ['enable', 'disable']

    properties_fields = ['key', 'name', 'is_enabled']
    emails_fields = ['subject', 'prefix_subject', 'template_file']
    if SUBJECT_PREFIX is None:
        emails_fields.remove('prefix_subject')
    fieldsets = [
        (_("Campaign properties"), {'fields': properties_fields}),
        (_("Campaign e-mails"), {'fields': emails_fields}),
    ]
    inlines = [CampaignMailHeaderInline, CampaignStaticAttachmentInline]

    def enable(self, request, queryset):
        queryset.update(is_enabled=True)
    enable.short_description = _("Enable selected e-mail campaigns")

    def disable(self, request, queryset):
        queryset.update(is_enabled=False)
    disable.short_description = _("Disable selected e-mail campaigns")


@admin.register(Mail)
class MailAdmin(admin.ModelAdmin):

    list_display = [
        'subject', 'campaign', 'scheduled_on', 'sent_on', 'status',
    ]
    list_filter = ['status', 'campaign']
    search_fields = ['subject']
    if not settings.USE_TZ or pytz_is_available:
        date_hierarchy = 'scheduled_on'

    fieldsets = [
        (_("Properties"), {'fields': [
            'campaign', 'scheduled_on',
        ]}),
        (_("Status"), {'fields': [
            'status', 'sent_on', 'failure_reason',
        ]}),
        (_("E-mail"), {'fields': [
            'subject', 'html_body', 'text_body',
        ]}),
    ]

    inlines = [
        MailHeaderInline, MailStaticAttachmentInline,
        MailDynamicAttachmentInline
    ]
    readonly_fields = ['sent_on', 'failure_reason']
