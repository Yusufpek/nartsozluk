import datetime

from cassandra.cqlengine import columns
from django_cassandra_engine.models import DjangoCassandraModel


class EntryLog(DjangoCassandraModel):
    created_at = columns.DateTime(
        primary_key=True,
        default=datetime.datetime.now)
    value = columns.Integer(default=0)
    entry_uid = columns.UUID()
