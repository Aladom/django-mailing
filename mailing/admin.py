# -*- coding: utf-8 -*-
# Copyright (c) 2016 Aladom SAS & Hosting Dvpt SAS
import re

from django.conf import settings
from django.contrib import admin
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from .conf import pytz_is_available, SUBJECT_PREFIX
from .forms import (
    CampaignMailHeaderForm, MailHeaderForm, CampaignStaticAttachmentForm,
    MailStaticAttachmentForm,
)
from .models import (
    Campaign, CampaignMailHeader, CampaignStaticAttachment,
    Mail, MailHeader, MailStaticAttachment, MailDynamicAttachment,
    SubscriptionType, Subscription, Blacklist,
)

__all__ = [
    'CampaignMailHeaderInline', 'MailHeaderInline',
    'CampaignStaticAttachmentInline', 'MailStaticAttachmentInline',
    'MailDynamicAttachmentInline', 'CampaignAdmin', 'MailAdmin',
    'SubscriptionTypeAdmin', 'SubscriptionAdmin', 'BlacklistAdmin',
]


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
    form = CampaignStaticAttachmentForm


class MailStaticAttachmentInline(admin.TabularInline):
    model = MailStaticAttachment
    extra = 1
    form = MailStaticAttachmentForm


class MailDynamicAttachmentInline(admin.TabularInline):
    model = MailDynamicAttachment
    extra = 1


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):

    list_display = [
        'key', 'name', 'subject', 'subscription_type', 'is_enabled',
        'debug_mode',
    ]
    list_display_links = ['key', 'name']
    list_filter = ['is_enabled', 'subscription_type', 'debug_mode']
    search_fields = ['key', 'name', 'subject']
    actions = ['enable', 'disable', 'set_debug_mode', 'unset_debug_mode']

    properties_fields = [
        'key', 'name', 'subscription_type', 'is_enabled', 'debug_mode',
    ]
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

    def set_debug_mode(self, request, queryset):
        queryset.update(debug_mode=True)
    enable.short_description = _("Set debug mode")

    def unset_debug_mode(self, request, queryset):
        queryset.update(debug_mode=False)
    disable.short_description = _("Unset debug mode")

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .select_related('subscription_type')
        )


@admin.register(Mail)
class MailAdmin(admin.ModelAdmin):

    list_display = [
        'subject', 'campaign', 'scheduled_on', 'sent_on', 'status',
    ]
    list_filter = ['status', 'campaign']
    search_fields = ['subject', 'headers__value']
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

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('campaign')

    def get_search_results(self, request, queryset, search_term):
        try:
            return self.get_headers_search_results(request, queryset, search_term)
        except Exception:
            return super().get_search_results(request, queryset, search_term)

    def get_headers_search_results(self, request, queryset, search_term):
        terms = re.split(r'(?:^|\s+)([a-z0-9,_-]+:(?:".*?"|[^ ]+))(?:\s+|$)', search_term)
        terms = filter(None, terms)
        query = Q()
        for term in terms:
            term = term.split(":", 1)
            headers = term[0].split(",")
            header_value = term[1]
            if header_value[0] == header_value[-1] == '"':
                header_value = header_value[1:-1]
            if len(headers) > 1:
                query |= Q(
                    headers__name__in=headers,
                    headers__value__icontains=header_value
                )
            else:
                query |= Q(
                    headers__name__iexact=headers[0],
                    headers__value__icontains=header_value
                )
        return queryset.filter(query), True


@admin.register(SubscriptionType)
class SubscriptionTypeAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'subscribed_by_default',
    ]
    fields = ['name', 'subscribed_by_default', 'description']


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        'email', 'subscription_type', 'subscribed',
    ]
    list_filter = ['subscription_type', 'subscribed']
    search_fields = ['email']


@admin.register(Blacklist)
class BlacklistAdmin(admin.ModelAdmin):
    list_display = [
        'reported_on', 'email', 'reason',
    ]
    list_display_links = ['reported_on', 'email']
