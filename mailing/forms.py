# -*- coding: utf-8 -*-
# Copyright (c) 2016 Aladom SAS & Hosting Dvpt SAS
from django.forms import ModelForm
from django.forms.widgets import Textarea
from django.utils.translation import ugettext_lazy as _

from .models import CampaignMailHeader, MailHeader


class CampaignMailHeaderForm(ModelForm):

    class Meta:
        model = CampaignMailHeader
        fields = '__all__'
        widgets = {
            'value': Textarea(attrs={'rows': 1}),
        }
        help_texts = {
            'value': _("May contain template variables."),
        }


class MailHeaderForm(ModelForm):

    class Meta:
        model = MailHeader
        fields = '__all__'
        widgets = {
            'value': Textarea(attrs={'rows': 1}),
        }
