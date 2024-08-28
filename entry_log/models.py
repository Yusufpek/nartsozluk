import uuid
import datetime

from cassandra.cqlengine import columns
from django_cassandra_engine.models import DjangoCassandraModel


class EntryLog(DjangoCassandraModel):
    created_at = columns.DateTime(
        primary_key=True,
        default=datetime.datetime.now)
    value = columns.Integer(default=0)
    entry_uid = columns.UUID()


class Summary(DjangoCassandraModel):
    # uuid.uuid4(): Generate a random UUID
    id = columns.UUID(primary_key=True, default=uuid.uuid4)
    entry_uid = columns.UUID()
    total_value = columns.Integer()
    record_count = columns.Integer()
    interval = columns.Text()
