from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinLengthValidator


# Create your models here.
class Author(AbstractUser):
    def __str__(self):
        return self.username


class Title(models.Model):
    text = models.CharField(max_length=50, validators=[MinLengthValidator(3)])
    created_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(Author, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.text


class Entry(models.Model):
    text = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(Author,  null=True, on_delete=models.SET_NULL)
    title = models.ForeignKey(Title, on_delete=models.CASCADE)

    def is_edited(self):
        return (self.created_at != self.updated_at)

    def __str__(self):
        return '{} - {} - {}'.format(self.title, self.author, self.created_at)


class Vote(models.Model):
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE)
    voter = models.ForeignKey(Author, on_delete=models.CASCADE)
    is_up = models.BooleanField(default=True)


class AuthorsFavorites(models.Model):
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('entry', 'author')  # for no duplicate favorites


class FollowAuthor(models.Model):
    user = models.ForeignKey(Author, on_delete=models.CASCADE,
                             related_name="user")
    follow = models.ForeignKey(Author, on_delete=models.CASCADE,
                               related_name="follow")
    follow_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'follow')  # for no duplicate
