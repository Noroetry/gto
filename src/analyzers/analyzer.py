
from config import settings
import os
import logging
from src.analyzers.preflop_analyzer import PreflopAnalyzer
from src.analyzers.pot_analyzer import PotAnalyzer

analyzer_logger = logging.getLogger(__name__)

class Analyzer():
    def __init__(self, active: bool):
        self.hero_name = settings.POKERSTARS_HERO_NAME
        self.formatted_dir = settings.FORMATTED_HANDS_DIR
        self.analyzed_dir = settings.ANALYZED_HANDS_DIR

        self.analyzers = [
            PreflopAnalyzer(self.analyzed_dir, self.formatted_dir, self.hero_name),
            PotAnalyzer(self.analyzed_dir, self.formatted_dir, self.hero_name)
        ]

        analyzer_logger.debug("PokerStars Analyzer initializated.")
        analyzer_logger.debug(f"Formatted path: {self.formatted_dir}")
        analyzer_logger.debug(f"Analyzed path: {self.analyzed_dir}")

        if active:
            self.execute_analyzers()

    def execute_analyzers(self) -> None:
        analyzer_logger.info("Starting analysis of PokerStars hands...")
        for analyzer in self.analyzers:
            analyzer_logger.debug(f"Executing analyzer: {analyzer.__class__.__name__}")
            analyzer.analyze_all()
        analyzer_logger.info("All analyzers executed successfully.")