from django.db import models
from django.contrib.auth.models import AbstractUser

from .constants import COUNT_CHOICES


# Create your models here.
class Author(AbstractUser):
    random_entry_count = models.CharField(
        max_length=2,
        default='10',
        choices=COUNT_CHOICES)
    title_entry_count = models.CharField(
        max_length=2, default='10', choices=COUNT_CHOICES)
    profile_image = models.ImageField(
        upload_to='profile_pictures', default='default.jpg')
    entry_count = models.IntegerField(default=0)
    title_count = models.IntegerField(default=0)
    follower_count = models.IntegerField(default=0)
    vote_count = models.IntegerField(default=0)
    up_vote_count = models.IntegerField(default=0)

    def __str__(self):
        return self.username
