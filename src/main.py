import os
import sys
import logging

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from config import settings
from src.utils.logger_config import setup_logging
from src.rooms.pokerstars_room import PokerStarsRoom

main_logger = logging.getLogger(__name__)

def main():
    setup_logging()
    main_logger.info("Inicio de aplicación")
    main_logger.debug("Inicio de debug")

    rooms = [ PokerStarsRoom() ]

    for room in rooms:
        main_logger.info(f"Procesando sala: {room.name_room}")

    main_logger.info("Fin de aplicación\n\n")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        main_logger.critical(f"An critical error has been on main: {e}", exc_info=True)
        sys.exit(1)