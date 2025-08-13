import abc

class BaseCollector(abc.ABC):
    def __init__(self, source_dir: str, end_dir: str):
        self.source_dir = source_dir
        self.end_dir = end_dir

    @abc.abstractmethod
    def collect_files(self) -> int:
        pass