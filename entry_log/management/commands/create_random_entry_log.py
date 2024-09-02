from django.core.management.base import BaseCommand, CommandError

from dictionary.models import Entry
from entry_log.models import EntryLog

import random
from datetime import datetime


class Command(BaseCommand):
    help = "Create entry log for entries"

    def add_arguments(self, parser):
        parser.add_argument("--count", nargs="+", type=int)

    def handle(self, *args, **options):
        count = options["count"][0]
        try:
            entry_ids = Entry.objects.all().values_list('uid', flat=True)
            _count = count
            while count > 0:
                uid = random.choice(entry_ids)
                entry_log = EntryLog(
                    entry_uid=uid,
                    value=random.randint(1, 17),
                    created_at=datetime.now())
                entry_log.save()
                print("Saved new entry log {} - {} - {}".format(
                    entry_log.created_at,
                    entry_log.entry_uid,
                    entry_log.value))
                count -= 1
            self.stdout.write(
                self.style.SUCCESS(
                    'Successfully created {} entry log'.format(_count)))
        except Exception as e:
            raise CommandError('Error creating random error log ' + str(e))
