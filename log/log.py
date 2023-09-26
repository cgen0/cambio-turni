import logging.config
import sys

from singleton_decorator import singleton


@singleton
class Log:

    def __init__(self):
        logging.basicConfig(stream=sys.stdout,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def info(self, message):
        print(message)
        #self.logger.info(message)

    def error(self, message):
        #self.logger.error(message)
        print(message)
