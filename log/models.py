from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError


class Log(models.Model):
    class Status(models.TextChoices):
        NOT_STARTED = "NOT_STARTED"
        RUNNING = "RUNNING"
        COMPLETED = "COMPLETED"
        ERROR = "ERROR"

    class Category(models.TextChoices):
        MANAGE = "Manage"
        ENTRY = "Entry"
        AUTH = "Auth"
        PERIODIC = "Periodic"

    task_name = models.CharField(max_length=200)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    duration = models.DurationField(null=True)
    task_status = models.CharField(
        max_length=11,
        choices=Status.choices,
        default=Status.RUNNING)
    category = models.CharField(
        max_length=8,
        choices=Category.choices)
    output = models.TextField(null=True, blank=True)

    def complete(self, output, status):
        self.output = output
        self.task_status = status
        self.end_time = timezone.now()
        self.duration = self.end_time - self.start_time
        self.save()

    def complete_task(self, output):
        self.complete(output, self.Status.COMPLETED)

    def complete_task_error(self, output):
        self.complete(output, self.Status.ERROR)

    def clean(self):
        if self.end_time and self.end_time < self.start_time:
            raise ValidationError('Incorrect time format')
