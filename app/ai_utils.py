import google.generativeai as genai
import os

from .models import Entry
from .utils import format_entry_urls

class AI:
    def __init__(self) -> None:
        GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
        genai.configure(api_key=GOOGLE_API_KEY)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def create_new_title(self):
        response = self.model.generate_content(
            """We have a dictionary which has titles and entries,
            the titles are about some topics which are career,
            music, sport, news and other can you write one title
            max 100 character and one entry in turkish and write the topic.
            Some examples of titles and entries
            topic: carrer, title: 'hacettepe', the entries: ['okulum', 'tıpı ile ünlü okul', 'hacettepe kariyer fuarını yapan okul'],
            topic: career, title: 'odtü' entries: ['mentorumun okulu', 'açılımı ortadoğu teknik üniversitesi olan üniversite'],
            topic: career, title: 'technarts', entries: ['mentorumun okulu', 'açılımı ortadoğu teknik üniversitesi olan üniversite'],
            topic: sport, title: 'paris yaz olimpiyatları', entries: ['güzel bi açılışla başlayan olimpiyat', 'voleybolda yarı finalde elendiğimiz yarışmalar bütünü'],
            topic: sport, title: 'galatasaray', entries: ['<p>tuttuğum takım</p>', '<p>son <strong>süper lig</strong> şampiyonu<p>'],
            topic: music, title: 'dolu kadehi terst tut', entries: ['en sevdiğim müzik grubu', 'yeni singleı bknz: https://www.youtube.com/watch?v=fjpgdivWwt0 olan grup']
            topic: music, title: 'aleyna tilki', entries: ['Sen Olsan Bari klibiyle tanıdığım sanatçı. Sesine hayranım.', 'En bilinen şarkılarından bazıları "Sen Olsan Bari" ve "Dipsiz Kuyu"']
            you can write the entry content with html content (a, small, italic, bold etc)
            do not write " ' * or character count etc to title and topic just write the text
            write in the format of:
            # Topic: <topic>
            # Title: <title>
            # Entry: <entry>
            """
            )
        text = response.text
        print(text)
        data = {
            'topic': text.split('# Topic: ')[1].split('\n')[0],
            'title': text.split('# Title: ')[1].split('\n')[0],
            'entry': text.split('# Entry: ')[1].split('\n')[0],
        }
        return data

    def get_new_entries_to_title(self, title, count):
        response = self.model.generate_content(
            """We have a dictionary which has titles and entries,
                the titles are about some topics which are career,
                music, sport, news and other can you write {count} entry
                up to 500 character for {title} in {topic} topic. It is up to
                500 chars, create different lengths entries.
                Some examples of titles and entries
                topic: carrer, title: 'hacettepe', the entries: ['okulum', 'tıpı ile ünlü okul', 'hacettepe kariyer fuarını yapan okul'],
                topic: career, title: 'odtü' entries: ['mentorumun okulu', 'açılımı ortadoğu teknik üniversitesi olan üniversite'],
                topic: career, title: 'technarts', entries: ['mentorumun okulu', 'açılımı ortadoğu teknik üniversitesi olan üniversite'],
                topic: sport, title: 'paris yaz olimpiyatları', entries: ['güzel bi açılışla başlayan olimpiyat', 'voleybolda yarı finalde elendiğimiz yarışmalar bütünü'],
                topic: music, title: 'dolu kadehi terst tut', entries: ['en sevdiğim müzik grubu', 'yeni singleı bknz: https://www.youtube.com/watch?v=fjpgdivWwt0 olan grup']
                you can write the entry content with html content (a, small, italic, bold etc)
                can u write in the just format of:
                ## Entry: <entry>
                ## Entry: <entry>
            """.format(title=title.text, topic=title.topic, count=count))
        response_text = response.text
        print("entry response text: ", response_text)
        data = []
        for text in response_text.split("## Entry: ")[1:]:
            print("text:", text)
            data.append(text)
        return data


def create_entry(content, user, title):
    content = format_entry_urls(content)
    entry = Entry(content=content, author=user, title=title)
    entry.save()
    print('created entry id:{id}, text: {text}'.format(
        id=entry.id, text=entry.content))
