from celery import shared_task

from .utils import send_delete_account_email, send_register_email
from log.models import Log


@shared_task
def send_delete_account_email_task(username, email):
    log = Log(
        task_name="Account Delete Email Task - " + username,
        category=Log.Category.AUTH
    )
    log.save()
    response = send_delete_account_email(
        username,
        email
    )
    log.complete_task(response)
    return response


@shared_task
def send_register_email_task(username, email):
    log = Log(
        task_name="Register Email Task - " + username,
        category=Log.Category.AUTH
    )
    log.save()
    response = send_register_email(
        username,
        email
    )
    log.complete_task(response)
    return response
