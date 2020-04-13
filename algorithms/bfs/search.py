import multiprocessing
from collections import deque

import time

from geteway.wiki_gateaway import *
from utils.logger import Logger

logger = Logger(__name__).get_logger()


class AsyncConsts:
    PROCESSES = multiprocessing.cpu_count()
    # PROCESSES = 2


class SyncSearch:
    def __init__(self, start, end):
        self.logger = Logger(__name__).get_logger()
        self.start = start
        self.end = end
        self.q = deque()
        # Add the source value - root node to the queue
        self._add_starting_node_page_to_queue()

    def _add_starting_node_page_to_queue(self):
        start_page = WikiGateway().page(self.start)
        if self._is_direct_path_to_end(start_page):
            self.logger.info('start_page and end_page are the same pages!')
        else:
            self.q.appendleft({
                'parent': [start_page.title],
                'pages': (subpage for subpage in start_page.links.values() if subpage.namespace == 0)}
            )

    def _is_direct_path_to_end(self, page):
        return (page.title == self.end) or (page.links.get(self.end) is not None)

    def _add_links_to_queue(self, current_page, sub_page):
        self.logger.info('"{}" or its sub links are not the target page, adding links to the qeuue'.format(
            sub_page.title
        ))
        self.q.appendleft(
            {
                'parent': current_page['parent'] + [sub_page.title],
                'pages': (link for link in sub_page.links.values() if link.namespace == 0)
            }
        )

    def _path_is_found(self, current_page, sub_page):
        path = current_page['parent'] + [sub_page.title]
        if sub_page.title != self.end:
            path.append(self.end)
        self.logger.info('Found a path between start_page- "{}" and end_page- "{}":\n{}'.format(
            self.start, self.end, str(path)
        ))
        return {'path': path}

    def start_search(self):
        while len(self.q) != 0:
            current_page = self.q.pop()
            self.logger.info("The current path is:\n" + str(current_page['parent']))
            for sub_page in current_page['pages']:
                if self._is_direct_path_to_end(sub_page):
                    return self._path_is_found(current_page, sub_page)
                else:
                    self._add_links_to_queue(current_page, sub_page)


class AsyncSearch:
    def __init__(self, start, end):
        self.start = start
        self.end = end
        self.q = multiprocessing.Queue()

    def _add_starting_node_page_to_queue(self):
        start_page = WikiGateway().page(self.start)
        return self._check_page(start_page)

    def _is_direct_path_to_end(self, page):
        return (page.title == self.end) or (page.links.get(self.end) is not None)

    def _add_tasks_to_queue(self, pages):
        for page in pages:
            self.q.put(page)

    def _check_page(self, page):
        logger.info('Checking page "{}"'.format(page.title))
        if self._is_direct_path_to_end(page):
            return True
        else:
            links = page.links
            logger.info("Couldn't find a direct path form \"{}\", "
                        "adding {} pages to the queue.".format(page.title, len(links)))
            self._add_tasks_to_queue(links.values())
            return None

    def _check_pages_in_queue(self, tasks_queue):
        while not tasks_queue.empty():
            try:
                page = self.q.get()
                if self._check_page(page):
                    print("#####\nPATH FOUND\n####")
                    return True
            except Exception as e:
                logger.error(e)
                raise e
        return True

    def start_search(self):
        processes = []
        logger.debug(f'Running with {AsyncConsts.PROCESSES} processes!')
        start_time = time.time()
        if self._add_starting_node_page_to_queue():
            return True
        for available_processes in range(AsyncConsts.PROCESSES):
            p = multiprocessing.Process(target=self._check_pages_in_queue, args=(self.q,))
            processes.append(p)
            p.start()
        for p in processes:
            p.join()
        logger.debug(f'Time taken = {time.time() - start_time:.10f}')


# s = SyncSearch('Python_(programming_language)', 'Algebraic_structure')
# # s = SyncSearch('Sloth', 'Joseph_Black')
# s.start_search()
if __name__ == "__main__":
    # s = AsyncSearch('Sloth', 'Argentina')
    s = AsyncSearch('Coronavirus', 'Amino acid transporter')
    # s = SyncSearch('Sloth', 'Joseph_Black')
    s.start_search()
