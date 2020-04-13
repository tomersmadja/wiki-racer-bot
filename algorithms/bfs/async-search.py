import concurrent.futures
import multiprocessing
import queue

from geteway.wiki_gateaway import *
from utils.logger import Logger

logger = Logger(__name__).get_logger()


def check_page(page, search_obj, parents):
    logger.info('Checking {}'.format(page.title))
    target_page = search_obj.target_page
    if page.title == target_page or page.links.get(target_page) is not None:
        path = parents + [page.title] if page.title == target_page else parents + [page.title, search_obj.target_page]
        return path
    else:
        search_obj.add_links_to_queue(page, parents)
        return None


class AsyncConsts:
    WORKERS = multiprocessing.cpu_count()
    # WORKERS = 2


class PagesList(list):
    def __lt__(self, other):
        return True

    def __le__(self, other):
        return True

    def __gt__(self, other):
        return True

    def __ge__(self, other):
        return True


class QueuedRankedLinksList(dict)


class AsyncSearch:
    def __init__(self, start_page, target_page):
        self.start_page = start_page
        self.target_page = target_page
        self.target_page_categories = list(WikiGateway().page(self.target_page).categories.keys())
        self.q = multiprocessing.Queue()
        # self.q = queue.PriorityQueue()
        self.keep_searching_flag = True

    def _get_page_rank(self, page):
        categories = page.categories.keys()
        rank = 0
        for cat in categories:
            if cat in self.target_page_categories:
                rank -= 1
        return rank

    def add_links_to_queue(self, page, parents):
        links_list = PagesList()
        for link in page.links.values():
            if link.namespace == 0:
                links_list.append(link)
        self.q.put({'ranked_links_list': (self._get_page_rank(page), links_list), 'parents': parents + [page.title]})

# def add_links_to_queue(self, page, parents):
#         links_list = PagesList()
#         for link in page.links.values():
#             if link.namespace == 0:
#                 links_list.append(link)
#         self.q.put({'ranked_links_list': (self._get_page_rank(page), links_list), 'parents': parents + [page.title]})
#
    def run(self):
        self._handle_start_page()
        while not self.q.empty() and self.keep_searching_flag:
            with concurrent.futures.ThreadPoolExecutor(max_workers=AsyncConsts.WORKERS) as executor:
                next_list_in_the_queue = self.q.get()
                logger.info("Now traversing list with priority of " +
                            str(next_list_in_the_queue['ranked_links_list'][0]))
                future_to_page = {executor.submit(check_page, page, self, next_list_in_the_queue['parents']): page
                                  for page in next_list_in_the_queue['ranked_links_list'][1]}
                for future in concurrent.futures.as_completed(future_to_page):
                    if future.result() is not None:
                        self.keep_searching_flag = False
                        return future.result()
                logger.info('There are {} lists of links in the queue'.format(str(self.q.qsize())))
        print("#####found a path###")

    def _handle_start_page(self):
        logger.info("Trying to find a path between {} and {}".format(self.start_page, self.target_page))
        start_page = WikiGateway().page(self.start_page)
        self.add_links_to_queue(start_page, [])


if __name__ == "__main__":
    # s = AsyncSearch('Coronavirus', 'Amino acid transporter')
    s = AsyncSearch('Grid Compass', 'Mobile operating system')
    # s = AsyncSearch('Operating system', 'Mobile operating system')
    print(s.run())
