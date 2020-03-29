import logging


class Logger:
    def __init__(self, name):
        self.logger = logging.getLogger(name)

    def get_logger(self):
        self.logger.setLevel(logging.DEBUG)
        self._get_logger_handler()
        return self.logger

    def _get_formatter(self):
        return logging.Formatter('[%(levelname)s][%(asctime)s][%(name)s][function:%(funcName)s]'
                                 '[tid:%(thread)d][pid:%(process)d] - %(message)s')

    def _get_logger_handler(self):
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(self._get_formatter())
        self.logger.addHandler(ch)