import os
from datetime import datetime
import logging

from config import settings

def setup_logging():

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    curr_date = datetime.now().strftime("%Y%m%d")
    curr_datetime = datetime.now().strftime("%Y%m%d%H%M")

    path_log = os.path.join(settings.LOGS_DIR, f"{curr_date}.log")

    # Crear subcarpeta por fecha para los logs de debug
    debug_subdir = os.path.join(settings.DEBUG_DIR, curr_date)
    os.makedirs(debug_subdir, exist_ok=True)
    path_debug = os.path.join(debug_subdir, f"{curr_datetime}.log")

    formatter = logging.Formatter(fmt="%(asctime)s - %(levelname)s - %(name)s: %(message)s", datefmt="%Y-%m-%d | %H:%M")

    log_handler = logging.FileHandler(path_log, encoding="utf-8")
    log_handler.setLevel(logging.INFO)
    log_handler.setFormatter(formatter)
    logger.addHandler(log_handler)

    debug_handler = logging.FileHandler(path_debug, encoding="utf-8")
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.setFormatter(formatter)
    logger.addHandler(debug_handler)