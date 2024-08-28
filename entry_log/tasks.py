from celery import shared_task
from django.core import management

from log.models import Log

from datetime import datetime


@shared_task
def get_log_summary_task():
    log = Log(
        task_name="Get Log Summary",
        category=Log.Category.PERIODIC
    )
    log.save()
    try:
        management.call_command('get_log_summary')
    except Exception as e:
        print(e)
    now = datetime.now()
    log.complete_task(
        "Summarized entry logs {}".format(now.strftime("%m/%d/%Y, %H:%M")))
    print("log saved :)")
    return True
