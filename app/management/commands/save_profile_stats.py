from django.core.management.base import BaseCommand
from django.core.cache import cache


from app.models import Author, Entry, Title, Vote
from app.models import FollowAuthor


class Command(BaseCommand):
    help = "Save all users stat to cache"

    def handle(self, *args, **options):
        try:
            authors = Author.objects.all()

            for author in authors:
                entry_count = Entry.objects.filter(author=author).count()
                title_count = Title.objects.filter(owner=author).count()
                follower_count = FollowAuthor.objects.filter(
                    follow=author).count()
                vote_count = Vote.objects.filter(entry__author=author).count()
                up_vote_count = Vote.objects.filter(
                    entry__author=author,
                    is_up=True).count()
                data = {
                    'entry_count': entry_count,
                    'title_count': title_count,
                    'follower_count': follower_count,
                    'vote_count': vote_count,
                    'up_vote_count': up_vote_count,
                }
                cache.set(
                    'users-stats-'+str(author.id),
                    data,
                    timeout=72000)
                self.stdout.write(
                    self.style.SUCCESS(
                        """Successfully saved user stats:
                            username: {username}
                            entry_count: {ec}
                            title_count: {tc}
                            follower_count: {fc}
                            vote_count: {vc}
                            up_vote_count: {uvc}
                            """.format(
                                username=author.username,
                                ec=entry_count,
                                tc=title_count,
                                fc=follower_count,
                                vc=vote_count,
                                uvc=up_vote_count
                            )))
        except Exception as e:
            self.stdout.write(self.style.ERROR_OUTPUT(str(e)))
