from src.base.base_analyzer import BaseAnalyzer
from config import settings
import os
import logging
import json
from src.tables.preflop_ranges import preflop_ranges

pokerstars_analyzer_logger = logging.getLogger(__name__)

class PokerStarsAnalyzer(BaseAnalyzer):
    def __init__(self, name_room: str, active: bool):
        self.hero_name = settings.POKERSTARS_HERO_NAME
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
        pokerstars_analyzer_logger.info("Starting analysis of all formatted hands...")
        os.makedirs(self.analyzed_dir, exist_ok=True)

        all_results = []

        for filename in os.listdir(self.formatted_dir):
            if not filename.endswith('.json'):
                continue

            filepath = os.path.join(self.formatted_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                hand_data = json.load(f)
            pokerstars_analyzer_logger.debug(f"Analyzing hand: {filename}")
            result = self.analyze_hand(hand_data)
            if result:
                result["filename"] = filename
                pokerstars_analyzer_logger.debug(f"Result for {filename}: {result}")
                all_results.append(result)

        # Guardar todo en un único archivo
        result_path = os.path.join(self.analyzed_dir, "open_raises.json")
        with open(result_path, 'w', encoding='utf-8') as f_out:
            json.dump(all_results, f_out, ensure_ascii=False, indent=2)

        pokerstars_analyzer_logger.info(
            f"Se guardaron {len(all_results)} open raises en {result_path}"
        )
        self.export_or_results(result_path)


    def analyze_hand(self, hand_data: dict) -> dict:
        results = {}
        pokerstars_analyzer_logger.debug(f"Analyzing PREFLOP hand data: {hand_data}")
        preflop_result = self.analyze_preflop(hand_data)
        if preflop_result:
            results["preflop"] = preflop_result
        
        pokerstars_analyzer_logger.debug(f"Results for hand: {results}")

        return results if results else None


    def analyze_preflop(self, hand_data: dict) -> dict:
        hero = self.hero_name
        preflop_actions = hand_data.get("actions", {}).get("preflop", [])
        players = hand_data.get("players", [])

        hero_info = next((p for p in players if p["name"] == hero), None)
        if not hero_info:
            return None

        def normalize_hand(cards):
            if len(cards) != 2:
                return None
            rank_order = "23456789TJQKA"
            r1, s1 = cards[0][0], cards[0][1]
            r2, s2 = cards[1][0], cards[1][1]

            if rank_order.index(r1) < rank_order.index(r2):
                r1, s1, r2, s2 = r2, s2, r1, s1

            suited = "s" if s1 == s2 else "o"
            if r1 == r2:
                return r1 + r2
            else:
                return f"{r1}{r2}{suited}"

        for action in preflop_actions:
            if action["action"] in ("BET", "RAISE"):
                if action["player"] == hero:
                    hand_str = normalize_hand(hero_info.get("cards", []))
                    position = hero_info.get("position")
                    allowed_hands = preflop_ranges.get(position, set())

                    correct_open = hand_str in allowed_hands if hand_str else False

                    return {
                        "position": position,
                        "cards": hero_info.get("cards", []),
                        "hand_str": hand_str,
                        "bet_size_bb": action["amount"],
                        "correct_open": correct_open
                    }
                else:
                    return None

        return None
    
    def export_or_results(self, json_file, output_filename="OR_results.txt"):
        try:
            output_path = os.path.join(self.analyzed_dir, output_filename)

            with open(json_file, "r") as f:
                data = json.load(f)

            unique_errors = set()

            for item in data:
                preflop = item.get("preflop", {})
                
                if not preflop.get("correct_open", True):
                    position = preflop.get("position", "Unknown")
                    cards = preflop.get("hand_str", "xx")
                    bet_size = preflop.get("bet_size_bb", 0)
                    
                    error_tuple = (position, cards, bet_size)
                    
                    unique_errors.add(error_tuple)

            with open(output_path, "w") as f:
                for error in unique_errors:
                    position, cards, bet_size = error
                    
                    f.write(f"{position} {cards} {bet_size}bb\n")
        
        except FileNotFoundError:
            print(f"Error: El archivo JSON '{json_file}' no se encontró.")
        except json.JSONDecodeError:
            print(f"Error: No se pudo decodificar el JSON del archivo '{json_file}'.")
        except Exception as e:
            print(f"Ocurrió un error inesperado: {e}")

