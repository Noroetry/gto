from src.base.base_analyzer import BaseAnalyzer
from config import settings
import os
import logging
import json

pokerstars_analyzer_logger = logging.getLogger(__name__)

class PokerStarsAnalyzer(BaseAnalyzer):
    def __init__(self, name_room: str, active: bool):
        self.source_dir = os.path.join(settings.PROCESSED_HAND_HISTORIES_DIR, name_room)
        self.formatted_dir = settings.FORMATTED_HANDS_DIR
        self.analyzed_dir = settings.ANALYZED_HANDS_DIR
        self.name_room = name_room

        super().__init__(self.source_dir, self.formatted_dir, self.analyzed_dir)
        pokerstars_analyzer_logger.debug("PokerStars Analyzer initializated.")
        pokerstars_analyzer_logger.debug(f"Source path: {self.source_dir}")
        pokerstars_analyzer_logger.debug(f"Formatted path: {self.formatted_dir}")
        pokerstars_analyzer_logger.debug(f"Analyzed path: {self.analyzed_dir}")

        if active:
            self.analyze_all()

    def analyze_all(self) -> None:
        os.makedirs(self.analyzed_dir, exist_ok=True)
        for filename in os.listdir(self.formatted_dir):
            if not filename.endswith('.json'):
                continue
            filepath = os.path.join(self.formatted_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                hand_data = json.load(f)
            # Aquí haces tu análisis avanzado y guardas resultados en analyzed_dir
            # Ejemplo:
            # result = self.analyze_hand(hand_data)
            # result_path = os.path.join(self.analyzed_dir, f"analyzed_{filename}")
            # with open(result_path, 'w', encoding='utf-8') as f_out:
            #     json.dump(result, f_out, ensure_ascii=False, indent=2)

    def analyze_hand(self, hand_data) -> dict:
        # Implementa aquí tu análisis avanzado sobre hand_data
        # Por ejemplo, calcular estadísticas, patrones, etc.
        # Devuelve un diccionario con los resultados del análisis
        return {}