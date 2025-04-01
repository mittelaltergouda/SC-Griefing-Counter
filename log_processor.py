import os
import re
import config
import logging
from datetime import datetime

# Stelle sicher, dass die Konfiguration vor allem anderen geladen wird
if not config.CURRENT_PLAYER_NAME and os.path.exists(config.CONFIG_FILE):
    config.load_config()

# Erst NACH dem Laden der Konfiguration weitere Module importieren
import database
import npc_handler

# Initialisiere den Logger korrekt
logger = logging.getLogger("GriefingCounter")

# Stelle sicher, dass die Datenbank initialisiert ist
database.ensure_db_initialized()

# Prüfen, ob die file_positions Tabelle tatsächlich existiert
try:
    test = database.fetch_query("SELECT COUNT(*) FROM file_positions")
except Exception as e:
    # Falls die Tabelle nicht existiert, führe init_db erneut aus
    logger.error(f"Tabellenfehler erkannt: {str(e)}")
    logger.info("Versuche Datenbank neu zu initialisieren...")
    database.init_db()  # Erneut ausführen, um fehlende Tabellen zu erstellen

ACTOR_DEATH_REGEX = re.compile(
    r"^<(?P<timestamp>[^>]+)>.*?<Actor Death>.*?'(?P<killed_player>[^']+)' \[\d+\].*?"
    r"in zone '(?P<zone>[^']+)'"
    r".*?killed by '(?P<killer>[^']+)' \[\d+\].*?using '(?P<weapon>[^']+)' \[Class (?P<class>[^]]+)\].*?"
    r"with damage type '(?P<damage_type>[^']+)'",
    re.IGNORECASE
)

def parse_log_line(line):
    """Parses a single log line using ACTOR_DEATH_REGEX, returns dict if matched."""
    match = ACTOR_DEATH_REGEX.match(line)
    if match:
        return match.groupdict()
    return None

def process_log_file(file_path):
    """Reads new lines from file_path, extracts kill events for the current player, saves to DB."""
    if not os.path.exists(file_path):
        return

    # Log start
    logger.info(f"Starting to read log: {file_path}")

    try:
        offset_res = database.fetch_query(
            "SELECT last_offset FROM file_positions WHERE file_path = ?", (file_path,)
        )
        offset = offset_res[0][0] if offset_res else 0

        new_events = []
        player = config.CURRENT_PLAYER_NAME.strip().lower() if config.CURRENT_PLAYER_NAME else ""
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            f.seek(offset)
            for line in f:
                event = parse_log_line(line.strip())
                if event and player:
                    killer = event["killer"].strip().lower()
                    victim = event["killed_player"].strip().lower()
                    # Only store events where the current player is killer or victim
                    if killer == player or victim == player:
                        # Auto-categorize NPCs - erweitert um weitere NPC-Präfixe
                        for key in ("killed_player", "killer"):
                            val = event[key].strip().lower()
                            if val.startswith("pu_") or val.startswith("vlk_") or val.startswith("kopion_") or val.startswith("quasigrazer_"):
                                npc_handler.save_npc_category(val, "uncategorized")

                        new_events.append((
                            event["timestamp"],
                            event["killed_player"],
                            event["killer"],
                            event["zone"],
                            event["weapon"],
                            event["class"],
                            event["damage_type"]
                        ))

        if new_events:
            try:
                database.execute_many("""\
                    INSERT OR IGNORE INTO kills (timestamp, killed_player, killer, zone, weapon, damage_class, damage_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, new_events)
                logger.info(f"Stored {len(new_events)} new events from {file_path}")
            except Exception as e:
                logger.error(f"Fehler beim Speichern von Ereignissen: {str(e)}")
                # Tabellen neu initialisieren und erneut versuchen
                database.init_db()
                database.execute_many("""\
                    INSERT OR IGNORE INTO kills (timestamp, killed_player, killer, zone, weapon, damage_class, damage_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, new_events)
                logger.info(f"Nach Neuinitialisierung: {len(new_events)} Ereignisse gespeichert")

        new_offset = os.path.getsize(file_path)
        try:
            database.execute_query("""\
                INSERT OR REPLACE INTO file_positions (file_path, last_offset)
                VALUES (?, ?)
            """, (file_path, new_offset))
        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren der Dateiposition: {str(e)}")
            # Tabellen neu initialisieren und erneut versuchen
            database.init_db()
            database.execute_query("""\
                INSERT OR REPLACE INTO file_positions (file_path, last_offset)
                VALUES (?, ?)
            """, (file_path, new_offset))
            
    except Exception as e:
        logger.error(f"Allgemeiner Fehler bei der Verarbeitung von {file_path}: {str(e)}")
        # Stellen Sie sicher, dass die Datenbank in einem konsistenten Zustand ist
        database.init_db()

    # Log finish
    logger.info(f"Finished reading log: {file_path}")

def parse_all_backup_logs():
    """Reads all backup logs once, so only new lines are processed for each."""
    if not os.path.isdir(config.BACKUP_FOLDER):
        return
    logs = [f for f in os.listdir(config.BACKUP_FOLDER) if f.lower().endswith(".log")]
    logs.sort()
    for lf in logs:
        full_path = os.path.join(config.BACKUP_FOLDER, lf)
        process_log_file(full_path)

def get_backup_log_progress():
    """
    Returns a tuple (imported, total) representing how many backup logs
    have been processed (offset > 0) and total log files in BACKUP_FOLDER.
    """
    if not os.path.isdir(config.BACKUP_FOLDER):
        return (0, 0)
    logs = [f for f in os.listdir(config.BACKUP_FOLDER) if f.lower().endswith(".log")]
    total = len(logs)
    imported = 0
    for lf in logs:
        full_path = os.path.join(config.BACKUP_FOLDER, lf)
        res = database.fetch_query(
            "SELECT last_offset FROM file_positions WHERE file_path = ?", (full_path,)
        )
        if res and res[0][0] > 0:
            imported += 1
    return imported, total
