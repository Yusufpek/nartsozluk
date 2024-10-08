from django_elasticsearch_dsl import Document
from django_elasticsearch_dsl.registries import registry

from .models import Author, Title, Topic


@registry.register_document
class AuthorDocument(Document):
    class Index:
        name = 'authors'

    class Django:
        model = Author

        fields = [
            'id',
            'username'
        ]


@registry.register_document
class TitleDocument(Document):
    class Index:
        name = 'titles'

    class Django:
        model = Title

        fields = [
            'id',
            'text',
        ]


@registry.register_document
class TopicDocument(Document):
    class Index:
        name = 'topics'

    class Django:
        model = Topic

        fields = [
            'id',
            'text'
        ]
