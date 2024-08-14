from .documents import AuthorDocument, TitleDocument, TopicDocument


def search_authors(query):
    authors = AuthorDocument.search().query("match", username=query,)
    response = authors.execute()
    print('author', response)
    return response


def search_titles(query):
    titles = TitleDocument.search().query("match", text=query,)
    response = titles.execute()
    print('title', response)
    return response


def search_topics(query):
    topics = TopicDocument.search().query("match", text=query)
    response = topics.execute()
    print('topic', response)
    return response
