import os
import shutil
import sys

# Añadimos el path del proyecto para importar settings
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from config import settings

FOLDERS_TO_CLEAN = [
    settings.ANALYZED_HANDS_DIR,
    settings.FORMATTED_HANDS_DIR,
    os.path.join(settings.PROCESSED_HAND_HISTORIES_DIR, 'pokerstars'),
]

RAW_POKERSTARS_DIR = os.path.join(settings.RAW_HAND_HISTORIES_DIR, 'pokerstars')
RAW_BACKUP = os.path.join(RAW_POKERSTARS_DIR, 'backup')

def clean_folder(folder):
    if not os.path.isdir(folder):
        print(f"Carpeta no encontrada: {folder}")
        return
    for fname in os.listdir(folder):
        fpath = os.path.join(folder, fname)
        if os.path.isfile(fpath):
            os.remove(fpath)
    print(f"Carpeta limpiada: {folder}")

def restore_raw_backup():
    if not os.path.isdir(RAW_BACKUP):
        print(f"No backup folder found at {RAW_BACKUP}")
        return
    for fname in os.listdir(RAW_BACKUP):
        src = os.path.join(RAW_BACKUP, fname)
        dst = os.path.join(RAW_POKERSTARS_DIR, fname)
        if os.path.isfile(src):
            shutil.move(src, dst)
    print("Archivos restaurados de backup a raw_hand_history/pokerstars.")

if __name__ == "__main__":
    print("Limpiando carpetas de datos...")
    for folder in FOLDERS_TO_CLEAN:
        clean_folder(folder)

    print("Restaurando archivos de backup de raw_hand_history/pokerstars...")
    restore_raw_backup()
    print("¡Preparación de entorno de pruebas completada!")