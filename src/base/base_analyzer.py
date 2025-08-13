import abc

class BaseAnalyzer(abc.ABC):
    def __init__(self, source_dir: str, formatted_dir: str, analyzed_dir: str):
        self.source_dir = source_dir
        self.formatted_dir = formatted_dir
        self.analyzed_dir = analyzed_dir

    @abc.abstractmethod
    def analyze_all(self) -> None:
        pass

    @abc.abstractmethod
    def analyze_hand(self, hand_data) -> dict:
        pass