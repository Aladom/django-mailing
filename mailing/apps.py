# -*- coding: utf-8 -*-
# Copyright (c) 2016 Aladom SAS & Hosting Dvpt SAS
from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class MailingConfig(AppConfig):
    name = 'mailing'
    verbose_name = _("Mailing")
