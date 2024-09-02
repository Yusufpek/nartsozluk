from django.core.management.base import BaseCommand, CommandError

from dictionary.models import Entry
from entry_log.models import EntryLog

import random
from datetime import datetime


class Command(BaseCommand):
    help = "Create entry log for entries"

    def add_arguments(self, parser):
        parser.add_argument("--ids", nargs="+", type=str)

    def handle(self, *args, **options):
        ids = options["ids"]
        for id in ids:
            try:
                entry = Entry.objects.filter(uid=id).first()
                if entry:
                    EntryLog(
                        entry_uid=entry.uid,
                        value=random.randint(1, 17),
                        created_at=datetime.now()).save()
                    self.stdout.write(
                        self.style.SUCCESS('Successfully created entry_log'))
                else:
                    self.stdout.write(self.style.ERROR('Entry does not exist'))
            except Exception as e:
                raise CommandError('Error creating random error log ' + str(e))
