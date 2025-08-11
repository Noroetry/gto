from src.base.base_parser import BaseParser
import os
import shutil
import logging
import re
from config import settings
from src.models.hand_model import StandardHand
from src.models.hand_model_2 import StandardHandTest

pokerstars_parser_logger = logging.getLogger(__name__)

class PokerStarsParser(BaseParser):
    def __init__(self, name_room: str, active: bool):
        self.name_room = name_room
        self.source_dir = os.path.join(settings.RAW_HAND_HISTORIES_DIR, name_room)
        self.processed_dir = os.path.join(settings.PROCESSED_HAND_HISTORIES_DIR, name_room)
        self.formatted_dir = settings.FORMATTED_HANDS_DIR

        super().__init__(self.source_dir, self.processed_dir, self.formatted_dir)

        pokerstars_parser_logger.info("PokerStars Parser Initializated")
        pokerstars_parser_logger.debug(f"Source path: {self.source_dir}")
        pokerstars_parser_logger.debug(f"Destiny path: {self.processed_dir}")
        pokerstars_parser_logger.debug(f"Formatted path: {self.formatted_dir}")

        if active:
            self.parse_files()
            self.convert_all_to_json()

    def check_dir(self) -> bool:
        pokerstars_parser_logger.debug("Checking source folder...")
        if not os.path.isdir(self.source_dir):
            pokerstars_parser_logger.critical("The source folder doesnt exists. Aborting...")
            return False

        # Comprobar y crear la carpeta de destino si no existe
        if not os.path.isdir(self.processed_dir):
            pokerstars_parser_logger.warning(f"The destination folder {self.processed_dir} does not exist. Creating it...")
            try:
                os.makedirs(self.processed_dir, exist_ok=True)
                pokerstars_parser_logger.info(f"Destination folder {self.processed_dir} created.")
            except Exception as e:
                pokerstars_parser_logger.critical(f"Could not create destination folder: {e}")
                return False

        return True
    
    def format_file(self, filename: str):
        filepath = os.path.join(self.source_dir, filename)
        pokerstars_parser_logger.debug(f"Processing file: {filename}")
        if not os.path.isfile(filepath):
            pokerstars_parser_logger.warning(f"File {filename} is not a file. Skipping...")
            return
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()

            content = content.replace('\u00A0', ' ').replace('\xa0', ' ')

            hands = [h.strip() for h in re.split(r'\n{2,}', content) if h.strip()]

            pokerstars_parser_logger.debug(f"Found {len(hands)} hands in file {filename}")

            for idx, hand in enumerate(hands):
                match = re.search(r'Mano n\.º (\d+)', hand)
                if match:
                    hand_id = match.group(1)
                    pokerstars_parser_logger.debug(f"Found hand ID: {hand_id} in file {filename}")
                    processed_file_path = os.path.join(self.processed_dir, f"{hand_id}.txt")
                    
                    if os.path.exists(processed_file_path):
                        with open(processed_file_path, 'r', encoding='utf-8') as existing_file:
                            existing_content = existing_file.read()
                        if existing_content == hand:
                            pokerstars_parser_logger.warning(f"Hand {hand_id} already exists and is identical. Skipping.")
                            continue
                        else:
                            pokerstars_parser_logger.critical(
                                f"Hand {hand_id} already exists but content differs! Ignoring..."
                            )
                            continue
                    
                    with open(processed_file_path, 'w', encoding='utf-8') as processed_file:
                        processed_file.write(hand)
                    pokerstars_parser_logger.debug(f"Processed hand {hand_id} and saved to {processed_file_path}")
                else:
                    pokerstars_parser_logger.error(
                        f"No valid hand ID found in file {filename} at hand #{idx+1}: {hand[:60]}..."
                    )

            # Guardar backup del fichero crudo
            backup_dir = os.path.join(self.source_dir, "backup")
            os.makedirs(backup_dir, exist_ok=True)
            backup_path = os.path.join(backup_dir, filename)
            shutil.copy2(filepath, backup_path)
            pokerstars_parser_logger.debug(f"Backup of {filename} saved to {backup_path}")

            # Eliminar el fichero original del origen
            os.remove(filepath)
            pokerstars_parser_logger.debug(f"Original file {filename} deleted from source directory")

        except Exception as e:
            pokerstars_parser_logger.error(f"Error processing file {filename}: {e}")
            return        

    def parse_files(self):
        pokerstars_parser_logger.debug(f"Starting parser function of {self.name_room}")
        if not self.check_dir():
            return
        
        for filename in os.listdir(self.source_dir):
            filepath = os.path.join(self.source_dir, filename)
            if not os.path.isfile(filepath):
                continue  # Ignora carpetas como 'backup'
            self.format_file(filename)

        return
    
    def format_hand(self, hand_text: str) -> StandardHand:
        pokerstars_parser_logger.debug(f"Primeras líneas de la mano:\n{hand_text[:200]}")

        # 1. Extraer cabecera (ID, tipo, fecha, SB, BB, Zoom/normal)
        header_match = re.search(
            r"Mano n\.º (\d+) de (?:Zoom de )?PokerStars:  Hold'em No Limit \(([\d\.,]+)[^\d]+\/([\d\.,]+)[^\d]+\).* - ([\d\- :]+) CET",
            hand_text
        )
        if not header_match:
            if re.search(r"Torneo n\.º \d+", hand_text):
                pokerstars_parser_logger.warning("Mano de torneo detectada. Se omite.")
            else:
                pokerstars_parser_logger.critical("No se pudo extraer la cabecera de la mano.")
            return None

        hand_id = header_match.group(1)
        is_zoom = "Zoom de" in hand_text.splitlines()[0]
        sb = float(header_match.group(2).replace(',', '.'))
        bb = float(header_match.group(3).replace(',', '.'))
        date = header_match.group(4)
        game_type = "zoom" if is_zoom else "holdem"

        pokerstars_parser_logger.debug(f"Cabecera extraída: hand_id={hand_id}, is_zoom={is_zoom}, sb={sb}, bb={bb}, date={date}, game_type={game_type}")

        # 2. Extraer mesa, tamaño y botón
        table_match = re.search(r'Mesa "([^"]+)" (\d+)-max El asiento n\.º (\d+) es el botón', hand_text)
        table = table_match.group(1) if table_match else ""
        size_table = int(table_match.group(2)) if table_match else None
        button_seat = int(table_match.group(3)) if table_match else None

        pokerstars_parser_logger.debug(f"Mesa: {table}, Tamaño: {size_table}-max, Botón en asiento: {button_seat}")


        # 3. Extraer jugadores y stacks (en BB)
        stacks = {}
        seat_to_player = {}
        for m in re.finditer(r"Asiento (\d+): ([^\(]+)\(([\d\.,]+)[^\d]+en fichas\)", hand_text):
            seat = int(m.group(1))
            player = m.group(2).strip()
            stack_eur = float(m.group(3).replace(',', '.'))
            stack_bb = round(stack_eur / bb, 2) if bb > 0 else 0
            stacks[player] = stack_bb
            seat_to_player[seat] = player
        pokerstars_parser_logger.debug(f"Stacks (en BB): {stacks}")

        # 4. Extraer héroe y cartas
        hero_match = re.search(r"Repartidas a ([^\[]+) \[([^\]]+)\]", hand_text)
        hero = hero_match.group(1).strip() if hero_match else ""
        hero_cards = hero_match.group(2).split() if hero_match else []
        pokerstars_parser_logger.debug(f"Héroe: {hero}, Cartas: {hero_cards}")

        # 5. Extraer acciones por calles
        actions = {"preflop": [], "flop": [], "turn": [], "river": []}
        street_splits = re.split(r"(\*\*\* [A-ZÁÉÍÓÚÑ ]+ \*\*\*)", hand_text)
        current_street = "preflop"
        for part in street_splits:
            if "*** FLOP ***" in part:
                current_street = "flop"
            elif "*** TURN ***" in part:
                current_street = "turn"
            elif "*** RIVER ***" in part:
                current_street = "river"
            elif "*** CARTAS DE MANO ***" in part:
                current_street = "preflop"
            else:
                for line in part.splitlines():
                    if ":" in line:
                        actions[current_street].append(line.strip())
        # Elimina la primera línea de preflop si es la cabecera
        if actions["preflop"] and actions["preflop"][0].startswith("Mano n.º"):
            actions["preflop"].pop(0)
        pokerstars_parser_logger.debug(f"Acciones extraídas: {actions}")

        # 6. Extraer board
        board = []
        board_match = re.search(r"\*\*\* FLOP \*\*\* \[([^\]]+)\]", hand_text)
        if board_match:
            board += board_match.group(1).split()
        turn_match = re.search(r"\*\*\* TURN \*\*\* \[[^\]]+\] \[([^\]]+)\]", hand_text)
        if turn_match:
            board.append(turn_match.group(1))
        river_match = re.search(r"\*\*\* RIVER \*\*\* \[[^\]]+\] \[([^\]]+)\]", hand_text)
        if river_match:
            board.append(river_match.group(1))
        pokerstars_parser_logger.debug(f"Board: {board}")

        # 7. Extraer ganador y cantidad ganada (en BB)
        winner = None
        win_amount = 0.0
        win_match = re.search(r"([^\s]+) se lleva ([\d\.,]+)[^\d]+del bote", hand_text)
        if win_match:
            winner = win_match.group(1)
            win_eur = float(win_match.group(2).replace(',', '.'))
            win_amount = round(win_eur / bb, 2) if bb > 0 else 0.0
        pokerstars_parser_logger.debug(f"Ganador: {winner}, Ganancia (BB): {win_amount}")

        # 8. Extraer comisión/rake (en BB)
        rake = 0.0
        rake_match = re.search(r"Comisión ([\d\.,]+)[^\d]+", hand_text)
        if rake_match:
            rake_eur = float(rake_match.group(1).replace(',', '.'))
            rake = round(rake_eur / bb, 2) if bb > 0 else 0.0
        pokerstars_parser_logger.debug(f"Rake (BB): {rake}")

        # 9. Crear objeto StandardHand
        hand = StandardHandTest(
            hand_id=hand_id,
            date=date,
            table=table,
            size_table=size_table,
            game_type=game_type,
            hero=hero,
            hero_position="",  # TODO: calcular posición real
            hero_cards=hero_cards,
            stacks=stacks,
            actions=actions,
            board=board,
            winner=winner,
            win_amount=win_amount,  # Solo en BB
            sb=sb,
            bb=bb,
            rake=rake,
            raw_text=hand_text
        )
        pokerstars_parser_logger.debug(f"Objeto StandardHand creado: {hand}")
        return hand

    def convert_all_to_json(self):
        os.makedirs(settings.FORMATTED_HANDS_DIR, exist_ok=True)
        for filename in os.listdir(self.processed_dir):
            filepath = os.path.join(self.processed_dir, filename)
            if not os.path.isfile(filepath):
                continue
            with open(filepath, 'r', encoding='utf-8') as f:
                hand_text = f.read()
            hand = self.format_hand(hand_text)
            if not hand:
                continue
            json_filename = f"pokerstars_{hand.hand_id}.json"
            json_path = os.path.join(settings.FORMATTED_HANDS_DIR, json_filename)
            if os.path.exists(json_path):
                pokerstars_parser_logger.warning(f"Mano {hand.hand_id} ya existe en formatted_hands. Se omite.")
                continue
            with open(json_path, 'w', encoding='utf-8') as f_json:
                import json
                json.dump(hand.__dict__, f_json, ensure_ascii=False, indent=2)
            pokerstars_parser_logger.debug(f"Mano {hand.hand_id} convertida a JSON y guardada en formatted_hands.")

            # Guardar backup del fichero processed
            backup_dir = os.path.join(self.processed_dir, "backup")
            os.makedirs(backup_dir, exist_ok=True)
            backup_path = os.path.join(backup_dir, filename)
            shutil.copy2(filepath, backup_path)
            pokerstars_parser_logger.debug(f"Backup of {filename} saved to {backup_path}")

            # Eliminar el fichero original del origen
            os.remove(filepath)
            pokerstars_parser_logger.debug(f"Original file {filename} deleted from source directory")