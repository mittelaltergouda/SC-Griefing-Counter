import os
import sys
from pathlib import Path

# Hilfsfunktion, um den richtigen Pfad für Anwendungsdaten zu bestimmen
def get_app_data_path():
    """Gibt den Pfad zum Anwendungsdatenverzeichnis im AppData-Ordner zurück."""
    app_name = "SC-Griefing-Counter"
    
    # Unter Windows AppData-Verzeichnis verwenden
    app_data = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), app_name)
    return app_data

# Folders for logs
LIVE_FOLDER = r"C:\Program Files\Roberts Space Industries\StarCitizen\LIVE"
BACKUP_FOLDER = os.path.join(LIVE_FOLDER, "logbackups")
GAME_LOG_FILENAME = "Game.log"

# Anwendungsverzeichnis für Daten
APP_DATA_PATH = get_app_data_path()

# Logging folders (nun im Benutzerverzeichnis)
LOG_FOLDER = os.path.join(APP_DATA_PATH, "Logs")
ERROR_LOG_FOLDER = os.path.join(LOG_FOLDER, "errors")
GENERAL_LOG_FOLDER = os.path.join(LOG_FOLDER, "general")
DEBUG_LOG_FOLDER = os.path.join(LOG_FOLDER, "debug")

# Config-Datei im Benutzerverzeichnis
CONFIG_FILE = os.path.join(APP_DATA_PATH, "config.txt")

# Folder where DB files are stored (im Benutzerverzeichnis)
DB_FOLDER = os.path.join(APP_DATA_PATH, "databases")

# Verschoben in eine Funktion, um PyArmor-Kompatibilität zu verbessern
def ensure_directories_exist():
    """Stellt sicher, dass alle benötigten Verzeichnisse existieren."""
    try:
        os.makedirs(APP_DATA_PATH, exist_ok=True)
        os.makedirs(ERROR_LOG_FOLDER, exist_ok=True)
        os.makedirs(GENERAL_LOG_FOLDER, exist_ok=True)
        os.makedirs(DEBUG_LOG_FOLDER, exist_ok=True)
        os.makedirs(DB_FOLDER, exist_ok=True)
    except Exception as e:
        print(f"Fehler beim Erstellen der Verzeichnisse: {e}")
        # Fallback: Verwende temporäres Verzeichnis
        global APP_DATA_PATH, LOG_FOLDER, ERROR_LOG_FOLDER, GENERAL_LOG_FOLDER, DEBUG_LOG_FOLDER, CONFIG_FILE, DB_FOLDER
        import tempfile
        temp_dir = tempfile.gettempdir()
        APP_DATA_PATH = os.path.join(temp_dir, "SC-Griefing-Counter")
        LOG_FOLDER = os.path.join(APP_DATA_PATH, "Logs")
        ERROR_LOG_FOLDER = os.path.join(LOG_FOLDER, "errors")
        GENERAL_LOG_FOLDER = os.path.join(LOG_FOLDER, "general")
        DEBUG_LOG_FOLDER = os.path.join(LOG_FOLDER, "debug")
        CONFIG_FILE = os.path.join(APP_DATA_PATH, "config.txt")
        DB_FOLDER = os.path.join(APP_DATA_PATH, "databases")
        
        # Versuche, die temporären Verzeichnisse zu erstellen
        os.makedirs(APP_DATA_PATH, exist_ok=True)
        os.makedirs(ERROR_LOG_FOLDER, exist_ok=True)
        os.makedirs(GENERAL_LOG_FOLDER, exist_ok=True)
        os.makedirs(DEBUG_LOG_FOLDER, exist_ok=True)
        os.makedirs(DB_FOLDER, exist_ok=True)

# Default/Global values
CURRENT_PLAYER_NAME = ""
LOGGING_ENABLED = True  # Standardmäßig ist Logging aktiviert
LOGGING_LEVEL = "INFO"  # Standardmäßig auf INFO-Level
REFRESH_INTERVAL = 30   # Standardmäßig 30 Sekunden

# NPC-Typen für Filter
NPC_CATEGORIES = [
    "pilot", "gunner", "ground", "civilian", "worker", 
    "lawenforcement", "pirate", "technical", "test", "animal", "uncategorized"
]

def load_config():
    """Loads the configuration file and sets global variables."""
    global CURRENT_PLAYER_NAME, LOGGING_ENABLED, LOGGING_LEVEL, REFRESH_INTERVAL
    
    # Stelle zuerst sicher, dass die benötigten Verzeichnisse existieren
    ensure_directories_exist()
    
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("PLAYER_NAME="):
                    CURRENT_PLAYER_NAME = line.split("=")[1]
                elif line.startswith("LOGGING_ENABLED="):
                    LOGGING_ENABLED = line.split("=")[1].lower() == "true"
                elif line.startswith("LOGGING_LEVEL="):
                    LOGGING_LEVEL = line.split("=")[1].upper()
                elif line.startswith("REFRESH_INTERVAL="):
                    try:
                        interval = int(line.split("=")[1])
                        REFRESH_INTERVAL = max(1, min(interval, 10000))  # Begrenze auf sinnvolle Werte
                    except ValueError:
                        # Bei Fehler Standard verwenden
                        pass
    else:
        save_config()

def save_config():
    """Saves the current config settings to a file with comments for better user understanding."""
    # Stelle sicher, dass Verzeichnisse existieren
    ensure_directories_exist()
    
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        f.write("# Spielername des aktuellen Benutzers\n")
        f.write(f"PLAYER_NAME={CURRENT_PLAYER_NAME}\n\n")

        f.write("# Aktiviert oder deaktiviert das Logging (true/false)\n")
        f.write(f"LOGGING_ENABLED={'true' if LOGGING_ENABLED else 'false'}\n\n")

        f.write("# Logging-Level: DEBUG, INFO, WARNING, ERROR, CRITICAL\n")
        f.write(f"LOGGING_LEVEL={LOGGING_LEVEL}\n\n")
        
        f.write("# Automatische Aktualisierungsintervall in Sekunden\n")
        f.write(f"REFRESH_INTERVAL={REFRESH_INTERVAL}\n")

def get_db_name():
    """
    Returns the database file path for the current player.
    Creates DB_FOLDER if it doesn't exist.
    """
    if not CURRENT_PLAYER_NAME:
        return None
    
    # Stelle sicher, dass das Datenbankverzeichnis existiert
    os.makedirs(DB_FOLDER, exist_ok=True)
    return os.path.join(DB_FOLDER, f"star_citizen_kills_{CURRENT_PLAYER_NAME}.db")

# Lade Konfiguration beim Import
try:
    load_config()
except Exception as e:
    print(f"Fehler beim Laden der Konfiguration: {e}")
    # Wenn es Probleme gibt, versuchen wir es im Hauptprogramm später nochmal
