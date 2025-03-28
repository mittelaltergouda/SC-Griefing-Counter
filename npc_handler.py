import re
import database

def clean_npc_name(npc_name):
    """
    Removes trailing numeric IDs from an NPC name.
    Example: "pu_human_enemy_npc_juggernaut_12345" -> "pu_human_enemy_npc_juggernaut"
    """
    return re.sub(r'_\d+$', '', npc_name.strip().lower())

def auto_categorize_npc(npc_name):
    """
    Automatically determines a category for an NPC based on keywords in the cleaned name.
    Returns one of: pilot, gunner, ground, civilian, worker, lawenforcement, pirate, technical, test, or uncategorized.
    """
    name = clean_npc_name(npc_name)
    if "pilot" in name:
        return "pilot"
    if "gunner" in name:
        return "gunner"
    if any(k in name for k in ["ground", "soldier", "cqc", "juggernaut", "sniper",
                               "gangster", "grunt", "kareah", "militia"]):
        return "ground"
    if "civilian" in name or ("populace" in name and "worker" not in name):
        return "civilian"
    if any(k in name for k in ["worker", "shopkeeper", "vendor", "gardener", "farmer"]):
        return "worker"
    if any(k in name for k in ["law", "security", "guard"]):
        return "lawenforcement"
    if "pirate" in name:
        return "pirate"
    if any(k in name for k in ["engineer", "technical"]):
        return "technical"
    if "test" in name:
        return "test"
    return "uncategorized"

def get_npc_category(npc_name):
    """
    Returns the category for the cleaned NPC name from DB, or None if not found.
    """
    cleaned = clean_npc_name(npc_name)
    res = database.fetch_query(
        "SELECT category FROM npc_categories WHERE npc_name=?",
        (cleaned,)
    )
    if res and len(res) > 0:
        return res[0][0]
    return None

def load_all_npc_categories():
    """
    Loads all npc_name->category from the DB into a dictionary.
    """
    rows = database.fetch_query("SELECT npc_name, category FROM npc_categories")
    out_dict = {}
    if rows:
        for (name, cat) in rows:
            out_dict[name] = cat
    return out_dict

def recategorize_uncategorized():
    """
    Checks all NPCs in npc_categories that are 'uncategorized' and tries to recategorize them.
    """
    rows = database.fetch_query(
        "SELECT npc_name, category FROM npc_categories WHERE category='uncategorized'"
    )
    if not rows:
        return
    for (npc_name, old_cat) in rows:
        new_cat = auto_categorize_npc(npc_name)
        if new_cat != "uncategorized":
            database.execute_query(
                "UPDATE npc_categories SET category=? WHERE npc_name=?",
                (new_cat, npc_name)
            )
            print(f"[INFO] Recategorized {npc_name} from {old_cat} to {new_cat}")

def save_npc_category(npc_name, default_category="uncategorized"):
    """
    If npc_name not in npc_categories, auto-categorize and do INSERT OR IGNORE.
    Afterwards, calls recategorize_uncategorized() once.
    """
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
    print(f"[INFO] Inserted or ignored NPC: {cleaned}, category={cat}")
    recategorize_uncategorized()
