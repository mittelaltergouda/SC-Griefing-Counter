import re
import database
import logging

# Logger für diese Datei einrichten
logger = logging.getLogger(__name__)

def clean_npc_name(npc_name):
    """
    Removes trailing numeric IDs from an NPC name.
    Example: "pu_human_enemy_npc_juggernaut_12345" -> "pu_human_enemy_npc_juggernaut"
    """
    return re.sub(r'_\d+$', '', npc_name.strip().lower())

def auto_categorize_npc(npc_name):
    """
    Automatically determines a category for an NPC based on keywords in the cleaned name.
    Returns one of: pilot, gunner, ground, civilian, worker, lawenforcement, pirate, technical, test, animal, or uncategorized.
    """
    name = clean_npc_name(npc_name).lower()
    
    # Spezielle Regel für ARGO_ATLS_GEO - als "unknown" kategorisieren
    if "argo_atls_geo" in name:
        logger.debug(f"NPC {npc_name} als 'unknown' kategorisiert (ARGO_ATLS_GEO)")
        return "unknown"
    
    # Erweiterte Kategorisierung: Alle Namen mit "hangar" und "unknown" als "unknown" klassifizieren
    if "hangar" in name.lower() and "unknown" in name.lower():
        logger.debug(f"NPC {npc_name} als 'unknown' kategorisiert (enthält 'hangar' und 'unknown')")
        return "unknown"
    
    # Tierkategorisierung basierend auf Präfixen
    if any(name.startswith(prefix) for prefix in ["vlk_", "kopion_", "quasigrazer_"]):
        return "animal"
        
    # NPC_Archetypes-Kategorisierung - diese sollten NIEMALS als Spieler klassifiziert werden
    if "npc_archetypes" in name:
        if "soldier" in name or "juggernaut" in name:
            return "ground"
        elif "pilot" in name:
            return "pilot"
        elif "techie" in name or "technical" in name:
            return "technical"
        elif "prisoner" in name or "civilian" in name:
            return "civilian"
        else:
            # Allgemeine NPC_Archetypes als Grundeinheit einstufen
            return "ground"
    
    # Hazard-Dungeon-NPCs erkennen (außer den speziell behandelten Fall)
    if "hazard" in name and "dungeon" in name:
        if "exec" in name:
            return "ground"  # Executive NPCs in Hazard-Dungeons
        elif "medic" in name or "med" in name:
            return "technical"  # Medics in Hazard-Dungeons
        else:
            return "ground"  # Standard-Einstufung für Hazard-Dungeon-NPCs
    
    if "pilot" in name:
        return "pilot"
    if "gunner" in name:
        return "gunner"
    if any(k in name for k in ["ground", "soldier", "cqc", "juggernaut", "sniper",
                               "gangster", "grunt", "kareah", "militia", "superboss",
                               "exec", "executive"]):
        return "ground"
    if "civilian" in name or ("populace" in name and "worker" not in name):
        return "civilian"
    if any(k in name for k in ["worker", "shopkeeper", "vendor", "gardener", "farmer"]):
        return "worker"
    if any(k in name for k in ["law", "security", "guard"]):
        return "lawenforcement"
    if "pirate" in name:
        return "pirate"
    if any(k in name for k in ["engineer", "technical", "techie", "medic"]):
        return "technical"
    if "test" in name:
        return "test"
    # Allgemeine Cheesecake-Archetypes als Grundeinheit einstufen
    if "cheesecake" in name:
        return "ground"
    # Wenn 'hazard' im Namen ist, aber nicht genauer kategorisiert werden kann
    if "hazard" in name:
        return "ground"
    return "uncategorized"

def get_npc_category(npc_name):
    """
    Returns the category for the cleaned NPC name from DB, or None if not found.
    """
    try:
        cleaned = clean_npc_name(npc_name)
        res = database.fetch_query(
            "SELECT category FROM npc_categories WHERE npc_name=?",
            (cleaned,)
        )
        if res and len(res) > 0:
            return res[0][0]
        return None
    except database.DatabaseError as e:
        logger.error(f"Fehler beim Abrufen der NPC-Kategorie für {npc_name}: {str(e)}")
        return None

def load_all_npc_categories():
    """
    Loads all npc_name->category from the DB into a dictionary.
    """
    try:
        rows = database.fetch_query("SELECT npc_name, category FROM npc_categories")
        out_dict = {}
        if rows:
            for (name, cat) in rows:
                out_dict[name] = cat
        return out_dict
    except database.DatabaseError as e:
        logger.error(f"Fehler beim Laden aller NPC-Kategorien: {str(e)}")
        return {}

def recategorize_uncategorized():
    """
    Checks all NPCs in npc_categories that are 'uncategorized' and tries to recategorize them.
    """
    try:
        rows = database.fetch_query(
            "SELECT npc_name, category FROM npc_categories WHERE category='uncategorized'"
        )
        if not rows:
            return
            
        updated_count = 0
        for (npc_name, old_cat) in rows:
            new_cat = auto_categorize_npc(npc_name)
            if new_cat != "uncategorized":
                database.execute_query(
                    "UPDATE npc_categories SET category=? WHERE npc_name=?",
                    (new_cat, npc_name)
                )
                logger.info(f"Recategorized {npc_name} from {old_cat} to {new_cat}")
                updated_count += 1
                
        if updated_count > 0:
            logger.debug(f"Insgesamt {updated_count} NPCs neu kategorisiert")
    except database.DatabaseError as e:
        logger.error(f"Fehler bei der Neukategorisierung von NPCs: {str(e)}")

def save_npc_category(npc_name, default_category="uncategorized"):
    """
    If npc_name not in npc_categories, auto-categorize and do INSERT OR IGNORE.
    Afterwards, calls recategorize_uncategorized() once.
    """
    try:
        cleaned = clean_npc_name(npc_name)
        existing = get_npc_category(cleaned)
        if existing is not None:
            return  # Already known

        cat = auto_categorize_npc(cleaned)
        if cat == "uncategorized" and default_category != "uncategorized":
            cat = default_category

        database.execute_query(
            "INSERT OR IGNORE INTO npc_categories (npc_name, category) VALUES (?, ?)",
            (cleaned, cat)
        )
        logger.info(f"NPC kategorisiert: {cleaned}, Kategorie={cat}")
        
        # Versuche, unkategorisierte NPCs neu zu kategorisieren
        recategorize_uncategorized()
    except database.DatabaseError as e:
        logger.error(f"Fehler beim Speichern der NPC-Kategorie für {npc_name}: {str(e)}")
