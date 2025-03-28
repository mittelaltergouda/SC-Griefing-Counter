"""
logger.py

Dieses Modul enthält die Konfiguration für das Logging im Griefing Counter Projekt.
Es bietet eine zentrale Funktion `setup_logging`, um das Logging für die gesamte Anwendung zu konfigurieren.

Funktionen:
- setup_logging: Konfiguriert das Logging mit Datei- und Konsolen-Handlern.

Verwendung:
- Importieren Sie dieses Modul und rufen Sie `setup_logging` auf, um das Logging zu initialisieren.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime
import traceback
from config import LOGGING_ENABLED, LOGGING_LEVEL, DEBUG_LOG_FOLDER

def setup_logging(general_log_folder, error_log_folder, debug_log_folder=DEBUG_LOG_FOLDER, log_level=LOGGING_LEVEL, app_logger_name=None, enable_logging=LOGGING_ENABLED):
    """
    Konfiguriert das Logging für das Projekt.

    Parameter:
    - general_log_folder (str): Pfad zum Ordner für allgemeine Log-Dateien.
    - error_log_folder (str): Pfad zum Ordner für Fehler-Log-Dateien.
    - debug_log_folder (str, optional): Pfad zum Ordner für Debug-Log-Dateien.
    - log_level (str): Logging-Level (z. B. "INFO", "DEBUG").
    - app_logger_name (str, optional): Name des spezifischen Loggers. Standard ist der Root-Logger.
    - enable_logging (bool): Wenn False, wird ein NullHandler hinzugefügt und Logging deaktiviert.

    Rückgabe:
    - logging.Logger: Der konfigurierte Logger.
    """
    if not enable_logging:
        logging.getLogger().addHandler(logging.NullHandler())
        return None

    # Erstelle die Ordner, falls sie nicht existieren
    os.makedirs(general_log_folder, exist_ok=True)
    os.makedirs(error_log_folder, exist_ok=True)
    if debug_log_folder:
        os.makedirs(debug_log_folder, exist_ok=True)

    # Zeitstempel für die Log-Dateien
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    general_log_file = os.path.join(general_log_folder, f"griefing_counter_{timestamp}.log")
    error_log_file = os.path.join(error_log_folder, f"griefing_counter_errors_{timestamp}.log")
    debug_log_file = os.path.join(debug_log_folder, f"griefing_counter_debug_{timestamp}.log") if debug_log_folder else None

    # Logger konfigurieren
    logger = logging.getLogger(app_logger_name) if app_logger_name else logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper(), logging.DEBUG))

    # Allgemeine Log-Datei
    general_handler = RotatingFileHandler(general_log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8")
    general_handler.setLevel(logging.INFO)
    general_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(general_handler)

    # Fehler-Log-Datei
    error_handler = RotatingFileHandler(error_log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8")
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s\n%(exc_info)s"))
    logger.addHandler(error_handler)

    # Debug-Log-Datei (optional)
    if debug_log_folder:
        debug_log_file = os.path.join(debug_log_folder, f"griefing_counter_debug_{timestamp}.log")
        debug_handler = RotatingFileHandler(debug_log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8")
        debug_handler.setLevel(logging.DEBUG)
        debug_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - [%(module)s:%(lineno)d] - %(message)s"))
        logger.addHandler(debug_handler)

    # Konsolen-Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(console_handler)

    return logger