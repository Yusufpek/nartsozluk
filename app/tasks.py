from celery import shared_task
from django.core import management

from .ai_utils import AI, create_entry
from .models import Title, Topic, Author


@shared_task
def create_random_entries_task(count):
    management.call_command('create_random_entry', count=[count])
    return True


@shared_task
def create_ai_title_task(title_count, entry_count):
    user = Author.objects.filter(username='bot').first()
    if not user:
        return "no user found as a bot"
    ai = AI()
    while title_count > 0:
        try:
            response = ai.create_new_title()
            title = Title.objects.filter(
                text=response['title']).first()
            if not title:
                topic = Topic.objects.filter(
                    text=response['topic']).first()
                if not topic:
                    topic = Topic(text=response['topic'])
                    topic.save()
                title = Title(
                    text=response['title'],
                    topic=topic,
                    owner=user)
                title.save()
                print('created title id:{id}, text: {text}'.format(
                    id=title.id, text=title.text))
                create_entry(
                    response['entry'], user, title)
                entry_res = ai.get_new_entries_to_title(
                    title, entry_count-1)
                for res in entry_res:
                    create_entry(res, user, title)
                title_count -= 1
            else:
                print("-------------------------------")
                print('title already exist: ', title)
                print("-------------------------------")

        except Exception as e:
            print("error while creating: " + str(e))
    return "Proccess done!"
