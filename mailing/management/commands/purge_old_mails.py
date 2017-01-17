# -*- coding: utf-8 -*-
from datetime import date, timedelta

from django.core.management.base import BaseCommand

from ...models import Mail


class Command(BaseCommand):
    help = """Purge mails past given period."""

    def add_arguments(self, parser):
        parser.add_argument(
            'days', type=int,
            help="Number of days to keep archived now.")
        parser.add_argument(
            '-e', '--exclude-statuses', nargs='*', default=[], type=str,
            help="""Prevent deletion of mails at the given statuses."""
                 """ This can be either statuses uppercased name of"""
                 """ integer values""")
        parser.add_argument(
            '-o', '--only-statuses', nargs='*', default=[], type=str,
            help="""Only delete mails at the given statuses. This can be"""
                 """ either statuses uppercased name or integer value""")

    def handle(self, *args, **options):
        statuses = {}
        for prop in dir(Mail):
            if prop.startswith("STATUS_") and prop != "STATUS_CHOICES":
                statuses[prop[7:]] = getattr(Mail, prop)
        new_options = {}
        for opt in ('only_statuses', 'exclude_statuses'):
            new_options[opt] = set()
            for status in options[opt]:
                if status in statuses:
                    new_options[opt].add(statuses[status])
                elif status.isdigit():
                    new_options[opt].add(int(status))
                else:
                    raise ValueError("{} is not a valid status".format(status))
        delete_until = date.today() - timedelta(days=options['days'])
        mails = Mail.objects.filter(scheduled_on__date__lt=delete_until)
        if new_options['only_statuses']:
            mails = mails.filter(status__in=new_options['only_statuses'])
        if new_options['exclude_statuses']:
            mails = mails.exclude(status__in=new_options['exclude_statuses'])
        mails.delete()
