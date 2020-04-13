import concurrent.futures
import multiprocessing

from geteway.wiki_gateaway import *
from utils.logger import Logger

logger = Logger(__name__).get_logger()


def check_page(page, search_obj):
    logger.info('Checking {}'.format(page.title))
    target_page = search_obj.target_page
    if page.title == "Allergic bronchopulmonary aspergillosis":
        print("#### Watchout!!! \nAllergic bronchopulmonary aspergillosis\n")
    if page.title == target_page or page.links.get(target_page) is not None:
        return True
    else:
        search_obj.add_links_to_queue(page)
        return False

class AsyncConsts:
    WORKERS = multiprocessing.cpu_count()
    # WORKERS = 2

class AsyncSearch:
    def __init__(self, start_page, target_page):
        self.start_page = start_page
        self.target_page = target_page
        self.q = multiprocessing.Queue()
        self.keep_searching_flag = True

    def add_links_to_queue(self, page):
        self.q.put([link for link in page.links.values() if link.namespace == 0])

    def run(self):
        logger.info("Trying to find a path between {} and {}".format(self.start_page, self.target_page))
        start_page = WikiGateway().page(self.start_page)
        if check_page(start_page, self) is True:
            logger.info("Source and target pages are the same: {} <-> {}".format(self.start_page, self.target_page))
            return True
        self.add_links_to_queue(start_page)
        while not self.q.empty() and self.keep_searching_flag:
            with concurrent.futures.ThreadPoolExecutor(max_workers=AsyncConsts.WORKERS) as executor:
                desired_path = None
                future_to_page = {executor.submit(check_page, page, self): page for page in self.q.get()}
                for future in concurrent.futures.as_completed(future_to_page):
                    if future_to_page[future] is True:
                        desired_path = True
                if desired_path is True:
                    self.keep_searching_flag = False
                logger.info('There are {} lists of links in the queue'.format(str(self.q.qsize())))
        print("#####found a path###")


if __name__=="__main__":
    s = AsyncSearch('Coronavirus', 'Amino acid transporter')
    # s = AsyncSearch('Sloth', 'Argentina')
    s.run()
