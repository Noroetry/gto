from src.base.base_collector import BaseCollector
import os
import shutil
import logging
import filecmp

from config import settings

pokerstars_collector_logger = logging.getLogger(__name__)

class PokerStarsCollector(BaseCollector):
    def __init__(self, name_room: str, active: bool):
        source_dir = settings.POKERSTARS_HAND_HISTORY_PATH
        end_dir = os.path.join(settings.RAW_HAND_HISTORIES_DIR, name_room)

        super().__init__(source_dir, end_dir)
        pokerstars_collector_logger.info("PokerStars Collector initializated.")
        pokerstars_collector_logger.debug(f"Source path: {source_dir}")
        pokerstars_collector_logger.debug(f"Destiny path: {end_dir}")

        if active:
            self.collect_files()

    def checkDestinationFolder(self):
        pokerstars_collector_logger.info(f"Checking folder")
        os.makedirs(self.end_dir, exist_ok=True)
        pokerstars_collector_logger.info("Destination directory checked.")

    def collect_files(self):
        self.checkDestinationFolder()
        files_count = 0

        if not os.path.isdir(self.source_dir):
            pokerstars_collector_logger.critical(f"Source directory does not exist: {self.source_dir}")
            return 0

        try:
            all_files = os.listdir(self.source_dir)
            hand_history_files = [f for f in all_files if f.endswith('.txt')]

            if not hand_history_files:
                pokerstars_collector_logger.warning("There aren't files at source directory")
                return 0

            for filename in hand_history_files:
                source_path = os.path.join(self.source_dir, filename)
                end_path = os.path.join(self.end_dir, filename)

                if not os.path.exists(end_path):
                    try:
                        shutil.copy2(source_path, end_path)
                        files_count += 1
                        pokerstars_collector_logger.debug(f"File copied: {filename}")

                        os.remove(source_path)
                        pokerstars_collector_logger.debug(f"File deleted: {filename}")
                    except Exception as e:
                        pokerstars_collector_logger.critical(f"Error critical: {e}")
                else:
                    pokerstars_collector_logger.warning(f"File already exists at destination: {filename}")
                    try:
                        if filecmp.cmp(source_path, end_path, shallow=False):
                            os.remove(source_path)
                            pokerstars_collector_logger.debug(f"File deleted: {filename}")
                    except Exception as e:
                        pokerstars_collector_logger.critical(f"Error critical: {e}")
            
            pokerstars_collector_logger.debug(f"Recollect of Pokerstars Collected ended with success. Files copied: {files_count}")

        except Exception as e:
            pokerstars_collector_logger.critical(f"Unexpected error during collection: {e}")

        return files_count