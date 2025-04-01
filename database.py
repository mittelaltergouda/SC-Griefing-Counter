import sqlite3
import config
import os
import threading
import time
import logging

# Logger für diese Datei einrichten
logger = logging.getLogger(__name__)

# Global lock for thread-safe DB operations
db_lock = threading.Lock()

class DatabaseError(Exception):
    """Basisklasse für Datenbankfehler"""
    pass

class NoPlayerConfiguredError(DatabaseError):
    """Wird ausgelöst, wenn kein Spieler konfiguriert ist"""
    pass

class DatabaseAccessError(DatabaseError):
    """Wird ausgelöst bei allgemeinen Fehlern beim Datenbankzugriff"""
    pass

def init_db():
    """
    Initializes the database for the current player and creates necessary tables.
    Raises:
        NoPlayerConfiguredError: Wenn kein Spieler konfiguriert ist
        DatabaseAccessError: Bei allgemeinen Datenbankfehlern
    """
    # Stelle sicher, dass die Konfiguration geladen ist
    if not config.CURRENT_PLAYER_NAME and os.path.exists(config.CONFIG_FILE):
        config.load_config()

    db_path = config.get_db_name()
    if not db_path:
        raise NoPlayerConfiguredError("No player name set. Cannot initialize database.")

    # Restlicher Code bleibt unverändert
    if not os.path.exists(db_path):
        logger.info(f"Creating new database file: {os.path.basename(db_path)}")

    try:
        with db_lock:
            conn = sqlite3.connect(db_path, timeout=30)
            c = conn.cursor()

            # Kills table with UNIQUE constraint to prevent duplicate kill events across log files
            c.execute("""
                CREATE TABLE IF NOT EXISTS kills (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    killed_player TEXT,
                    killer TEXT,
                    zone TEXT,
                    weapon TEXT,
                    damage_class TEXT,
                    damage_type TEXT,
                    UNIQUE(timestamp, killed_player, killer, zone, weapon, damage_class, damage_type)
                )
            """)

            # File positions table
            c.execute("""
                CREATE TABLE IF NOT EXISTS file_positions (
                    file_path TEXT PRIMARY KEY,
                    last_offset INTEGER
                )
            """)

            # NPC categories table
            c.execute("""
                CREATE TABLE IF NOT EXISTS npc_categories (
                    npc_name TEXT PRIMARY KEY,
                    category TEXT
                )
            """)

            conn.commit()
            conn.close()
    except sqlite3.Error as e:
        logger.error(f"SQLite error during initialization: {str(e)}")
        raise DatabaseAccessError(f"Failed to initialize database: {str(e)}") from e

def execute_query(query, params=()):
    """
    Executes a single query (INSERT, UPDATE, DELETE, or SELECT) on the player's DB.
    Returns rows if it's a SELECT, otherwise None.
    
    Raises:
        NoPlayerConfiguredError: Wenn kein Spieler konfiguriert ist
        DatabaseAccessError: Bei allgemeinen Datenbankfehlern
    """
    db_path = config.get_db_name()
    if not db_path:
        raise NoPlayerConfiguredError("No player name set. Cannot execute query.")

    try:
        with db_lock:
            conn = sqlite3.connect(db_path, timeout=30)
            c = conn.cursor()
            c.execute(query, params)
            result = None
            if query.strip().lower().startswith("select"):
                result = c.fetchall()
            conn.commit()
            conn.close()
        return result
    except sqlite3.Error as e:
        logger.error(f"SQLite error during query execution: {str(e)}")
        logger.debug(f"Query: {query}, Params: {params}")
        raise DatabaseAccessError(f"Failed to execute query: {str(e)}") from e

def execute_many(query, param_list):
    """
    Executes a batch query with multiple parameter sets (e.g. for inserting many rows).
    
    Raises:
        NoPlayerConfiguredError: Wenn kein Spieler konfiguriert ist
        DatabaseAccessError: Bei allgemeinen Datenbankfehlern
    """
    db_path = config.get_db_name()
    if not db_path:
        raise NoPlayerConfiguredError("No player name set. Cannot execute many.")
        
    try:
        with db_lock:
            conn = sqlite3.connect(db_path, timeout=30)
            c = conn.cursor()
            c.executemany(query, param_list)
            conn.commit()
            conn.close()
    except sqlite3.Error as e:
        logger.error(f"SQLite error during batch execution: {str(e)}")
        logger.debug(f"Query: {query}, Param count: {len(param_list)}")
        raise DatabaseAccessError(f"Failed to execute batch query: {str(e)}") from e

def fetch_query(query, params=()):
    """
    Helper function for SELECT queries, returning the result.
    
    Raises:
        NoPlayerConfiguredError: Wenn kein Spieler konfiguriert ist
        DatabaseAccessError: Bei allgemeinen Datenbankfehlern
    """
    return execute_query(query, params)

def get_db_size_kb():
    """
    Returns the database file size in KB.
    """
    db_path = config.get_db_name()
    if not db_path or not os.path.exists(db_path):
        return 0
    return os.path.getsize(db_path) / 1024

def ensure_db_initialized():
    """
    Ensures the database is initialized by calling init_db().
    
    Raises:
        NoPlayerConfiguredError: Wird abgefangen und protokolliert
    """
    # Stelle sicher, dass die Konfiguration geladen ist
    if not config.CURRENT_PLAYER_NAME and os.path.exists(config.CONFIG_FILE):
        config.load_config()
        
    try:
        # Immer init_db aufrufen, um sicherzustellen, dass alle Tabellen existieren,
        # auch wenn die Datenbankdatei bereits vorhanden ist
        init_db()
    except NoPlayerConfiguredError as e:
        logger.error(str(e))
        # Exception hier abfangen, damit die Anwendung weiterlaufen kann
        # auch wenn keine DB-Initialisierung möglich ist
