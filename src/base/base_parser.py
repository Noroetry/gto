import abc
import logging

base_parser_logger = logging.getLogger(__name__)

class BaseParser(abc.ABC):
    def __init__(self, source_dir: str, processed_dir: str, formatted_dir: str):
        self.source_dir = source_dir
        self.processed_dir = processed_dir
        self.formatted_dir = formatted_dir
        base_parser_logger.debug("Base Parser initializated")

    @abc.abstractmethod
    def check_dir(self) -> bool:
        pass

    @abc.abstractmethod
    def parse_files(self):
        pass

    @abc.abstractmethod
    def format_file(self, filename: str):
        pass

    @abc.abstractmethod
    def format_hand(self, hand_text: str):
        pass

    @abc.abstractmethod
    def convert_all_to_json(self):
        pass