import uuid

from django.db import models
from django_ckeditor_5.fields import CKEditor5Field
from timescale.db.models.fields import TimescaleDateTimeField
from timescale.db.models.managers import TimescaleManager


from authentication.models import Author
from app.models import Title


class TimescaleModel(models.Model):
    created_at = TimescaleDateTimeField(
        interval="1 day",
        auto_now_add=True)
    objects = TimescaleManager()

    class Meta:
        abstract = True
        unique_together = (('uid', 'created_at'),)


class Entry(TimescaleModel):
    uid = models.UUIDField(default=uuid.uuid4, editable=False)
    content = CKEditor5Field(max_length=2000, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(Author,  null=True, on_delete=models.SET_NULL)
    title = models.ForeignKey(Title, on_delete=models.CASCADE)

    class Meta:
        indexes = [
            models.Index(fields=['created_at', 'author'])]

    def is_edited(self):
        compare_created_at = self.created_at.strftime("%B %d %Y - %I:%M %p")
        compare_updated_at = self.updated_at.strftime("%B %d %Y - %I:%M %p")
        return (compare_created_at != compare_updated_at)

    def __str__(self):
        return '{} - {} - {}'.format(self.title, self.author, self.created_at)
