import uuid

from django.utils import timezone
from django_ckeditor_5.fields import CKEditor5Field

from cassandra.cqlengine import columns
from django_cassandra_engine.models import DjangoCassandraModel


class Entry(DjangoCassandraModel):
    uid = columns.UUID(primary_key=True, default=uuid.uuid4)
    created_at = columns.DateTime()
    updated_at = columns.DateTime()
    content = CKEditor5Field(
        max_length=2000,
        null=True,
        blank=True)
    author_id = columns.Integer(index=True)
    title = columns.Text(required=True)

    @property
    def is_edited(self):
        compare_created_at = self.created_at.strftime("%B %d %Y - %I:%M %p")
        compare_updated_at = self.updated_at.strftime("%B %d %Y - %I:%M %p")
        return (compare_created_at != compare_updated_at)

    def save(self, *args, **kwargs):
        now = timezone.now()
        if not self.created_at:
            self.created_at = now
        self.updated_at = now
        super(Entry, self).save(*args, **kwargs)

    def __str__(self):
        return '{} - {} - {}'.format(self.title, self.author, self.created_at)
