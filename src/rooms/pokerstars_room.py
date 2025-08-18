from src.collectors.pokerstars_collector import PokerStarsCollector
from src.parser.pokerstars_parser import PokerStarsParser
import logging

room_logger = logging.getLogger(__name__)

class PokerStarsRoom(object):
    def __init__(self, active: bool = False):
        self.name_room = 'pokerstars'
        self.hero_name = 'SrLyce'

        if active:
            self.collector = PokerStarsCollector(self.name_room, active=True)
            self.parser = PokerStarsParser(self.name_room, self.hero_name, active=True)

        room_logger.debug("PokerStars Room initializated.")