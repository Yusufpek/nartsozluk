import os
from celery import Celery
from celery.signals import worker_process_init, beat_init
from cassandra.cqlengine import connection
from cassandra.cqlengine.connection import (
    cluster as cql_cluster, session as cql_session)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nartsozluk.settings')


def cassandra_init(**kwargs):
    """ Initialize a clean Cassandra connection. """
    if cql_cluster is not None:
        cql_cluster.shutdown()
    if cql_session is not None:
        cql_session.shutdown()
    connection.setup(hosts=['cassandra'], default_keyspace="cassandra_db")


# Initialize worker context for both standard and periodic tasks.
worker_process_init.connect(cassandra_init)
beat_init.connect(cassandra_init)


app = Celery('nartsozluk')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
