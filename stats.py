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
import logging
from datetime import datetime, time, timedelta
import config
import database
import npc_handler

# Logger einrichten
logger = logging.getLogger(__name__)

class StatsError(Exception):
    """Basisklasse für Fehler in der Statistik-Berechnung"""
    pass

def clean_id(text):
    """Entfernt anhängende numerische IDs von Strings (z. B. NPC-Namen, Waffen)."""
    # Grundlegende ID-Entfernung
    text = re.sub(r'(_\d+)$', '', text)
    return text

def clean_npc_name(name):
    """Bereinigt NPC-Namen für die Kategorisierung und entfernt ID-Anhänge."""
    if not name:
        return ""
    
    # Zu Kleinbuchstaben konvertieren
    name_lower = name.lower()
    
    # Entferne numerische IDs am Ende
    clean_name = re.sub(r'(_\d+)$', '', name_lower)
    
    return clean_name

def categorize_missing_npcs():
    """Durchsucht die Datenbank nach NPCs mit vlk_, kopion_, oder quasigrazer_ Präfixen, 
    die noch nicht in npc_categories sind, und fügt sie hinzu."""
    try:
        # Hole alle Killer und Victims aus der Datenbank
        all_entities = database.fetch_query("""
            SELECT DISTINCT killed_player FROM kills
            UNION
            SELECT DISTINCT killer FROM kills
        """)

        count = 0
        for (entity,) in all_entities:
            entity_lower = entity.strip().lower()
            # Prüfe, ob es sich um einen NPC mit einem der Präfixe handelt
            if entity_lower.startswith(("vlk_", "kopion_", "quasigrazer_")):
                # Füge ihn zur NPC-Kategorie hinzu, wenn er noch nicht existiert
                try:
                    npc_handler.save_npc_category(entity_lower, "uncategorized")
                    count += 1
                except Exception as e:
                    logger.error(f"Fehler beim Kategorisieren von NPC {entity_lower}: {str(e)}")
        
        logger.info(f"Categorized {count} previously uncategorized NPCs")
        return count
    except database.DatabaseError as e:
        logger.error(f"Datenbankfehler beim Kategorisieren von NPCs: {str(e)}")
        return 0
    except Exception as e:
        logger.error(f"Allgemeiner Fehler beim Kategorisieren von NPCs: {str(e)}", exc_info=True)
        return 0

def get_stats(start_date=None, end_date=None, entity_filters=None):
    """
    Berechnet die Gesamt- und Detailstatistiken zu Kills/Deaths aus der Datenbank für den aktuellen Spieler.
    
    Args:
        start_date (datetime, optional): Startdatum für die Filterung
        end_date (datetime, optional): Enddatum für die Filterung
        entity_filters (dict, optional): Filter für Entitätstypen (players, npcs, etc.)
            Format: {'players': True, 'npc_pilot': False, ...}
    
    Returns:
        tuple: (stats_text, recent_kill_events_text)
    """
    try:
        if not config.CURRENT_PLAYER_NAME:
            logger.warning("Kein Spielername konfiguriert")
            return ("No player name set.", "No kill events to show.")

        player_lower = config.CURRENT_PLAYER_NAME.lower()

        # Debugging: Log the filter parameters
        logger.debug(f"Fetching stats for player: {player_lower}")
        logger.debug(f"Start date: {start_date}, End date: {end_date}")
        logger.debug(f"Entity filters: {entity_filters}")

        # Wenn keine Entity-Filter gesetzt sind, alle anzeigen
        if entity_filters is None:
            entity_filters = {
                "players": True,
                "unknown": True,
            }
            for category in config.NPC_CATEGORIES:
                entity_filters[f"npc_{category}"] = True

        # Anpassung der Datumsformate für SQL
        
        # Startdatum: Wenn angegeben, setze es auf 00:00:00 des Tages
        if start_date:
            start_date = datetime.combine(start_date.date(), time.min)
            start_date_str = start_date.strftime('%Y-%m-%d %H:%M:%S')
        else:
            start_date_str = None
        
        # Enddatum: Wenn angegeben, setze es auf 00:00:00 des NÄCHSTEN Tages
        if end_date:
            # Setze auf 00:00:00 des nächsten Tages, um den vollen Tag einzuschließen
            end_date = datetime.combine(end_date.date(), time.min) + timedelta(days=1)
            end_date_str = end_date.strftime('%Y-%m-%d %H:%M:%S')
        else:
            end_date_str = None

        # Debug-Ausgabe der angepassten Datumsfilter
        logger.debug(f"Adjusted date filters - Start: {start_date_str}, End: {end_date_str}")

        # Add date filters to SQL queries
        date_filter = ""
        date_params = []
        
        # Standardfilter für Datum
        if start_date_str:
            date_filter += " AND timestamp >= ?"
            date_params.append(start_date_str)
        if end_date_str:
            date_filter += " AND timestamp < ?"  # Wichtig: Verwende "<" statt "<=" da end_date jetzt auf den nächsten Tag zeigt
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
        """, tuple(kill_detail_params)) or []        # Death Breakdown - filtert Selbstmorde aus (nur Tode durch andere)
        death_detail_params = [player_lower, player_lower] + date_params
        deaths_detail = database.fetch_query(f"""
            SELECT killer FROM kills
            WHERE LOWER(killed_player)=? AND LOWER(killer) <> ? {date_filter}
        """, tuple(death_detail_params)) or []

        npc_dict = npc_handler.load_all_npc_categories()

        # Initialisiere Zählvariablen mit allen NPC-Kategorien
        kill_counts = {
            "players": 0, "npc_pilot": 0, "npc_civilian": 0, "npc_worker": 0,
            "npc_lawenforcement": 0, "npc_gunner": 0, "npc_technical": 0,
            "npc_test": 0, "npc_pirate": 0, "npc_ground": 0, "npc_animal": 0,
            "npc_uncategorized": 0
        }
        # Initialisiere Death Breakdown Zähler (mit "unknown")
        death_counts = {
            "players": 0, "npc_pilot": 0, "npc_civilian": 0, "npc_worker": 0,
            "npc_lawenforcement": 0, "npc_gunner": 0, "npc_technical": 0,
            "npc_test": 0, "npc_pirate": 0, "npc_ground": 0, "npc_animal": 0,
            "npc_uncategorized": 0, "unknown": 0
        }

        # Filtere und zähle Kills basierend auf den Entity-Filtern
        for (victim,) in kills_detail:
            cleaned = npc_handler.clean_npc_name(victim)
            # Tiere und andere NPC-Typen erkennen
            if cleaned.startswith(("vlk_", "kopion_", "quasigrazer_")):
                category = "npc_animal"
                if entity_filters.get(category, True):
                    kill_counts[category] += 1
            elif cleaned.startswith("pu_"):
                cat = npc_dict.get(cleaned, "uncategorized")
                category = f"npc_{cat}"
                if entity_filters.get(category, True):
                    kill_counts[category] = kill_counts.get(category, 0) + 1
            else:
                if entity_filters.get("players", True):
                    kill_counts["players"] += 1

        # Filtere und zähle Deaths basierend auf den Entity-Filtern
        for (killer,) in deaths_detail:
            cleaned = npc_handler.clean_npc_name(killer)
            if cleaned.lower() == "unknown":
                if entity_filters.get("unknown", True):
                    death_counts["unknown"] = death_counts.get("unknown", 0) + 1
            # Tiere und andere NPC-Typen erkennen
            elif cleaned.startswith(("vlk_", "kopion_", "quasigrazer_")):
                category = "npc_animal"
                if entity_filters.get(category, True):
                    death_counts[category] += 1
            elif cleaned.startswith("pu_"):
                cat = npc_dict.get(cleaned, "uncategorized")
                category = f"npc_{cat}"
                if entity_filters.get(category, True):
                    death_counts[category] = death_counts.get(category, 0) + 1
            else:
                # Wenn es nicht als NPC identifiziert wurde, betrachten wir es als Spieler
                if entity_filters.get("players", True):
                    death_counts["players"] += 1

        # Berechne gefilterte Totalsummen für die Anzeige
        filtered_kills = sum(count for category, count in kill_counts.items() if entity_filters.get(category, True))
        filtered_deaths = sum(count for category, count in death_counts.items() 
                            if entity_filters.get(category, True) and category != "unknown")
        
        # K/D-Ratio mit gefilterten Werten
        filtered_kd_ratio = filtered_kills / filtered_deaths if filtered_deaths > 0 else float('inf')

        stats_text = (
            f"Total Kills (filtered): {filtered_kills}\n"
            f"Total Deaths (excl. suicides, filtered): {filtered_deaths}\n"
            f"K/D Ratio (filtered): {filtered_kd_ratio:.2f}\n\n"
            f"Kills Breakdown:\n"
        )
        
        # Füge nur die Kategorien hinzu, die im Filter aktiviert sind
        if entity_filters.get("players", True):
            stats_text += f"  Player Kills: {kill_counts['players']}\n"
        
        # Alle NPC-Kategorien
        for category in config.NPC_CATEGORIES:
            key = f"npc_{category}"
            if entity_filters.get(key, True):
                stats_text += f"  NPC {category.capitalize()} Kills: {kill_counts.get(key, 0)}\n"
        
        stats_text += "\nDeaths Breakdown:\n"
        
        # Spieler-Deaths
        if entity_filters.get("players", True):
            stats_text += f"  Player Deaths: {death_counts['players']}\n"
        
        # Unknown Deaths
        if entity_filters.get("unknown", True):
            stats_text += f"  Unknown Deaths: {death_counts.get('unknown', 0)}\n"
        
        # Selbstmorde immer anzeigen
        stats_text += f"  Suicides: {suicides}\n"
        
        # Alle NPC-Kategorien für Deaths
        for category in config.NPC_CATEGORIES:
            key = f"npc_{category}"
            if entity_filters.get(key, True):
                stats_text += f"  NPC {category.capitalize()} Deaths: {death_counts.get(key, 0)}\n"

        recent_text = get_recent_kill_events(start_date, end_date, entity_filters)
        return stats_text, recent_text
        
    except database.DatabaseError as e:
        logger.error(f"Datenbankfehler bei der Statistikberechnung: {str(e)}")
        return (f"Database error: {str(e)}", "No kill events to show due to database error.")
    except Exception as e:
        logger.error(f"Fehler bei der Statistikberechnung: {str(e)}", exc_info=True)
        return (f"Error calculating statistics: {str(e)}", "No kill events to show due to error.")

def get_recent_kill_events(start_date=None, end_date=None, entity_filters=None):
    """
    Formatiert die letzten 100 Kill-Events:
      - Es werden nur Events zurückgegeben, bei denen der Spieler entweder als Killer oder Opfer auftritt,
      - Selbstmorde werden ausgeschlossen,
      - Die Ergebnisse werden anhand des Timestamps (absteigend: neueste zuerst) sortiert,
      - Namen werden von anhängenden Zahlen befreit.
      
    Args:
        start_date (datetime, optional): Startdatum für die Filterung
        end_date (datetime, optional): Enddatum für die Filterung
        entity_filters (dict, optional): Filter für Entitätstypen (players, npcs, etc.)
            Format: {'players': True, 'npc_pilot': False, ...}
    """
    try:
        if not config.CURRENT_PLAYER_NAME:
            logger.warning("Kein Spielername für Recent-Events konfiguriert")
            return "No player name set."
            
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
            LIMIT 1000
        """, tuple(all_params))

        recent_text = ""
        
        # Debug-Ausgabe
        logger.debug(f"Recent Kill Events: {len(recent_res)} Einträge gefunden")
        
        # NPC-Kategorien für die Filterung laden
        npc_dict = npc_handler.load_all_npc_categories()
        
        # Wenn keine Entity-Filter gesetzt sind, alle anzeigen
        if entity_filters is None:
            entity_filters = {
                "players": True,
                "unknown": True,
            }
            for category in config.NPC_CATEGORIES:
                entity_filters[f"npc_{category}"] = True
        
        events_shown = 0
        
        for ev in recent_res:
            ts, killed_p, killer, zone, weapon, dmg_class, dmg_type = ev
            
            # Kategorie des Killers und Opfers bestimmen
            killer_category = "unknown"
            victim_category = "unknown"
            
            # Killer-Kategorie bestimmen
            cleaned_killer = npc_handler.clean_npc_name(killer)
            if cleaned_killer.lower() == player_lower.lower():
                killer_category = "players"  # Der Spieler selbst
            elif cleaned_killer.lower() == "unknown":
                killer_category = "unknown"
            elif cleaned_killer.startswith(("vlk_", "kopion_", "quasigrazer_")):
                killer_category = "npc_animal"
            elif cleaned_killer.startswith("pu_"):
                cat = npc_dict.get(cleaned_killer, "uncategorized")
                killer_category = f"npc_{cat}"
            else:
                killer_category = "players"  # Andere Spieler
                
            # Opfer-Kategorie bestimmen
            cleaned_victim = npc_handler.clean_npc_name(killed_p)
            if cleaned_victim.lower() == player_lower.lower():
                victim_category = "players"  # Der Spieler selbst
            elif cleaned_victim.startswith(("vlk_", "kopion_", "quasigrazer_")):
                victim_category = "npc_animal"
            elif cleaned_victim.startswith("pu_"):
                cat = npc_dict.get(cleaned_victim, "uncategorized")
                victim_category = f"npc_{cat}"
            else:
                victim_category = "players"  # Andere Spieler

            # Debug-Ausgabe
            logger.debug(f"Killer: {killer} (Kategorie: {killer_category}), Victim: {killed_p} (Kategorie: {victim_category})")
            
            # Überprüfen, ob dieses Event angezeigt werden soll basierend auf den Filtern
            # Spieler ist Opfer: Zeige, wenn Killer-Kategorie aktiviert ist
            # Spieler ist Killer: Zeige, wenn Opfer-Kategorie aktiviert ist
            show_event = False
            if cleaned_victim.lower() == player_lower.lower():
                show_event = entity_filters.get(killer_category, True)
            elif cleaned_killer.lower() == player_lower.lower():
                show_event = entity_filters.get(victim_category, True)
            
            if not show_event:
                continue
                
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
            
            events_shown += 1
            if events_shown >= 100:  # Begrenze auf 100 gefilterte Einträge
                break
        
        # Debug-Ausgabe
        logger.debug(f"Recent Kill Events angezeigt: {events_shown}")
        
        return recent_text
        
    except database.DatabaseError as e:
        logger.error(f"Datenbankfehler beim Abrufen aktueller Events: {str(e)}")
        return "Database error occurred while retrieving recent events."
    except Exception as e:
        logger.error(f"Fehler beim Abrufen aktueller Events: {str(e)}", exc_info=True)
        return f"Error retrieving recent kill events: {str(e)}"

def get_leaderboards(start_date=None, end_date=None, entity_filters=None):
    """
    Gibt zwei Listen zurück (kill_leaderboard, death_leaderboard):
      - Kill Leaderboard: Spieler und NPCs, die der Benutzer getötet hat (basierend auf Filtern).
      - Death Leaderboard: Spieler und NPCs, die den Benutzer getötet haben (basierend auf Filtern).
    
    Args:
        start_date: Optional[datetime] - Filtere Ereignisse nach diesem Datum
        end_date: Optional[datetime] - Filtere Ereignisse vor diesem Datum
        entity_filters: Optional[dict] - Filter für Entitätstypen 
            Format: {'players': True, 'npc_pilot': False, ...}
    """
    try:
        if not config.CURRENT_PLAYER_NAME:
            logger.warning("Kein Spielername für Leaderboards konfiguriert")
            return [], []

        # Stelle sicher, dass alle vlk_, kopion_, quasigrazer_ und pu_-NPCs kategorisiert sind
        categorize_missing_npcs()
        
        # Initialisiere leere Ergebnismengen
        kill_data = []
        death_data = []
        
        # Standardfilter, wenn keine angegeben sind
        if entity_filters is None:
            entity_filters = {
                "players": True,
                "unknown": True,
            }
            for category in config.NPC_CATEGORIES:
                entity_filters[f"npc_{category}"] = True
        
        player_lower = config.CURRENT_PLAYER_NAME.lower()
        
        # Anpassung der Datumsformate für SQL
        
        # Startdatum: Wenn angegeben, setze es auf 00:00:00 des Tages
        if start_date:
            start_date = datetime.combine(start_date.date(), time.min)
            start_date_str = start_date.strftime('%Y-%m-%d %H:%M:%S')
        else:
            start_date_str = None
        
        # Enddatum: Wenn angegeben, setze es auf 00:00:00 des NÄCHSTEN Tages
        if end_date:
            # Setze auf 00:00:00 des nächsten Tages, um den vollen Tag einzuschließen
            end_date = datetime.combine(end_date.date(), time.min) + timedelta(days=1)
            end_date_str = end_date.strftime('%Y-%m-%d %H:%M:%S')
        else:
            end_date_str = None
        
        # Debug-Ausgabe der angepassten Datumsfilter
        logger.debug(f"Leaderboards - Adjusted date filters - Start: {start_date_str}, End: {end_date_str}")

        # Füge Datumsfilter hinzu
        date_filter = ""
        date_params = []
        if start_date_str:
            date_filter += " AND timestamp >= ?"
            date_params.append(start_date_str)
        if end_date_str:
            date_filter += " AND timestamp < ?"  # Wichtig: Verwende "<" statt "<=" da end_date jetzt auf den nächsten Tag zeigt
            date_params.append(end_date_str)

        # Lade alle Kills ohne Filterung
        kill_params = [player_lower, player_lower] + date_params
        all_kills = database.fetch_query(f"""
            SELECT killed_player, COUNT(*) as cnt
            FROM kills
            WHERE LOWER(killer) = ?
              AND LOWER(killed_player) <> ?
              {date_filter}
            GROUP BY LOWER(killed_player)
            ORDER BY cnt DESC
        """, tuple(kill_params))        # Lade alle Deaths ohne Filterung (exklusive Selbstmorde)
        death_params = [player_lower, player_lower] + date_params
        all_deaths = database.fetch_query(f"""
            SELECT killer, COUNT(*) as cnt
            FROM kills
            WHERE LOWER(killed_player) = ?
              AND LOWER(killer) <> ?
              {date_filter}
            GROUP BY LOWER(killer)
            ORDER BY cnt DESC
        """, tuple(death_params))

        # NPC-Kategorien für die Filterung laden
        npc_dict = npc_handler.load_all_npc_categories()
        
        # Dictionary für die Zusammenfassung von NPCs mit verschiedenen IDs aber gleichem Basisnamen
        kill_summary = {}
        death_summary = {}
        
        # Kill-Leaderboard filtern und IDs bei NPCs entfernen
        for name, count in all_kills:
            # Entferne die ID am Ende des Namens (bei bestimmten NPCs)
            clean_name = name
            
            # Entferne ID-Anhänge sowohl für PU_* als auch für vlk_*, kopion_*, quasigrazer_* NPCs
            import re
            match = re.search(r'(.+?)_\d+$', name)
            if match:
                clean_name = match.group(1)
                
            # Bereinigter Name für die Kategorisierung
            cleaned = npc_handler.clean_npc_name(name)
            
            # Hangar & Unknown Check - als unknown behandeln
            if "hangar" in cleaned.lower() and "unknown" in cleaned.lower():
                if entity_filters.get("unknown", True):
                    # Zu unknown hinzufügen, wenn unknown-Filter aktiv ist
                    kill_summary[clean_name] = kill_summary.get(clean_name, 0) + count
                continue  # Skip weitere Checks, da wir die Kategorie bereits kennen
            
            # Spezieller Check für NPC_Archetypes - diese NIEMALS als Spieler zeigen
            if "npc_archetypes" in cleaned.lower():
                # Auto-Kategorisierung durchführen
                category = npc_handler.auto_categorize_npc(cleaned)
                npc_category = f"npc_{category}"
                if entity_filters.get(npc_category, True):
                    # Füge zum Summary-Dict hinzu
                    kill_summary[clean_name] = kill_summary.get(clean_name, 0) + count
                continue  # Skip weitere Checks
            
            # Entity-Kategorie bestimmen und entsprechend filtern
            elif cleaned.startswith(("vlk_", "kopion_", "quasigrazer_")):
                if entity_filters.get("npc_animal", True):
                    # Füge zum Summary-Dict hinzu
                    kill_summary[clean_name] = kill_summary.get(clean_name, 0) + count
            elif cleaned.startswith("pu_"):
                cat = npc_dict.get(cleaned, "uncategorized")
                if entity_filters.get(f"npc_{cat}", True):
                    # Füge zum Summary-Dict hinzu
                    kill_summary[clean_name] = kill_summary.get(clean_name, 0) + count
            else:
                if entity_filters.get("players", True):
                    # Spielernamen hinzufügen (keine Zusammenfassung nötig)
                    kill_summary[clean_name] = kill_summary.get(clean_name, 0) + count

        # Death-Leaderboard filtern und IDs bei NPCs entfernen
        for name, count in all_deaths:
            # Entferne die ID am Ende des Namens (bei bestimmten NPCs)
            clean_name = name
            
            # Entferne ID-Anhänge sowohl für PU_* als auch für vlk_*, kopion_*, quasigrazer_* NPCs
            import re
            match = re.search(r'(.+?)_\d+$', name)
            if match:
                clean_name = match.group(1)
            
            cleaned = npc_handler.clean_npc_name(name)
            
            # Hangar & Unknown Check - als unknown behandeln
            if "hangar" in cleaned.lower() and "unknown" in cleaned.lower():
                if entity_filters.get("unknown", True):
                    # Zu unknown hinzufügen, wenn unknown-Filter aktiv ist
                    death_summary[clean_name] = death_summary.get(clean_name, 0) + count
                continue  # Skip weitere Checks, da wir die Kategorie bereits kennen
            
            # Spezieller Check für NPC_Archetypes - diese NIEMALS als Spieler zeigen
            if "npc_archetypes" in cleaned.lower():
                # Auto-Kategorisierung durchführen
                category = npc_handler.auto_categorize_npc(cleaned)
                npc_category = f"npc_{category}"
                if entity_filters.get(npc_category, True):
                    death_summary[clean_name] = death_summary.get(clean_name, 0) + count
                continue  # Skip weitere Checks
            
            # Spezieller Check für Hazard_dungeon NPCs - immer als NPC betrachten
            elif "hazard" in cleaned.lower() and "dungeon" in cleaned.lower() and not ("hangar" in cleaned.lower() and "unknown" in cleaned.lower()):
                category = npc_handler.auto_categorize_npc(cleaned)
                npc_category = f"npc_{category}"
                if entity_filters.get(npc_category, True):
                    death_summary[clean_name] = death_summary.get(clean_name, 0) + count
                continue  # Skip weitere Checks
            
            # Spezieller Fall für Unknown-Entities
            elif cleaned.lower() == "unknown":
                if entity_filters.get("unknown", True):
                    death_summary[clean_name] = death_summary.get(clean_name, 0) + count
            
            # Spieler-Selbstmorde überspringen
            elif cleaned.lower() == player_lower:
                # Selbstmorde nicht anzeigen
                continue
                
            # NPCs mit klassifizierbaren Präfixen
            elif cleaned.startswith(("vlk_", "kopion_", "quasigrazer_")):
                if entity_filters.get("npc_animal", True):
                    death_summary[clean_name] = death_summary.get(clean_name, 0) + count
                    
            elif cleaned.startswith("pu_"):
                cat = npc_dict.get(cleaned, "uncategorized")
                if entity_filters.get(f"npc_{cat}", True):
                    death_summary[clean_name] = death_summary.get(clean_name, 0) + count
                    
            # WICHTIG: Alle anderen Einträge werden als Spieler betrachtet
            else:
                if entity_filters.get("players", True):
                    death_summary[clean_name] = death_summary.get(clean_name, 0) + count

        # Konvertiere die Zusammenfassungs-Dictionaries zurück in Listen von Tupeln
        kill_data = [(name, count) for name, count in kill_summary.items()]
        death_data = [(name, count) for name, count in death_summary.items()]
        
        # Sortiere die gefilterten Daten und beschränke auf Top 10
        kill_data.sort(key=lambda x: x[1], reverse=True)
        death_data.sort(key=lambda x: x[1], reverse=True)
        
        # Debug-Ausgabe
        logger.debug(f"Kill-Leaderboard: {len(kill_data)} Einträge gefunden")
        logger.debug(f"Death-Leaderboard: {len(death_data)} Einträge gefunden")

        return kill_data[:10], death_data[:10]
        
    except database.DatabaseError as e:
        logger.error(f"Datenbankfehler beim Erstellen der Leaderboards: {str(e)}")
        return [], []
    except Exception as e:
        logger.error(f"Fehler beim Erstellen der Leaderboards: {str(e)}", exc_info=True)
        return [], []
