# -*- coding: utf-8 -*-
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from ...models import Mail


class Command(BaseCommand):
    help = """Purge old sended mails."""

    def add_arguments(self, parser):
        parser.add_argument(
            'days', type=int,
            help="Specify the day frequency.")
        parser.add_argument(
            '-e', '--exclude-statuses', nargs='*', type=str,
            help="Exclude specified statuses.")
        parser.add_argument(
            '-o', '--only-statuses', nargs='*', type=str,
            help="Delete mail with specified statuses.")

    def handle(self, *args, **options):
        exclude_statuses = set()
        only_statuses = set()
        statuses = {}
        for x in dir(Mail):
            if x.startswith("STATUS_") and x != "STATUS_CHOICES":
                statuses[x[7:]] = getattr(Mail, x)

        for status in options['exclude_statuses']:
            if status in statuses:
                exclude_statuses.add(statuses[status])
            elif status.isdigit():
                exclude_statuses.add(int(status))
            else:
                raise ValueError("{} is not a valid status".format(status))
        for status in options['only_statuses']:
            if status in statuses:
                only_statuses.add(statuses[status])
            elif status.isdigit():
                only_statuses.add(int(status))
            else:
                raise ValueError("{} is not a valid status".format(status))
        end = date.today()
        start = end - timedelta(days=options['days'])
        mails = Mail.objects.filter(
           scheduled_on__date__gte=start,
           scheduled_on__date__lte=end
        )
        if only_statuses:
            mails = mails.filter(status__in=only_statuses)
        if exclude_statuses:
            mails = mails.exclude(status__in=exclude_statuses)
        mails.delete()
