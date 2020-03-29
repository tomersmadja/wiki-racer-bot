import wikipediaapi


class WikiGateway:
    def __init__(self):
        pass

    def page(self, title):
        wiki = wikipediaapi.Wikipedia('en')
        page = wiki.page(title)
        return page

