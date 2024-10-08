import uuid

from django.db import models
from django.core.validators import MinLengthValidator
from django_ckeditor_5.fields import CKEditor5Field
from timescale.db.models.fields import TimescaleDateTimeField
from timescale.db.models.managers import TimescaleManager

from authentication.models import Author


class TimescaleModel(models.Model):
    created_at = TimescaleDateTimeField(
        interval="1 day",
        auto_now_add=True)
    objects = TimescaleManager()

    class Meta:
        abstract = True
        unique_together = (('uid', 'created_at'),)


# Create your models here.
class Topic(models.Model):
    text = models.CharField(max_length=50)
    created_by = models.ForeignKey(
        Author,
        null=True,
        blank=True,
        on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.text


class Title(models.Model):
    text = models.CharField(
        max_length=100,
        validators=[MinLengthValidator(3)])
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True)
    owner = models.ForeignKey(
        Author,
        null=True,
        on_delete=models.SET_NULL)
    topic = models.ForeignKey(
        Topic,
        null=True,
        blank=True,
        on_delete=models.SET_NULL)

    def __str__(self):
        return self.text


class Entry(TimescaleModel):
    uid = models.UUIDField(default=uuid.uuid4, editable=False)
    updated_at = models.DateTimeField(auto_now=True)
    content = CKEditor5Field(
        max_length=2000,
        null=True,
        blank=True)
    author = models.ForeignKey(
        Author,
        null=True,
        on_delete=models.SET_NULL)
    title = models.ForeignKey(
        Title,
        on_delete=models.CASCADE)

    class Meta:
        indexes = [
            models.Index(fields=['created_at', 'author'])]

    @property
    def is_edited(self):
        compare_created_at = self.created_at.strftime("%B %d %Y - %I:%M %p")
        compare_updated_at = self.updated_at.strftime("%B %d %Y - %I:%M %p")
        return (compare_created_at != compare_updated_at)

    def __str__(self):
        return '{} - {} - {}'.format(self.title, self.author, self.created_at)


class Vote(models.Model):
    entry_id = models.UUIDField()
    is_up = models.BooleanField(default=True)
    voter = models.ForeignKey(
        Author,
        on_delete=models.CASCADE)


class AuthorsFavorites(models.Model):
    entry_id = models.UUIDField()
    author = models.ForeignKey(
        Author,
        on_delete=models.CASCADE)

    class Meta:
        unique_together = ('entry_id', 'author')  # for no duplicate favorites


class FollowAuthor(models.Model):
    user = models.ForeignKey(
        Author,
        on_delete=models.CASCADE,
        related_name="following")
    follow = models.ForeignKey(
        Author,
        on_delete=models.CASCADE,
        related_name="followers")
    follow_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'follow')  # for no duplicate


class FollowTitle(models.Model):
    title = models.ForeignKey(
        Title,
        on_delete=models.CASCADE)
    author = models.ForeignKey(
        Author,
        on_delete=models.CASCADE)
    last_seen = models.DateTimeField(auto_now=True)


class Report(models.Model):
    entry_uid = models.UUIDField()
    date = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=500)
    user = models.ForeignKey(
        Author,
        on_delete=models.CASCADE)

    def __str__(self):
        return self.description + '- entry: ' + str(self.entry_uid)
