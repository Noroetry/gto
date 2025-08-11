import os
from src.collectors.pokerstars_collector import PokerStarsCollector
from src.parser.pokerstars_parser import PokerStarsParser
from src.analyzers.pokerstars_analyzer import PokerStarsAnalyzer
from config import settings
import logging

room_logger = logging.getLogger(__name__)

class PokerStarsRoom(object):
    def __init__(self):
        self.name_room = 'pokerstars'

        self.collector = PokerStarsCollector(self.name_room, active=True)
        self.parser = PokerStarsParser(self.name_room, active=True)
        self.analyzer = PokerStarsAnalyzer(self.name_room, active=True)

        room_logger.debug("PokerStars Room initializated.")