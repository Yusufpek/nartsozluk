from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from entry_log.models import EntryLog, Summary

from datetime import datetime


class Command(BaseCommand):
    help = "Group the entry logs"

    def format_date(self, date):
        return date.strftime("%m/%d/%Y, %H:%M")

    def handle(self, *args, **options):
        try:
            now = datetime.now()
            previous = now - timezone.timedelta(hours=1)
            print("now", now)
            entry_ids = EntryLog.objects.filter(
                created_at__lt=now,
                created_at__gt=previous).values_list('entry_uid', flat=True)
            entry_ids = set(entry_ids)
            for id in entry_ids:
                time_filtered = EntryLog.objects.filter(
                    created_at__lt=now,
                    created_at__gt=previous)
                records = time_filtered.filter(entry_uid=id)
                val = 0
                for rec in records:
                    val += rec.value
                Summary(
                    entry_uid=id,
                    record_count=records.count(),
                    total_value=val,
                    interval="{} - {}".format(
                        self.format_date(previous),
                        self.format_date(now))
                ).save()
                self.stdout.write(
                    self.style.SUCCESS('Saved summary of entry: {}'.format(id))
                )
            self.stdout.write(
                self.style.SUCCESS(
                    'Successfully summarized entry logs'))
        except Exception as e:
            raise CommandError('Error creating summary of error log ' + str(e))
