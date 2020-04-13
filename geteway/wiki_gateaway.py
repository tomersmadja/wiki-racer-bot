import wikipediaapi


# TODO: Refactor gateway to get only required info- links, title, category
class WikiGateway:
    def __init__(self):
        pass

    def page(self, title):
        wiki = wikipediaapi.Wikipedia('en')
        page = wiki.page(title)
        return page


# class WikiGateway:
#     def __init__(self):
#         self.base_url =
#
#     def page(self, title):
#         wiki = wikipediaapi.Wikipedia('en')
#         page = wiki.page(title)
#         return page
