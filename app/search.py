from .documents import AuthorDocument, TitleDocument


def search_authors(query):
    authors = AuthorDocument.search().query("match", username=query,)
    response = authors.execute()
    print(response)
    return response


def search_titles(query):
    titles = TitleDocument.search().query("match", text=query,)
    response = titles.execute()
    print(response)
    return response
