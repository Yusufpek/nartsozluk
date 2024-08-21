from celery import shared_task

from .utils import send_delete_account_email, send_register_email


@shared_task
def send_delete_account_email_task(username, email):
    response = send_delete_account_email(
        username,
        email
    )
    return response


@shared_task
def send_register_email_task(username, email):
    response = send_register_email(
        username,
        email
    )
    return response
