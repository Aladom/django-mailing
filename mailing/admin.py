# -*- coding: utf-8 -*-
# Copyright (c) 2016 Aladom SAS & Hosting Dvpt SAS
from django.contrib import admin
from django.db.models import TextField
from django.forms.widgets import Textarea

from .models import Campaign, CampaignMailHeader


class CampaignMailHeaderInline(admin.TabularInline):
    model = CampaignMailHeader
    extra = 1
    formfield_overrides = {
        TextField: {'widget': Textarea(attrs={'rows': 1})}
    }


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):

    list_display = ['key', 'name', 'subject', 'is_enabled']
    list_filter = ['is_enabled']
    search_fields = ['key', 'name', 'subject']

    inlines = [CampaignMailHeaderInline]
