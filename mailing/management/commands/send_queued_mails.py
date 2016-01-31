# -*- coding: utf-8 -*-
# Copyright (c) 2016 Aladom SAS & Hosting Dvpt SAS
from django.core.management.base import BaseCommand

from ...utils import send_queued_mails


class Command(BaseCommand):
    help = """Send mails with `status` Mail.STATUS_PENDING and having
    `scheduled_on` set on a past date."""

    def handle(self, *args, **options):
        send_queued_mails()
