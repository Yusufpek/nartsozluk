from django.core.management.base import BaseCommand, CommandError
from app.models import Entry


class Command(BaseCommand):
    help = "Delete the last entries"

    def add_arguments(self, parser):
        parser.add_argument("entry_ids", nargs="+", type=int)

    def handle(self, *args, **options):
        for entry_id in options["entry_ids"]:
            try:
                entry = Entry.objects.get(pk=entry_id)
            except Entry.DoesNotExist:
                raise CommandError('Entry "%s" does not exist' % entry_id)

            entry.delete()

            self.stdout.write(
                self.style.SUCCESS(
                    'Successfully deleted entry {}'.format(entry_id)))
