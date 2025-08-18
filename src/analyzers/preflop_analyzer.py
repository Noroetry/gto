from src.base.base_analyzer import BaseAnalyzer
import os
import logging
import json
from config import settings
from collections import defaultdict
from datetime import datetime
from src.tables.preflop_ranges import preflop_ranges

preflop_analyzer_logger = logging.getLogger(__name__)

class PreflopAnalyzer(BaseAnalyzer):
    def __init__(self, analyzed_dir, formatted_dir, hero_name: str):
        self.analyzed_dir = analyzed_dir
        self.formatted_dir = formatted_dir
        self.hero_name = hero_name
        self.analyzed_dir_or = os.path.join(settings.ANALYZED_HANDS_DIR, "OR")
        os.makedirs(self.analyzed_dir_or, exist_ok=True)
        
        super().__init__(self.formatted_dir, self.analyzed_dir_or)
        preflop_analyzer_logger.debug("Preflop Analyzer initializated.")

    def analyze_hand(self, hand_data: dict) -> dict:
        results = {}
        preflop_analyzer_logger.debug(f"Analyzing PREFLOP hand data: {hand_data}")
        preflop_result = self.analyze_preflop(hand_data)
        if preflop_result:
            results["preflop"] = preflop_result
        
        preflop_analyzer_logger.debug(f"Results for hand: {results}")

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

        hero_hand_str = normalize_hand(hero_info.get("cards", []))
        hero_position = hero_info.get("position")
        date_played = hand_data.get("date_played", "")

        # El BB no tiene la oportunidad de hacer un open raise
        if hero_position == 'BB':
            return None

        # Encontrar la posición de hero en el orden de acciones
        hero_action_index = -1
        for i, action in enumerate(preflop_actions):
            if action["player"] == hero:
                hero_action_index = i
                break

        # Si hero no ha actuado, no hay nada que analizar
        if hero_action_index == -1:
            return None
            
        # Comprobar si hero es el primer jugador en enfrentar una acción (excluyendo ciegas y folds)
        previous_raises = False
        for i in range(hero_action_index):
            if preflop_actions[i]["action"] in ("RAISE", "BET"):
                previous_raises = True
                break
        
        # Si hubo un raise previo, el análisis no es de un open raise.
        if previous_raises:
            return None

        # Si no hubo raise previo, hero tuvo la oportunidad de hacer un OR.
        hero_action = preflop_actions[hero_action_index]
        
        allowed_hands = preflop_ranges.get(hero_position, set())
        
        # Caso 1: Hero hizo un Open Raise
        if hero_action["action"] in ("RAISE", "BET"):
            correct_open = hero_hand_str in allowed_hands if hero_hand_str else False
            return {
                "position": hero_position,
                "cards": hero_info.get("cards", []),
                "hand_str": hero_hand_str,
                "bet_size_bb": hero_action["amount"],
                "correct_open": correct_open,
                "date_played": date_played,
                "action_type": "OR_made", # Open Raise realizado
            }

        # Caso 2: Hero hizo un Fold cuando debió hacer un Open Raise
        if hero_action["action"] == "FOLD":
            if hero_hand_str in allowed_hands:
                return {
                    "position": hero_position,
                    "cards": hero_info.get("cards", []),
                    "hand_str": hero_hand_str,
                    "bet_size_bb": None,
                    "correct_open": False,
                    "date_played": date_played,
                    "action_type": "OR_missed", # Open Raise perdido
                }

        # En cualquier otro caso (call, check, etc.), no hay un error de OR.
        return None

    def generate_daily_or_reports(self):
        try:
            preflop_analyzer_logger.info("Generando informes de Open Raises por día y el informe general...")
            preflop_analyzer_logger.debug("Inicializando el proceso de generación de informes.")

            json_file = os.path.join(self.analyzed_dir_or, "open_raises.json")

            if not os.path.exists(json_file):
                preflop_analyzer_logger.critical(f"Error: El archivo JSON '{json_file}' no existe.")
                return

            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            reports_by_day = defaultdict(lambda: {
                "correct_opens": 0,
                "incorrect_opens": set(),
                "made_opens": 0,
                "missed_opens": 0
            })
            preflop_analyzer_logger.debug(f"Procesando {len(data)} jugadas en total.")

            total_correct_global = 0
            total_incorrect_global = 0
            total_made_global = 0
            total_missed_global = 0

            for item in data:
                preflop = item.get("preflop", {})
                date_played_str = preflop.get("date_played")

                if not date_played_str:
                    preflop_analyzer_logger.critical(f"Mano sin fecha encontrada. Saltando... Hand: {item.get('filename', 'Unknown')}")
                    continue

                try:
                    date_obj = datetime.strptime(date_played_str, "%d-%m-%Y %H:%M:%S")
                    formated_date = date_obj.strftime("%y%m%d")
                except ValueError:
                    preflop_analyzer_logger.error(f"Formato de fecha inválido para '{date_played_str}'. Saltando...")
                    continue
                
                action_type = preflop.get("action_type")
                correct_open = preflop.get("correct_open", False)

                if correct_open:
                    reports_by_day[formated_date]["correct_opens"] += 1
                    reports_by_day[formated_date]["made_opens"] += 1
                    total_correct_global += 1
                    total_made_global += 1
                else:
                    position = preflop.get("position", "Unknown")
                    hand_str = preflop.get("hand_str", "Xx")
                    
                    # Modificación clave: añadir el tipo de acción
                    if action_type == "OR_missed":
                        incorrect_play_string = f"{position} {hand_str} OR missed"
                        reports_by_day[formated_date]["missed_opens"] += 1
                        total_missed_global += 1
                    else: # OR_made con mano incorrecta
                        incorrect_play_string = f"{position} {hand_str} OR made"
                        reports_by_day[formated_date]["made_opens"] += 1
                        total_made_global += 1
                    
                    reports_by_day[formated_date]["incorrect_opens"].add(incorrect_play_string)
                    total_incorrect_global += 1
            
            preflop_analyzer_logger.debug(f"Reports sets for days: {reports_by_day}")

            # --- GENERACIÓN DEL INFORME DIARIO ---
            for date, report_data in reports_by_day.items():
                output_filename = f"{date} - OR.txt"
                output_file_path = os.path.join(self.analyzed_dir_or, output_filename)
                preflop_analyzer_logger.debug(f"Generando informe para la fecha: {date} en {output_file_path}")
                
                with open(output_file_path, "w", encoding="utf-8") as f:
                    f.write(f"Informe de Open Raises del día {date}\n")
                    f.write("=" * 40 + "\n\n")
                    
                    correct_count = report_data["correct_opens"]
                    incorrect_plays = report_data["incorrect_opens"]
                    incorrect_count = len(incorrect_plays)
                    made_count = report_data["made_opens"]
                    missed_count = report_data["missed_opens"]

                    total_plays = made_count + missed_count
                    
                    improvement_index = (
                        (correct_count / total_plays) * 100
                        if total_plays > 0
                        else 0
                    )

                    f.write(f"Total: {total_plays} jugadas\n")
                    f.write(f"Total de manos correctas: {correct_count}\n")
                    f.write(f"Total de manos incorrectas: {incorrect_count}\n")
                    f.write(f"Perfección: {improvement_index:.2f}%\n\n")
                    f.write(f"Total OR realizados: {made_count}\n")
                    f.write(f"Total OR perdidos: {missed_count}\n\n")

                    if incorrect_count > 0:
                        f.write("Detalles de las manos incorrectas:\n")
                        unique_incorrect_plays = sorted(list(incorrect_plays))
                        
                        for play_string in unique_incorrect_plays:
                            f.write(f"- {play_string}\n")

            # --- GENERACIÓN DEL INFORME GENERAL ---
            preflop_analyzer_logger.debug("Generando el informe general.")
            brief_report_filename = "OR - Brief.txt"
            brief_report_path = os.path.join(self.analyzed_dir_or, brief_report_filename)

            with open(brief_report_path, "w", encoding="utf-8") as f:
                total_plays_global = total_made_global + total_missed_global
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
                f.write(f"Total OR realizados: {total_made_global}\n")
                f.write(f"Total OR perdidos: {total_missed_global}\n")
            
            preflop_analyzer_logger.info("Informes de Open Raises generados correctamente.")
            preflop_analyzer_logger.debug(f"Informe general guardado en: {brief_report_path}")

        except FileNotFoundError:
            preflop_analyzer_logger.critical(f"Error: El archivo JSON '{json_file}' no se encontró.")
        except json.JSONDecodeError:
            preflop_analyzer_logger.critical(f"Error: No se pudo decodificar el JSON del archivo '{json_file}'.")
        except Exception as e:
            preflop_analyzer_logger.critical(f"Ocurrió un error inesperado: {e}")

    def analyze_all(self) -> None:
        preflop_analyzer_logger.info("Starting analysis of all formatted hands...")
    
        all_results = []

        for filename in os.listdir(self.formatted_dir):
            if not filename.endswith('.json'):
                continue

            filepath = os.path.join(self.formatted_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                hand_data = json.load(f)
            preflop_analyzer_logger.debug(f"Analyzing hand: {filename}")
            result = self.analyze_hand(hand_data)
            if result:
                result["filename"] = filename
                preflop_analyzer_logger.debug(f"Result for {filename}: {result}")
                all_results.append(result)

        # Guardar todo en un único archivo
        result_path = os.path.join(self.analyzed_dir_or, "open_raises.json")
        with open(result_path, 'w', encoding='utf-8') as f_out:
            json.dump(all_results, f_out, ensure_ascii=False, indent=2)

        preflop_analyzer_logger.info(
            f"Se guardaron {len(all_results)} open raises en {result_path}"
        )
        self.generate_daily_or_reports()