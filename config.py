import os

# Folders for logs
LIVE_FOLDER = r"C:\Program Files\Roberts Space Industries\StarCitizen\LIVE"
BACKUP_FOLDER = os.path.join(LIVE_FOLDER, "logbackups")
GAME_LOG_FILENAME = "Game.log"

# Logging folders
LOG_FOLDER = "Logs"
ERROR_LOG_FOLDER = os.path.join(LOG_FOLDER, "errors")
GENERAL_LOG_FOLDER = os.path.join(LOG_FOLDER, "general")

# Ensure directories exist
os.makedirs(ERROR_LOG_FOLDER, exist_ok=True)
os.makedirs(GENERAL_LOG_FOLDER, exist_ok=True)

# Where we store the player's config
CONFIG_FILE = "config.txt"

# Folder where DB files are stored
DB_FOLDER = "databases"

# Default/Global values
CURRENT_PLAYER_NAME = ""
LOGGING_ENABLED = True  # Standardmäßig ist Logging aktiviert
LOGGING_LEVEL = "INFO"  # Standardmäßig auf INFO-Level

def load_config():
    """Loads the configuration file and sets global variables."""
    global CURRENT_PLAYER_NAME, LOGGING_ENABLED, LOGGING_LEVEL
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
    else:
        save_config()

def save_config():
    """Saves the current config settings to a file with comments for better user understanding."""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        f.write("# Spielername des aktuellen Benutzers\n")
        f.write(f"PLAYER_NAME={CURRENT_PLAYER_NAME}\n\n")

        f.write("# Aktiviert oder deaktiviert das Logging (true/false)\n")
        f.write(f"LOGGING_ENABLED={'true' if LOGGING_ENABLED else 'false'}\n\n")

        f.write("# Logging-Level: DEBUG, INFO, WARNING, ERROR, CRITICAL\n")
        f.write(f"LOGGING_LEVEL={LOGGING_LEVEL}\n")

def get_db_name():
    """
    Returns the database file path for the current player.
    Creates DB_FOLDER if it doesn't exist.
    """
    if not CURRENT_PLAYER_NAME:
        return None
    os.makedirs(DB_FOLDER, exist_ok=True)
    return os.path.join(DB_FOLDER, f"star_citizen_kills_{CURRENT_PLAYER_NAME}.db")

# Load config at startup
load_config()
