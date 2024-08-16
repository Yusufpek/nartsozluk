from django.core.management.base import BaseCommand, CommandError
from django.core.cache import cache


from app.models import Author


class Command(BaseCommand):
    help = "Save all users stats to db from cache"

    def add_arguments(self, parser):
        parser.add_argument("--user-ids", nargs="+", type=int)

    def handle(self, *args, **options):
        for id in options["--user-ids"]:
            try:
                author = Author.objects.get(pk=id)
            except Author.DoesNotExist:
                raise CommandError('Author "%s" does not exist' % id)

            try:
                stats = cache.get('user_stat-'+str(author.id))
                print(stats)
            except Exception as e:
                raise CommandError('Data not found for {} author {}'.format(
                    str(id), str(e)))

            self.stdout.write(
                self.style.SUCCESS(
                    'Successfully updated stat of author {}'.format(id)))
