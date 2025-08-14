from src.base.base_analyzer import BaseAnalyzer
from config import settings
import os
import logging
import json
from src.tables.preflop_ranges import preflop_ranges
from collections import defaultdict
from datetime import datetime

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
        result_path_dir = os.path.join(self.analyzed_dir, "OR")
        pokerstars_analyzer_logger.debug("Checking if result OR directory exists...")
        os.makedirs(result_path_dir, exist_ok=True)
        result_path = os.path.join(result_path_dir, "open_raises.json")
        with open(result_path, 'w', encoding='utf-8') as f_out:
            json.dump(all_results, f_out, ensure_ascii=False, indent=2)

        pokerstars_analyzer_logger.info(
            f"Se guardaron {len(all_results)} open raises en {result_path}"
        )
        self.generate_daily_or_reports()


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
                    if position == 'BB':
                        return None  # No se analiza el BB
                    date_played = hand_data.get("date_played", "")
                    allowed_hands = preflop_ranges.get(position, set())

                    correct_open = hand_str in allowed_hands if hand_str else False

                    return {
                        "position": position,
                        "cards": hero_info.get("cards", []),
                        "hand_str": hand_str,
                        "bet_size_bb": action["amount"],
                        "correct_open": correct_open,
                        "date_played": date_played,
                    }
                else:
                    return None

        return None

    def generate_daily_or_reports(self):
        try:
            pokerstars_analyzer_logger.info("Generando informes de Open Raises por día y el informe general...")
            pokerstars_analyzer_logger.debug("Inicializando el proceso de generación de informes.")

            path_or_results = os.path.join(self.analyzed_dir, "OR")
            json_file = os.path.join(path_or_results, "open_raises.json")

            if not os.path.exists(json_file):
                pokerstars_analyzer_logger.critical(f"Error: El archivo JSON '{json_file}' no existe.")
                return

            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            reports_by_day = defaultdict(lambda: {
                "correct_opens": 0,
                "incorrect_opens": set()
            })
            pokerstars_analyzer_logger.debug(f"Procesando {len(data)} jugadas en total.")

            total_correct_global = 0
            total_incorrect_global = 0

            for item in data:
                preflop = item.get("preflop", {})
                date_played_str = preflop.get("date_played")

                if not date_played_str:
                    pokerstars_analyzer_logger.critical(f"Mano sin fecha encontrada. Saltando... Hand: {item.get('filename', 'Unknown')}")
                    continue

                try:
                    date_obj = datetime.strptime(date_played_str, "%d-%m-%Y %H:%M:%S")
                    formated_date = date_obj.strftime("%y%m%d")
                except ValueError:
                    pokerstars_analyzer_logger.error(f"Formato de fecha inválido para '{date_played_str}'. Saltando...")
                    continue

                correct_open = preflop.get("correct_open", False)

                if correct_open:
                    reports_by_day[formated_date]["correct_opens"] += 1
                    total_correct_global += 1
                else:
                    position = preflop.get("position", "Unknown")
                    hand_str = preflop.get("hand_str", "Xx")
                    incorrect_play_string = f"{position} {hand_str}"
                    reports_by_day[formated_date]["incorrect_opens"].add(incorrect_play_string)
                    total_incorrect_global += 1
            
            pokerstars_analyzer_logger.debug(f"Reports sets for days: {reports_by_day}")

            for date, report_data in reports_by_day.items():
                output_filename = f"{date} - OR.txt"
                output_file_path = os.path.join(path_or_results, output_filename)
                pokerstars_analyzer_logger.debug(f"Generando informe para la fecha: {date} en {output_file_path}")
                
                with open(output_file_path, "w", encoding="utf-8") as f:
                    f.write(f"Informe de Open Raises del día {date}\n")
                    f.write("=" * 40 + "\n\n")
                    
                    correct_count = report_data["correct_opens"]
                    incorrect_plays = report_data["incorrect_opens"]
                    incorrect_count = len(incorrect_plays)

                    improvement_index = (
                        (correct_count / (correct_count + incorrect_count)) * 100
                        if (correct_count + incorrect_count) > 0
                        else 0
                    )

                    f.write(f"Total: {correct_count + incorrect_count} jugadas\n")
                    f.write(f"Total de manos correctas: {correct_count}\n")
                    f.write(f"Total de manos incorrectas: {incorrect_count}\n")
                    f.write(f"Perfección: {improvement_index:.2f}%\n\n")

                    if incorrect_count > 0:
                        f.write("Detalles de las manos incorrectas:\n")
                        unique_incorrect_plays = sorted(list(incorrect_plays))
                        
                        for play_string in unique_incorrect_plays:
                            f.write(f"- {play_string}\n")

            # --- GENERACIÓN DEL INFORME GENERAL ---
            pokerstars_analyzer_logger.debug("Generando el informe general.")
            brief_report_filename = "OR - Brief.txt"
            brief_report_path = os.path.join(path_or_results, brief_report_filename)

            with open(brief_report_path, "w", encoding="utf-8") as f:
                total_plays_global = total_correct_global + total_incorrect_global
                improvement_index_total = (
                    (total_correct_global / total_plays_global) * 100
                    if total_plays_global > 0
                    else 0
                )

                f.write("--- Resumen General de Open Raises ---\n")
                f.write("=" * 40 + "\n")
                
                f.write(f"Total: {total_plays_global} jugadas\n")
                f.write(f"Correctas: {total_correct_global}\n")
                f.write(f"Incorrectas: {total_incorrect_global}\n")
                f.write(f"Perfección: {improvement_index_total:.2f}%\n")
            
            pokerstars_analyzer_logger.info("Informes de Open Raises generados correctamente.")
            pokerstars_analyzer_logger.debug(f"Informe general guardado en: {brief_report_path}")

        except FileNotFoundError:
            pokerstars_analyzer_logger.critical(f"Error: El archivo JSON '{json_file}' no se encontró.")
        except json.JSONDecodeError:
            pokerstars_analyzer_logger.critical(f"Error: No se pudo decodificar el JSON del archivo '{json_file}'.")
        except Exception as e:
            pokerstars_analyzer_logger.critical(f"Ocurrió un error inesperado: {e}")

