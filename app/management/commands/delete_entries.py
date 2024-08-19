from django.core.management.base import BaseCommand, CommandError
from app.models import Entry


class Command(BaseCommand):
    help = "Delete the all entries"

    def handle(self, *args, **options):
        try:
            entries = Entry.objects.all()
            count = entries.count()
            entries.delete()
        except Entry.DoesNotExist:
            raise CommandError('Entry delete error!')

        self.stdout.write(
            self.style.SUCCESS(
                'Successfully deleted all entries: {}'.format(count)))
