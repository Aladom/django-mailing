# -*- coding: utf-8 -*-
# Copyright (c) 2016 Aladom SAS & Hosting Dvpt SAS
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from .conf import pytz_is_available
from .forms import CampaignMailHeaderForm, MailHeaderForm
from .models import Campaign, CampaignMailHeader, Mail, MailHeader


class CampaignMailHeaderInline(admin.TabularInline):
    model = CampaignMailHeader
    extra = 1
    form = CampaignMailHeaderForm


class MailHeaderInline(admin.TabularInline):
    model = MailHeader
    extra = 1
    form = MailHeaderForm


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):

    list_display = ['key', 'name', 'subject', 'is_enabled']
    list_display_links = ['key', 'name']
    list_filter = ['is_enabled']
    search_fields = ['key', 'name', 'subject']
    actions = ['enable', 'disable']

    inlines = [CampaignMailHeaderInline]

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

    if pytz_is_available:
        date_hierarchy = 'scheduled_on'

    inlines = [MailHeaderInline]
