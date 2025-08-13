from src.base.base_parser import BaseParser
import os
import shutil
import logging
import re
from config import settings
from src.models.hand_model import StandardHand
from typing import Optional, List, Dict, Any

pokerstars_parser_logger = logging.getLogger(__name__)

class PokerStarsParser(BaseParser):
    def __init__(self, name_room: str, active: bool):
        self.hero_name = settings.POKERSTARS_HERO_NAME
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
    
    def assign_remaining_positions(self, button_seat: Optional[int] = None, overwrite: bool = False, table_size: int = 6, players: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        positions_map = {
            2: ["BTN/SB", "BB"],
            3: ["BTN", "SB", "BB"],
            4: ["BTN", "SB", "BB", "CO"],
            5: ["BTN", "SB", "BB", "UTG", "CO"],
            6: ["BTN", "SB", "BB", "UTG", "MP", "CO"],
            7: ["BTN", "SB", "BB", "UTG", "MP", "HJ", "CO"],
            8: ["BTN", "SB", "BB", "EP1", "EP2", "MP", "HJ", "CO"],
            9: ["BTN", "SB", "BB", "EP1", "EP2", "MP1", "MP2", "HJ", "CO"]
        }

        # Filtrar jugadores activos con seat válido
        active_players = [p for p in players if p.get("active", True) and p.get("seat") is not None]
        num_active = len(active_players)
        if num_active < 2:
            return  players

        positions_order = positions_map.get(num_active, positions_map[9])

        # 1) Buscar BTN ya marcado por el parser
        btn_player = next((p for p in active_players if p.get("position") in ("BTN", "BTN/SB")), None)

        # 2) Si no hay BTN pero el caller pasa button_seat, usarlo
        if btn_player is None and button_seat is not None:
            btn_player = next((p for p in active_players if p.get("seat") == button_seat), None)

        if btn_player is None:
            # No podemos determinar botón, salimos sin tocar nada.
            return players

        btn_seat = btn_player["seat"]

        # 3) Construir la lista de asientos activos en orden horario empezando por BTN,
        #    usando table_size para wrap-around.
        seats_order = []
        seat = btn_seat
        while len(seats_order) < num_active:
            found = next((p for p in active_players if p["seat"] == seat), None)
            if found:
                seats_order.append(seat)
            # incrementar con wrap-around
            seat = seat + 1 if seat < table_size else 1

        # 4) Asignar posiciones en el mismo orden (zipping)
        for seat_val, pos in zip(seats_order, positions_order):
            p = next((pl for pl in players if pl.get("seat") == seat_val and pl.get("active", True)), None)
            if not p:
                continue
            current = p.get("position")
            if overwrite or current in (None, ""):
                p["position"] = pos
            else:
                # si ya tiene posición distinta y no queremos sobreescribir, la dejamos.
                # podrías loggear una advertencia aquí si te interesa detectar inconsistencias.
                pass
        return players


    def format_hand(self, hand_text: str, filename: str) -> StandardHand:
        pokerstars_parser_logger.debug(f"Primeras líneas de la mano:\n{hand_text[:200]}")

        # 1. Extraer cabecera (ID, tipo, fecha, SB, BB, Zoom/normal)
        header_match = re.search(
            r"Mano n\.º (\d+) de (?:Zoom de )?PokerStars:  Hold'em No Limit \(([\d\.,]+)[^\d]+\/([\d\.,]+)[^\d]+\).* - ([\d\- :]+) CET",
            hand_text
        )
        if not header_match:
            if re.search(r"Torneo n\.º \d+", hand_text):
                pokerstars_parser_logger.debug("Mano de torneo detectada. Se omite.")
                # Guardamos mano en carpeta tournament por el momento
                tournament_dir = os.path.join(self.processed_dir, "tournament")
                filepath = os.path.join(self.processed_dir, filename)
                os.makedirs(tournament_dir, exist_ok=True)
                backup_path = os.path.join(tournament_dir, filename)
                shutil.copy2(filepath, backup_path)
                pokerstars_parser_logger.debug(f"Backup of {filename} saved to {backup_path}")

                # Eliminar el fichero original del origen
                os.remove(filepath)
                pokerstars_parser_logger.debug(f"Original file {filename} deleted from source directory")
            else:
                pokerstars_parser_logger.critical("No se pudo extraer la cabecera de la mano.")
            return None

        hand_id = header_match.group(1)
        is_zoom = "Zoom de" in hand_text.splitlines()[0]
        sb = float(header_match.group(2).replace(',', '.'))
        bb = float(header_match.group(3).replace(',', '.'))
        date_played = header_match.group(4)
        game_type = "zoom" if is_zoom else "holdem"

        pokerstars_parser_logger.debug(f"Cabecera extraída: hand_id={hand_id}, is_zoom={is_zoom}, sb={sb}, bb={bb}, date={date_played}, game_type={game_type}")

        # 2. Extraer mesa, tamaño y botón
        table_match = re.search(r'Mesa "([^"]+)" (\d+)-max El asiento n\.º (\d+) es el botón', hand_text)
        table_name = table_match.group(1) if table_match else ""
        table_size = int(table_match.group(2)) if table_match else None
        button_seat = int(table_match.group(3)) if table_match else None

        pokerstars_parser_logger.debug(f"Mesa: {table_name}, Tamaño: {table_size}-max, Botón en asiento: {button_seat}")

        players = []
        for m in re.finditer(r"Asiento (\d+): ([^\(]+)\(([\d\.,]+)[^\d]+en fichas\)( está ausente)?", hand_text):
            seat = int(m.group(1))
            player_name = m.group(2).strip()
            stack_eur = float(m.group(3).replace(',', '.'))
            stack_bb = round(stack_eur / bb, 2) if bb > 0 else 0
            is_active = m.group(4) is None  # Si hay "está ausente", estará en group(4)
            if seat == button_seat:
                position = "BTN"
            else:
                position = None
            players.append({
                "name": player_name,
                "stack": stack_bb,
                "seat": seat,
                "position": position,  # Se asignará después si corresponde
                "cards": [],
                "active": is_active
            })

        # 3. Detectar jugadores que se han ido
        out_patterns = [
            r"^([^\:]+) deja la mesa",
            r"^([^\:]+) ha agotado su tiempo mientras siga sin conexión",
            r"^([^\:]+): está ausente$"
        ]

        for pattern in out_patterns:
            for m in re.finditer(pattern, hand_text, flags=re.MULTILINE):
                out_player = m.group(1).strip()
                players = [p for p in players if p["name"] != out_player]

        # 4. Detectar posiciones SB y BB
        for m in re.finditer(r"^(.+?): pone la ciega pequeña", hand_text, flags=re.MULTILINE):
            sb_player = m.group(1).strip()
            for p in players:
                if p["name"] == sb_player:
                    p["position"] = "SB"

        for m in re.finditer(r"^(.+?): pone la ciega grande", hand_text, flags=re.MULTILINE):
            bb_player = m.group(1).strip()
            for p in players:
                if p["name"] == bb_player:
                    p["position"] = "BB"

        # 5. Asignar posiciones a los jugadores restantes
        players = self.assign_remaining_positions(button_seat=button_seat, overwrite=True, table_size=table_size, players=players)
        pokerstars_parser_logger.debug(f"Players finales de mano: {players}")
        
        # 6. Extraer hero info
        hero_in_hand = False
        for p in players:
            if p["name"] == self.hero_name and p.get("active", False):
                hero_in_hand = True
                break

        if not hero_in_hand:
            pokerstars_parser_logger.warning(f"Hero {self.hero_name} not found in hand {hand_id}. Skipping.")
            return None

        match_hero_cards = re.search(rf"Repartidas a {re.escape(self.hero_name)} \[([2-9TJQKA][cdhs])\s+([2-9TJQKA][cdhs])\]", hand_text)
        hero_cards = []
        if match_hero_cards:
            hero_cards = [match_hero_cards.group(1), match_hero_cards.group(2)]
        else:
            pokerstars_parser_logger.warning(f"Hero cards not found for {self.hero_name} in hand {hand_id}. Skipping.")
            return None
        
        for p in players:
            if p["name"] == self.hero_name:
                p["cards"] = hero_cards
                pokerstars_parser_logger.debug(f"Hero cards: {p["cards"]}")
                break

        # 7. Extraer acciones por calles (lectura secuencial)
        actions = {"preflop": [], "flop": [], "turn": [], "river": []}
        current_street = None

        re_fold = re.compile(r"^(.+?): se retira")
        re_check = re.compile(r"^(.+?): pasa")
        re_call = re.compile(r"^(.+?): iguala ([\d\.,]+) €")
        re_bet = re.compile(r"^(.+?): apuesta ([\d\.,]+) €")
        re_raise = re.compile(r"^(.+?): sube .* a ([\d\.,]+) €")

        def update_player(name, action_type, amount_bb):
            """Actualiza el estado de un jugador en la lista players."""
            for p in players:
                if p["name"] == name:
                    if action_type == "FOLD":
                        p["active"] = False
                    elif action_type in ("CALL", "BET", "RAISE"):
                        p["stack"] = round(p["stack"] - amount_bb, 2)
                    # CHECK no cambia nada
                    break

        for raw_line in hand_text.splitlines():
            line = raw_line.strip()

            # Detectar calles
            if line.startswith("*** CARTAS DE MANO ***"):
                current_street = "preflop"
                continue
            elif line.startswith("*** FLOP ***"):
                current_street = "flop"
                continue
            elif line.startswith("*** TURN ***"):
                current_street = "turn"
                continue
            elif line.startswith("*** RIVER ***"):
                current_street = "river"
                continue
            elif line.startswith("*** SHOW DOWN ***") or line.startswith("*** RESUMEN ***"):
                break

            # Filtrar líneas irrelevantes
            if not current_street:
                continue
            if line.startswith("Repartidas a "):
                continue
            if "se une a la mesa" in line or "deja la mesa" in line:
                continue
            if ":" not in line:
                continue

            # FOLD
            m = re_fold.match(line)
            if m:
                player = m.group(1).strip()
                actions[current_street].append({
                    "player": player,
                    "action": "FOLD",
                    "amount": 0.0
                })
                update_player(player, "FOLD", 0.0)
                continue

            # CHECK
            m = re_check.match(line)
            if m:
                player = m.group(1).strip()
                actions[current_street].append({
                    "player": player,
                    "action": "CHECK",
                    "amount": 0.0
                })
                update_player(player, "CHECK", 0.0)
                continue

            # CALL
            m = re_call.match(line)
            if m:
                player = m.group(1).strip()
                amount_eur = float(m.group(2).replace(',', '.'))
                amount_bb = round(amount_eur / bb, 2)
                actions[current_street].append({
                    "player": player,
                    "action": "CALL",
                    "amount": amount_bb
                })
                update_player(player, "CALL", amount_bb)
                continue

            # BET
            m = re_bet.match(line)
            if m:
                player = m.group(1).strip()
                amount_eur = float(m.group(2).replace(',', '.'))
                amount_bb = round(amount_eur / bb, 2)
                actions[current_street].append({
                    "player": player,
                    "action": "BET",
                    "amount": amount_bb
                })
                update_player(player, "BET", amount_bb)
                continue

            # RAISE
            m = re_raise.match(line)
            if m:
                player = m.group(1).strip()
                amount_eur = float(m.group(2).replace(',', '.'))
                amount_bb = round(amount_eur / bb, 2)
                actions[current_street].append({
                    "player": player,
                    "action": "RAISE",
                    "amount": amount_bb
                })
                update_player(player, "RAISE", amount_bb)
                continue

        pokerstars_parser_logger.debug(f"Acciones extraídas: {actions}")
        pokerstars_parser_logger.debug(f"Estado final jugadores: {players}")

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
        hand = StandardHand(
            hand_id=hand_id,
            game_type=game_type,
            sb=sb,
            bb=bb,
            date_played=date_played,
            table_name=table_name,
            table_size=table_size,
            players=players,
            actions=actions,
            board=board,
            winner=winner,
            win_amount=win_amount,  # Solo en BB
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
            hand = self.format_hand(hand_text, filename=filename)
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