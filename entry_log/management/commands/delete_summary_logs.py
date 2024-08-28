from django.core.management.base import BaseCommand, CommandError

from entry_log.models import Summary


class Command(BaseCommand):
    help = "Delete the all summary logs"

    def handle(self, *args, **options):
        try:
            summaries = Summary.objects.all()
            count = summaries.count()
            for summary in summaries:
                summary.delete()
        except Summary.DoesNotExist:
            raise CommandError('Summary delete error!')

        self.stdout.write(
            self.style.SUCCESS(
                'Successfully deleted all summary logs: {}'.format(count)))
