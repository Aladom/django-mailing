# -*- coding: utf-8 -*-
# Copyright (c) 2016 Aladom SAS & Hosting Dvpt SAS
from datetime import date, timedelta
import sys

from django.core.management.base import BaseCommand

from ...models import Mail


class Command(BaseCommand):
    help = """Purge mails past given period."""

    def add_arguments(self, parser):
        parser.add_argument(
            'days', type=int,
            help="Number of days to keep archived until today.")
        parser.add_argument(
            '-e', '--exclude-statuses', nargs='*', default=[], type=str,
            help=(
                "Prevent deletion of mails at the given statuses. This can "
                "be either statuses uppercased name of integer value."
            ))
        parser.add_argument(
            '-o', '--only-statuses', nargs='*', default=[], type=str,
            help=(
                "Only delete mails at the given statuses. This can be either "
                "statuses uppercased name or integer value."
            ))

    def handle(self, *args, **options):
        self.init_statuses()
        delete_until = date.today() - timedelta(days=options['days'])

        try:
            only_statuses = set(
                map(self.parse_status, options['only_statuses']))
            exclude_statuses = set(
                map(self.parse_status, options['exclude_statuses']))
        except ValueError as e:
            self.stderr.write(str(e))
            sys.exit(1)

        mails = Mail.objects.filter(scheduled_on__date__lt=delete_until)
        if only_statuses:
            mails = mails.filter(status__in=only_statuses)
        if exclude_statuses:
            mails = mails.exclude(status__in=exclude_statuses)
        mails.delete()

    def init_statuses(self):
        self.statuses = {}
        for prop in dir(Mail):
            if prop.startswith("STATUS_") and prop != "STATUS_CHOICES":
                self.statuses[prop[7:]] = getattr(Mail, prop)

    def parse_status(self, status):
        if status in self.statuses:
            return self.statuses[status]
        elif status.isdigit():
            return int(status)
        else:
            raise ValueError("{} is not a valid status".format(status))
