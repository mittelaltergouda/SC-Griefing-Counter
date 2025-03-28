"""
stats.py

Berechnet die Gesamt- und Detailstatistiken zu Kills/Deaths aus der Datenbank für den aktuellen Spieler.
- Bei den Kills werden Selbstmorde nicht berücksichtigt.
- Bei den Deaths wird als "Total Deaths" nur die Zahl der Deaths durch Gegner (ohne Selbstmorde) angezeigt;
  die Selbstmorde werden separat im Death Breakdown gelistet.
- Zwei Leaderboards:
  - Kill Leaderboard: Top 10 Spieler, die der Benutzer getötet hat (NPCs und Selbstmorde ausgeschlossen).
  - Death Leaderboard: Top 10 Spieler, die den Benutzer getötet haben (NPCs und Selbstmorde ausgeschlossen).
- Recent Kill Events werden anhand des Timestamps in absteigender Reihenfolge (neueste zuerst) angezeigt.
"""

import re
import database
import config
import npc_handler
from datetime import datetime

def clean_id(text):
    """Entfernt anhängende numerische IDs von Strings (z. B. NPC-Namen, Waffen)."""
    return re.sub(r'(_\d+)$', '', text)

def get_stats(start_date=None, end_date=None):
    if not config.CURRENT_PLAYER_NAME:
        return ("No player name set.", "No kill events to show.")

    player_lower = config.CURRENT_PLAYER_NAME.lower()

    # Debugging: Log the filter parameters
    print(f"Fetching stats for player: {player_lower}")
    print(f"Start date: {start_date}, End date: {end_date}")

    # Convert dates to strings for SQL comparison
    start_date_str = start_date.strftime('%Y-%m-%d %H:%M:%S') if start_date else None
    end_date_str = end_date.strftime('%Y-%m-%d %H:%M:%S') if end_date else None

    # Add date filters to SQL queries
    date_filter = ""
    date_params = []
    if start_date_str:
        date_filter += " AND timestamp >= ?"
        date_params.append(start_date_str)
    if end_date_str:
        date_filter += " AND timestamp <= ?"
        date_params.append(end_date_str)

    # Gesamtkills (ohne Selbstmorde)
    kill_params = [player_lower, player_lower] + date_params
    kills_res = database.fetch_query(f"""
        SELECT COUNT(*) FROM kills
        WHERE LOWER(killer)=? AND LOWER(killed_player) <> ? {date_filter}
    """, tuple(kill_params))
    kills_by_me = kills_res[0][0] if kills_res else 0

    # Gesamtdeaths (inklusive Selbstmorde)
    death_params = [player_lower] + date_params  # Hier nur ein Parameter für player_lower
    deaths_res = database.fetch_query(f"""
        SELECT COUNT(*) FROM kills
        WHERE LOWER(killed_player)=? {date_filter}
    """, tuple(death_params))
    deaths_total = deaths_res[0][0] if deaths_res else 0

    # Selbstmorde
    suicide_params = [player_lower, player_lower] + date_params
    suicide_res = database.fetch_query(f"""
        SELECT COUNT(*) FROM kills
        WHERE LOWER(killer)=? AND LOWER(killed_player)=? {date_filter}
    """, tuple(suicide_params))
    suicides = suicide_res[0][0] if suicide_res else 0

    # Deaths by others (ohne Selbstmorde)
    deaths_by_others = deaths_total - suicides

    # K/D-Ratio (ohne Selbstmorde)
    kd_ratio = kills_by_me / deaths_by_others if deaths_by_others > 0 else float('inf')

    # Kills Breakdown (nur Kills, bei denen der Spieler als Killer agierte, ohne Selbstmorde)
    kill_detail_params = [player_lower, player_lower] + date_params
    kills_detail = database.fetch_query(f"""
        SELECT killed_player FROM kills
        WHERE LOWER(killer)=? AND LOWER(killed_player) <> ? {date_filter}
    """, tuple(kill_detail_params)) or []

    # Death Breakdown now includes suicides and unknown deaths (no killer filter)
    death_detail_params = [player_lower] + date_params
    deaths_detail = database.fetch_query(f"""
        SELECT killer FROM kills
        WHERE LOWER(killed_player)=? {date_filter}
    """, tuple(death_detail_params)) or []

    npc_dict = npc_handler.load_all_npc_categories()

    # Initialisiere Zählvariablen
    kill_counts = {
        "players": 0, "npc_pilot": 0, "npc_civilian": 0, "npc_worker": 0,
        "npc_lawenforcement": 0, "npc_gunner": 0, "npc_technical": 0,
        "npc_test": 0, "npc_uncategorized": 0
    }
    # Initialize Death Breakdown counters (add "unknown")
    death_counts = {
        "players": 0, "npc_pilot": 0, "npc_civilian": 0, "npc_worker": 0,
        "npc_lawenforcement": 0, "npc_gunner": 0, "npc_technical": 0,
        "npc_test": 0, "npc_uncategorized": 0, "unknown": 0
    }

    for (victim,) in kills_detail:
        cleaned = npc_handler.clean_npc_name(victim)
        if not cleaned.startswith("pu_"):
            kill_counts["players"] += 1
        else:
            cat = npc_dict.get(cleaned, "uncategorized")
            key = f"npc_{cat}"
            kill_counts[key] = kill_counts.get(key, 0) + 1

    for (killer,) in deaths_detail:
        cleaned = npc_handler.clean_npc_name(killer)
        if cleaned.lower() == "unknown":
            death_counts["unknown"] = death_counts.get("unknown", 0) + 1
        elif not cleaned.startswith("pu_"):
            death_counts["players"] += 1
        else:
            cat = npc_dict.get(cleaned, "uncategorized")
            key = f"npc_{cat}"
            death_counts[key] = death_counts.get(key, 0) + 1

    stats_text = (
        f"Total Kills: {kills_by_me}\n"
        f"Total Deaths (excl. suicides): {deaths_by_others}\n"
        f"K/D Ratio (excl. suicides): {kd_ratio:.2f}\n\n"
        f"Kills Breakdown:\n"
        f"  Player Kills: {kill_counts['players']}\n"
        f"  NPC Pilot Kills: {kill_counts.get('npc_pilot', 0)}\n"
        f"  NPC Civilian Kills: {kill_counts.get('npc_civilian', 0)}\n"
        f"  NPC Worker Kills: {kill_counts.get('npc_worker', 0)}\n"
        f"  NPC Law Enforcement Kills: {kill_counts.get('npc_lawenforcement', 0)}\n"
        f"  NPC Gunner Kills: {kill_counts.get('npc_gunner', 0)}\n"
        f"  NPC Technical Kills: {kill_counts.get('npc_technical', 0)}\n"
        f"  NPC Test Kills: {kill_counts.get('npc_test', 0)}\n"
        f"  NPC Uncategorized: {kill_counts.get('npc_uncategorized', 0)}\n\n"
        f"Deaths Breakdown:\n"
        f"  Player Deaths: {death_counts['players']}\n"
        f"  Unknown Deaths: {death_counts.get('unknown', 0)}\n"
        f"  Suicides: {suicides}\n"
        f"  NPC Pilot Deaths: {death_counts.get('npc_pilot', 0)}\n"
        f"  NPC Civilian Deaths: {death_counts.get('npc_civilian', 0)}\n"
        f"  NPC Worker Deaths: {death_counts.get('npc_worker', 0)}\n"
        f"  NPC Law Enforcement Deaths: {death_counts.get('npc_lawenforcement', 0)}\n"
        f"  NPC Gunner Deaths: {death_counts.get('npc_gunner', 0)}\n"
        f"  NPC Technical Deaths: {death_counts.get('npc_technical', 0)}\n"
        f"  NPC Test Deaths: {death_counts.get('npc_test', 0)}\n"
        f"  NPC Uncategorized: {death_counts.get('npc_uncategorized', 0)}\n"
    )

    return stats_text, get_recent_kill_events(start_date, end_date)

def get_recent_kill_events(start_date=None, end_date=None):
    """
    Formatiert die letzten 100 Kill-Events:
      - Es werden nur Events zurückgegeben, bei denen der Spieler entweder als Killer oder Opfer auftritt,
      - Selbstmorde werden ausgeschlossen,
      - Die Ergebnisse werden anhand des Timestamps (absteigend: neueste zuerst) sortiert,
      - Namen werden von anhängenden Zahlen befreit.
    """
    player_lower = config.CURRENT_PLAYER_NAME.lower()
    start_date_str = start_date.strftime('%Y-%m-%d %H:%M:%S') if start_date else None
    end_date_str = end_date.strftime('%Y-%m-%d %H:%M:%S') if end_date else None

    date_filter = ""
    date_params = []
    params = [player_lower, player_lower, player_lower, player_lower]
    if start_date_str:
        date_filter += " AND timestamp >= ?"
        date_params.append(start_date_str)
    if end_date_str:
        date_filter += " AND timestamp <= ?"
        date_params.append(end_date_str)

    # Kombiniere alle Parameter
    all_params = params + date_params
    
    recent_res = database.fetch_query(f"""
        SELECT timestamp, killed_player, killer, zone, weapon, damage_class, damage_type
        FROM kills
        WHERE (LOWER(killer)=? OR LOWER(killed_player)=?)
          AND NOT (LOWER(killer)=? AND LOWER(killed_player)=?)
          {date_filter}
        ORDER BY timestamp DESC
        LIMIT 100
    """, tuple(all_params))

    recent_text = ""
    for ev in recent_res:
        ts, killed_p, killer, zone, weapon, dmg_class, dmg_type = ev

        # Namen bereinigen
        killed_p = clean_id(killed_p)
        weapon = clean_id(weapon)
        zone = clean_id(zone)

        recent_text += (
            f"Time: {ts}\n"
            f"Killer: {killer}\n"
            f"Killed: {killed_p}\n"
            f"Weapon: {weapon}\n"
            f"Class: {dmg_class}\n"
            f"Type: {dmg_type}\n"
            f"Zone: {zone}\n"
            "------------------------------------\n"
        )
    return recent_text

def get_leaderboards(start_date=None, end_date=None):
    """
    Gibt zwei Listen zurück (kill_leaderboard, death_leaderboard):
      - Kill Leaderboard: Top 10 Spieler, die der Benutzer getötet hat (ohne NPCs und Selbstmorde).
      - Death Leaderboard: Top 10 Spieler, die den Benutzer getötet haben (ohne NPCs und Selbstmorde).
    
    Args:
        start_date: Optional[datetime] - Filtere Ereignisse nach diesem Datum
        end_date: Optional[datetime] - Filtere Ereignisse vor diesem Datum
    """
    if not config.CURRENT_PLAYER_NAME:
        return [], []

    player_lower = config.CURRENT_PLAYER_NAME.lower()
    
    # Wandle Datumsangaben in Strings für SQL-Vergleiche um
    start_date_str = start_date.strftime('%Y-%m-%d %H:%M:%S') if start_date else None
    end_date_str = end_date.strftime('%Y-%m-%d %H:%M:%S') if end_date else None

    # Füge Datumsfilter hinzu
    date_filter = ""
    date_params = []
    if start_date_str:
        date_filter += " AND timestamp >= ?"
        date_params.append(start_date_str)
    if end_date_str:
        date_filter += " AND timestamp <= ?"
        date_params.append(end_date_str)

    # Kill Leaderboard Abfrage mit Datumsfilter
    kill_params = [player_lower, player_lower] + date_params
    kill_data = database.fetch_query(f"""
        SELECT killed_player, COUNT(*) as cnt
        FROM kills
        WHERE LOWER(killer) = ?
          AND LENGTH(killed_player) <= 35
          AND LOWER(killed_player) NOT IN (SELECT LOWER(npc_name) FROM npc_categories)
          AND LOWER(killed_player) <> ?
          {date_filter}
        GROUP BY LOWER(killed_player)
        ORDER BY cnt DESC
        LIMIT 10
    """, tuple(kill_params))

    # Death Leaderboard Abfrage mit Datumsfilter
    death_params = [player_lower, player_lower] + date_params
    death_data = database.fetch_query(f"""
        SELECT killer, COUNT(*) as cnt
        FROM kills
        WHERE LOWER(killed_player) = ?
          AND LENGTH(killer) <= 35
          AND LOWER(killer) NOT IN (SELECT LOWER(npc_name) FROM npc_categories)
          AND LOWER(killer) <> ?
          AND LOWER(killer) <> 'unknown'
          {date_filter}
        GROUP BY LOWER(killer)
        ORDER BY cnt DESC
        LIMIT 10
    """, tuple(death_params))

    return kill_data or [], death_data or []
