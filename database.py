import sqlite3
import config
import os
import threading

# Global lock for thread-safe DB operations
db_lock = threading.Lock()

def init_db():
    """
    Initializes the database for the current player and creates necessary tables.
    """
    db_path = config.get_db_name()
    if not db_path:
        print("[ERROR] No player name set. Cannot initialize database.")
        return

    if not os.path.exists(db_path):
        print(f"[INFO] Creating new database file: {os.path.basename(db_path)}")

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

def execute_query(query, params=()):
    """
    Executes a single query (INSERT, UPDATE, DELETE, or SELECT) on the player's DB.
    Returns rows if it's a SELECT, otherwise None.
    """
    db_path = config.get_db_name()
    if not db_path:
        print("[ERROR] No player name set. Cannot execute query.")
        return None

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

def execute_many(query, param_list):
    """
    Executes a batch query with multiple parameter sets (e.g. for inserting many rows).
    """
    db_path = config.get_db_name()
    if not db_path:
        print("[ERROR] No player name set. Cannot execute many.")
        return
    with db_lock:
        conn = sqlite3.connect(db_path, timeout=30)
        c = conn.cursor()
        c.executemany(query, param_list)
        conn.commit()
        conn.close()

def fetch_query(query, params=()):
    """
    Helper function for SELECT queries, returning the result.
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
