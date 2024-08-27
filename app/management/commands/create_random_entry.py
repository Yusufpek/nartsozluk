from django.core.management.base import BaseCommand, CommandError
from app.models import Title, Topic, Author
from entry.models import Entry

import os
import random


class Command(BaseCommand):
    help = "Delete the last entries"

    def add_arguments(self, parser):
        parser.add_argument("--count", nargs="+", type=int)
        parser.add_argument("--entry_count", nargs="+", type=int, default=10)

    def create_random_entries(self, user, count, entry_count):
        words = []
        module_dir = os.path.dirname(__file__)
        file_path = os.path.join(module_dir, 'words.txt')  # full path to text.
        with open(file_path, 'r') as file:
            words = file.readlines()

        for i in range(count):
            word_count = random.randint(1, 5)
            random.shuffle(words)
            title_content = ''
            for i in range(word_count):
                title_content += (words[i].replace('\n', ' '))
            topic = Topic.objects.filter(text='other').first()
            title = Title(text=title_content, topic=topic, owner=user)
            title.save()
            for j in range(entry_count):
                entry_content = ''
                for k in range(random.randint(3, 10)):
                    randomize = random.randint(50, 120)
                    entry_content += words[-(i+j+k+randomize)]
                    entry_content = entry_content.replace('\n', ' ')
                entry = Entry(
                    content=entry_content,
                    author_id=user.id,
                    title=title)
                entry.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        'created entry id:{id}, text: {text}'.format(
                            id=entry.id, text=entry.content)))

    def handle(self, *args, **options):
        count = options["count"][0]
        try:
            entry_count = options["entry_count"][0]
        except:  # noqa: E722 - ignore exception
            self.stdout.write(self.style.WARNING("Entry count set default 10"))
            entry_count = 10
        if not entry_count:
            entry_count = 10
        try:
            author = Author.objects.filter(username='bot').first()
            self.create_random_entries(author, count, entry_count)
        except Exception as e:
            raise CommandError('Error while creating random' + str(e))

        self.stdout.write(
            self.style.SUCCESS(
                'Successfully created {} tiltes, {} entries'.format(
                    count,
                    entry_count * count)))
