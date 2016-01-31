# -*- coding: utf-8 -*-
# Copyright (c) 2016 Aladom SAS & Hosting Dvpt SAS
from .utils import render_mail


__all__ = [
    'render_mail',
    'default_app_config',
]


default_app_config = 'mailing.apps.MailingConfig'
