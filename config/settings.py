import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
DEBUG_DIR = os.path.join(LOGS_DIR, 'debug')

RAW_HAND_HISTORIES_DIR = os.path.join(BASE_DIR, 'data', 'raw_hand_history')
PROCESSED_HAND_HISTORIES_DIR = os.path.join(BASE_DIR, 'data', 'processed_hand_history')
FORMATTED_HANDS_DIR = os.path.join(BASE_DIR, 'data', 'formatted_hands')
ANALYZED_HANDS_DIR = os.path.join(BASE_DIR, 'data', 'analyzed_hands')

POKERSTARS_HAND_HISTORY_PATH = r"C:\Users\Pablo\AppData\Local\PokerStars.ES\HandHistory\SrLyce"
#POKERSTARS_HAND_HISTORY_PATH = r"C:\Users\PABLO\Documents\projects\SrLyce"
POKERSTARS_HERO_NAME = "SrLyce"