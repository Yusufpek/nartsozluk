import google.generativeai as genai
import os

from .models import Entry, Title, Topic
from .utils import format_entry_urls

import random


class AI:
    examples = """
    Some examples of titles and entries
    topic: carrer, title: 'hacettepe', the entries: ['okulum', 'tıpı ile ünlü okul', 'hacettepe kariyer fuarını yapan okul'],
    topic: career, title: 'odtü' entries: ['mentorumun okulu', 'açılımı ortadoğu teknik üniversitesi olan üniversite'],
    topic: career, title: 'technarts', entries: ['mentorumun okulu', 'açılımı ortadoğu teknik üniversitesi olan üniversite'],
    topic: sport, title: 'paris yaz olimpiyatları', entries: ['güzel bi açılışla başlayan olimpiyat', 'voleybolda yarı finalde elendiğimiz yarışmalar bütünü'],
    topic: sport, title: 'galatasaray', entries: ['<p>tuttuğum takım</p>', '<p>son <strong>süper lig</strong> şampiyonu<p>'],
    topic: music, title: 'dolu kadehi terst tut', entries: ['en sevdiğim müzik grubu', 'son single https://www.youtube.com/watch?v=fjpgdivWwt0 olan grup']
    topic: other, title: 'ankara', entries: ['palak kodu 06 olan şehir', 'odtü, hacettepe, bilkent gibi üniversiteleri bünyesindebulunduran şehir', '<strong>başkent</strong>']
    """  # noqa: E501 - ignore long line

    def __init__(self) -> None:
        GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
        genai.configure(api_key=GOOGLE_API_KEY)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def create_new_title(self):
        titles = Title.objects.all().values_list('text', flat='true')
        title_texts = '\n'
        for title in titles:
            title_texts += '- ' + title + '\n'
        response = self.model.generate_content(
            """We have a dictionary which has titles and entries,
            the titles are about some topics which are career,
            music, sport, news and other can you write one title
            max 100 character and one entry in turkish and write the topic.
            {examples}
            here is the existing titles list, create completely different
            NEW title: {titles}
            WRITE NEW TITLE excluding this list!
            you can write the entry content with html content
            (a href, small, italic, bold etc.)
            DO NOT WRITE ", ', *, or character count etc. to title and topic
            just write the text. write in the format of:
            # Topic: <topic>
            # Title: <title>
            # Entry: <entry>
            """.format(
                examples=AI.examples,
                titles=title_texts))
        text = response.text
        data = {
            'topic': text.split('# Topic: ')[1].split('\n')[0].lower().strip(),
            'title': text.split('# Title: ')[1].split('\n')[0].lower().strip(),
            'entry': text.split('# Entry: ')[1].split('\n')[0],
        }
        return data

    def get_new_entries_to_title(self, title, count):
        response = self.model.generate_content(
            """We have a dictionary which has titles and entries,
                the titles are about some topics which are career,
                music, sport, news and other can you write {count} entry
                up to 500 character for {title} in {topic} topic. It is up to
                500 chars, create different lengths entries in turkish.
                {examples}
                you can write the entry content with html content
                (a, small, italic, bold etc). do not use *, write in html
                format if you need. Can u write in the just format of:
                ## Entry: <entry>
                ## Entry: <entry>
            """.format(
                examples=AI.examples,
                title=title.text,
                topic=title.topic,
                count=count))
        response_text = response.text
        data = []
        for text in response_text.split("## Entry: ")[1:]:
            data.append(text)
        return data[:count]

    def get_entries_like_an_entry(self, title, entry, count):
        print("given entry: ", entry.content)
        response = self.model.generate_content(
            """We have a dictionary which has titles and entries,
                the titles are about some topics which are career,
                music, sport, news and other can you write {count} entry
                up to 500 character for {title} in {topic} topic. It is up to
                500 chars, create different lengths entries like a given entry
                style in turkish. {examples}
                here is the base entry, write an entry like that, act like
                this entry's author and write {count} entry for {title} title.
                base entry: {entry_content}
                you can write the entry content with html content
                (a, small, italic, bold etc). do not use *, write in html
                format if you need. Can u write in the just format of:
                ## Entry: <entry>
                ## Entry: <entry>
            """.format(
                examples=AI.examples,
                title=title.text,
                topic=title.topic,
                count=count,
                entry_content=entry.content))
        response_text = response.text
        data = []
        for text in response_text.split("## Entry: ")[1:]:
            data.append(text)
        return data[:count]


def create_entry(content, user, title):
    content = format_entry_urls(content)
    entry = Entry(content=content, author=user, title=title)
    entry.save()
    print('created entry id:{id}, text: {text}'.format(
        id=entry.id, text=entry.content))


def create_random_entries(user, count):
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
            title_content += words[i]
        topic = Topic.objects.filter(text='other').first()
        title = Title(text=title_content, topic=topic, owner=user)
        title.save()
        for j in range(10):
            entry_content = ''
            for k in range(random.randint(3, 10)):
                randomize = random.randint(50, 120)
                entry_content += words[-(i+j+k+randomize)]
            create_entry(entry_content, user, title)
