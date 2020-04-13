import concurrent.futures
import multiprocessing
import queue
import time
from datetime import datetime

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


class RankedLinksList(dict):
    def __lt__(self, other):
        return self['rank'] < other['rank']

    def __le__(self, other):
        return self['rank'] <= other['rank']

    def __gt__(self, other):
        return self['rank'] > other['rank']

    def __ge__(self, other):
        return self['rank'] >= other['rank']


class AsyncSearch:
    def __init__(self, start_page, target_page, use_naive_search=False):
        """
        :param start_page: Start page title
        :param target_page: End page title
        :param naive_search: While True, the search method doesn't considers categories similarity. False by default
        """
        self.start_page = start_page
        self.target_page = target_page
        self.target_page_categories = list(WikiGateway().page(self.target_page).categories.keys())
        self.q = queue.PriorityQueue() if not use_naive_search else queue.Queue()
        self.use_naive_search = use_naive_search

    def _get_page_rank(self, page):
        categories = page.categories.keys()
        rank = 0
        for cat in categories:
            if cat in self.target_page_categories:
                rank -= 1
        return rank

    def add_links_to_queue(self, page, parents):
        ranked_links_list = RankedLinksList({
            'links': [link for link in page.links.values() if link.namespace == 0],
            'rank': self._get_page_rank(page) if not self.use_naive_search else 0,
            'parents': parents + [page.title]
        })
        self.q.put(ranked_links_list)
        logger.info('{} links were added, they are {}\'s children.'
                    .format(str(len(ranked_links_list['links'])), str(ranked_links_list['parents'])))

    def run(self):
        self._handle_start_page()
        while not self.q.empty():
            result = self._check_pages_list_concurrently()
            if result:
                return result

    def _check_pages_list_concurrently(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=AsyncConsts.WORKERS) as executor:
            next_list_in_the_queue = self.q.get()
            logger.info("Now traversing list with priority of " + str(abs(next_list_in_the_queue['rank'])))
            future_to_page = {executor.submit(check_page, page, self, next_list_in_the_queue['parents']): page
                              for page in next_list_in_the_queue['links']}
            for future in concurrent.futures.as_completed(future_to_page):
                if future.result() is not None:
                    return future.result()
            logger.info("There are {} lists in the queue".format(str(self.q.qsize())))

    def _handle_start_page(self):
        logger.info("Trying to find a path between {} and {}".format(self.start_page, self.target_page))
        start_page = WikiGateway().page(self.start_page)
        self.add_links_to_queue(start_page, [])


if __name__ == "__main__":
    s = AsyncSearch('Python', 'Total Film')
    start = datetime.now()
    print(s.run())
    print('non-naive search took: ' + str(datetime.now()-start))

    # s = AsyncSearch('Lightning', 'Atlas_(computer)', use_naive_search=True)
    # start = datetime.now()
    # print(s.run())
    # print('naive search took: ' + str(datetime.now()-start))
