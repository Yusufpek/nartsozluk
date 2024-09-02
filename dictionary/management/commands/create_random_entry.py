from django.core.management.base import BaseCommand, CommandError
from dictionary.models import Entry, Title, Topic, Author

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

        entries = []
        for i in range(count):
            word_count = random.randint(1, 5)
            random.shuffle(words)
            title_content = ''
            for m in range(word_count):
                title_content += (words[m].replace('\n', ' '))
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
                    author=user,
                    title=title)
                entries.append(entry)
                self.stdout.write(
                    self.style.SUCCESS(
                        'entry index:{ind}, text: {text} added to list'.format(
                            ind=i*entry_count + k,
                            text=entry.content)))

        Entry.objects.bulk_create(entries)
        self.stdout.write(self.style.SUCCESS('Entry bulk created completed'))

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
