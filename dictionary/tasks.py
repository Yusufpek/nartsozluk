from celery import shared_task
from django.core import management

from .ai_utils import AI, create_entry
from .models import Title, Topic, Author, Entry
from log.models import Log


@shared_task
def create_random_entries_task(count, entry_count):
    log = Log(
        task_name="Create Random Entries - {}".format(count*entry_count),
        category=Log.Category.MANAGE
    )
    log.save()
    management.call_command(
        'create_random_entry',
        count=[count],
        entry_count=[entry_count])
    log.complete_task("Added {} title, {} entries".format(
        count,
        count*entry_count))
    print("log saved :)")
    return True


@shared_task
def create_ai_title_task(title_count, entry_count):
    log = Log(
            task_name="Create Title AI - {}".format(title_count*entry_count),
            category=Log.Category.ENTRY,
        )
    log.save()
    user = Author.objects.filter(username='bot').first()
    if not user:
        output = "no user found as a bot"
        log.complete_task_error(output)
        return output
    try:
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
        log.complete_task("Proccess done!")
        return "Proccess done!"
    except Exception as e:
        log.complete_task_error("Proccess done!")
        return str(e)


@shared_task
def create_new_entries_to_title_task(form_title, entry_count):
    log = Log(
            task_name="Create Title with AI",
            category=Log.Category.ENTRY,
        )
    log.save()

    user = Author.objects.filter(username='bot').first()
    if not user:
        output = "no user found as a bot"
        log.complete_task_error(output)
        return output
    try:
        ai = AI()
        title = Title.objects.filter(pk=form_title).first()
        if title:
            entry_res = ai.get_new_entries_to_title(title, entry_count)
            for res in entry_res:
                create_entry(res, user, title)
            output = str(entry_count) + " Entries added to title!"
            log.complete_task(output)
            return output
        log.complete_task_error("Title not found!")
        return "Title not found"
    except Exception as e:
        log.complete_task_error(str(e))
        return str(e)


@shared_task
def create_entries_like_an_entry_task(entry_id, title_id, count):
    log = Log(
            task_name="Create Title with AI",
            category=Log.Category.ENTRY,
        )
    log.save()

    entry = Entry.objects.filter(uid=entry_id).first()
    title = Title.objects.filter(pk=title_id).first()
    if not (title and entry):
        out = "not found title and entry"
        log.complete_task_error(out)
        return out

    user = Author.objects.filter(username='bot').first()
    if not user:
        output = "no user found as a bot"
        log.complete_task_error(output)
        return output

    try:
        ai = AI()
        entry_res = ai.get_entries_like_an_entry(title, entry, count)
        for res in entry_res:
            create_entry(res, user, title)
        log.complete_task("Like an entries added to title")
        return "Entries added"
    except Exception as e:
        log.complete_task_error(str(e))
        return str(e)
