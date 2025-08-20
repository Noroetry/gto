from src.base.base_analyzer import BaseAnalyzer
import os
import logging
import json
from config import settings
from collections import defaultdict
from datetime import datetime

pot_analyzer_logger = logging.getLogger(__name__)

class PotAnalyzer(BaseAnalyzer):
    def __init__(self, analyzed_dir, formatted_dir, hero_name: str):
        self.analyzed_dir = analyzed_dir
        self.formatted_dir = formatted_dir
        self.hero_name = hero_name
        self.analyzed_dir_pot = os.path.join(settings.ANALYZED_HANDS_DIR, "POT")
        os.makedirs(self.analyzed_dir_pot, exist_ok=True)
        
        super().__init__(self.formatted_dir, self.analyzed_dir_pot)
        pot_analyzer_logger.debug("Pot Analyzer initializated.")

    def analyze_hand(self, hand_data: dict) -> dict:
        results = {}
        pot_analyzer_logger.debug(f"Analyzing POT hand data: {hand_data}")
        pot_result = self.analyze_pot(hand_data)
        if pot_result:
            results["pot"] = pot_result
        
        pot_analyzer_logger.debug(f"Results for hand: {results}")

        return results if results else None


    def analyze_pot(self, hand_data: dict) -> dict:

        hero_name = self.hero_name
    
        # Obtener las acciones preflop del hero
        hero_preflop_actions = [action for action in hand_data.get("actions", {}).get("preflop", []) if action.get("player") == hero_name]
        
        # Validar si el hero ha foldeado en preflop
        for action in hero_preflop_actions:
            if action.get("action") == "FOLD":
                pot_analyzer_logger.debug(f"Hero ({hero_name}) folded preflop. Skipping hand {hand_data.get('hand_id')}")
                return None
        
        # Obtener el stack final del héroe
        hero_position = None
        hero_final_stack = 0.0
        for player in hand_data.get("players", []):
            if player.get("name") == hero_name:
                hero_position = player.get("position")
                hero_final_stack = player.get("stack", 0.0)
                break

        # Calcular el dinero total invertido por el héroe en big blinds (pot_invested_bb)
        # Sumar las cantidades de todas las acciones del héroe, incluidas las ciegas
        pot_invested_bb = 0.0

        if hero_position == "BB":
            pot_invested_bb += 1.0
        elif hero_position == "SB":
            pot_invested_bb += 0.5

        streets = ["preflop", "flop", "turn", "river"]
        for street in streets:
            street_actions = hand_data.get("actions", {}).get(street, [])
            for action in street_actions:
                if action.get("player") == hero_name:
                    pot_invested_bb += action.get("amount", 0.0)
        
        # Calcular el stack inicial del héroe (pot_start_bb)
        # Se calcula sumando el stack final y el dinero invertido
        pot_start_bb = hero_final_stack + pot_invested_bb

        # Calcular el tamaño del bote final (win_amount ya está en BBs)
        pot_final_bb = hand_data.get("win_amount")
        
        # Determinar si el jugador (hero) ganó o perdió
        is_winner = hand_data.get("winner") == hero_name

        return {
            "hand_id": hand_data.get("hand_id"),
            "date_played": hand_data.get("date_played"),
            "pot_start_bb": round(pot_start_bb, 2),
            "pot_invested_bb": round(pot_invested_bb, 2),
            "pot_final_bb": round(pot_final_bb, 2),
            "is_winner": is_winner
        }

    def generate_daily_or_reports(self):
        try:
            pot_analyzer_logger.info("Generando informes de Pots por día y el informe general...")
            pot_analyzer_logger.debug("Inicializando el proceso de generación de informes.")

            json_file = os.path.join(self.analyzed_dir_pot, "pot.json")

            if not os.path.exists(json_file):
                pot_analyzer_logger.critical(f"Error: El archivo JSON '{json_file}' no existe.")
                return

            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            reports_by_day = defaultdict(lambda: {
                "total_pots": 0,
                "ganados": 0,
                "perdidos": 0,
                "ganancias": 0.0,
                "perdidas": 0.0
            })
            pot_analyzer_logger.debug(f"Procesando {len(data)} jugadas en total.")

            total_ganados_global = 0
            total_perdidos_global = 0
            total_ganancias_global = 0.0
            total_perdidas_global = 0.0
            total_pots_global = 0

            for item in data:
                pot = item.get("pot", {})
                date_played_str = pot.get("date_played")

                if not date_played_str:
                    pot_analyzer_logger.critical(f"Mano sin fecha encontrada. Saltando... Hand: {pot.get('hand_id', 'Unknown')}")
                    continue
                
                try:
                    date_obj = datetime.strptime(date_played_str, "%d-%m-%Y %H:%M:%S")
                    formated_date = date_obj.strftime("%y%m%d")
                except ValueError:
                    pot_analyzer_logger.error(f"Formato de fecha inválido para '{date_played_str}'. Saltando...")
                    continue
                
                total_pots_global += 1
                is_winner = pot.get("is_winner", False)
                pot_invested_bb = pot.get("pot_invested_bb", 0.0)

                reports_by_day[formated_date]["total_pots"] += 1
                
                if is_winner:
                    net_profit = pot.get("pot_final_bb", 0.0) - pot_invested_bb
                    reports_by_day[formated_date]["ganados"] += 1
                    reports_by_day[formated_date]["ganancias"] += net_profit
                    
                    total_ganados_global += 1
                    total_ganancias_global += net_profit
                else:
                    reports_by_day[formated_date]["perdidos"] += 1
                    reports_by_day[formated_date]["perdidas"] += pot_invested_bb
                    
                    total_perdidos_global += 1
                    total_perdidas_global += pot_invested_bb

            # --- GENERACIÓN DEL INFORME DIARIO ---
            for date, report_data in reports_by_day.items():
                output_filename = f"{date} - POT.txt"
                output_file_path = os.path.join(self.analyzed_dir_pot, output_filename)
                pot_analyzer_logger.debug(f"Generando informe para la fecha: {date} en {output_file_path}")
                
                with open(output_file_path, "w", encoding="utf-8") as f:
                    f.write(f"Informe de Pots jugados del día {date}\n")
                    f.write("=" * 40 + "\n\n")
                    
                    ganancias = round(report_data["ganancias"], 2)
                    perdidas = round(report_data["perdidas"], 2)
                    diferencia = round(ganancias - perdidas, 2)
                    
                    f.write(f"Total: {report_data['total_pots']} pots jugados\n")
                    f.write(f"Ganados: {report_data['ganados']}\n")
                    f.write(f"Perdidos: {report_data['perdidos']}\n")
                    f.write(f"Ganancias: {ganancias}\n")
                    f.write(f"Pérdidas: {perdidas}\n")
                    f.write(f"Diferencia: {diferencia}\n")

            # --- GENERACIÓN DEL INFORME GENERAL ---
            pot_analyzer_logger.debug("Generando el informe general.")
            brief_report_filename = "POT - Brief.txt"
            brief_report_path = os.path.join(self.analyzed_dir_pot, brief_report_filename)

            with open(brief_report_path, "w", encoding="utf-8") as f:
                diferencia_global = round(total_ganancias_global - total_perdidas_global, 2)
                
                f.write("--- Resumen General de Pots jugados ---\n")
                f.write("=" * 40 + "\n")
                
                f.write(f"Total: {total_pots_global} pots jugados\n")
                f.write(f"Ganados: {total_ganados_global}\n")
                f.write(f"Perdidos: {total_perdidos_global}\n")
                f.write(f"Ganancias: {round(total_ganancias_global, 2)}\n")
                f.write(f"Pérdidas: {round(total_perdidas_global, 2)}\n")
                f.write(f"Diferencia: {diferencia_global}\n")
            
            pot_analyzer_logger.info("Informes de Pots generados correctamente.")
            pot_analyzer_logger.debug(f"Informe general guardado en: {brief_report_path}")

        except FileNotFoundError:
            pot_analyzer_logger.critical(f"Error: El archivo JSON '{json_file}' no se encontró.")
        except json.JSONDecodeError:
            pot_analyzer_logger.critical(f"Error: No se pudo decodificar el JSON del archivo '{json_file}'.")
        except Exception as e:
            pot_analyzer_logger.critical(f"Ocurrió un error inesperado: {e}")

    def analyze_all(self) -> None:
        pot_analyzer_logger.info("Starting analysis of all formatted hands...")

        all_results = []

        for filename in os.listdir(self.formatted_dir):
            if not filename.endswith('.json'):
                continue

            filepath = os.path.join(self.formatted_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                hand_data = json.load(f)
            pot_analyzer_logger.debug(f"Analyzing hand: {filename}")
            result = self.analyze_hand(hand_data)
            if result:
                result["filename"] = filename
                pot_analyzer_logger.debug(f"Result for {filename}: {result}")
                all_results.append(result)

        # Guardar todo en un único archivo
        result_path = os.path.join(self.analyzed_dir_pot, "pot.json")
        with open(result_path, 'w', encoding='utf-8') as f_out:
            json.dump(all_results, f_out, ensure_ascii=False, indent=2)

        pot_analyzer_logger.info(
            f"Se guardaron {len(all_results)} open raises en {result_path}"
        )
        self.generate_daily_or_reports()