"""
update_checker.py

Modul zur Überprüfung und Durchführung von Updates für den Star Citizen Griefing Counter.
Ermöglicht automatisches Herunterladen und Installieren von neuen Versionen.
"""

import os
import sys
import json
import subprocess
import requests
import logging
import shutil
from packaging import version

logger = logging.getLogger(__name__)

# Der GitHub-Username und Repo-Name sollten in einer Konfigurationsdatei gespeichert
# oder zur Laufzeit durch GitHub Actions gesetzt werden
GITHUB_REPO_OWNER = os.environ.get('GITHUB_REPOSITORY_OWNER', 'mittelaltergouda')
GITHUB_REPO_NAME = "SC-Griefing-Counter" # Verwende das Hauptrepo statt eines separaten Release-Repos

# Datei, die anzeigt, dass ein Update durchgeführt wurde
UPDATE_MARKER_FILE = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 
                                  "SC-Griefing-Counter", "update_performed.marker")

def check_for_updates(current_version):
    """
    Prüft, ob eine neue Version des Griefing Counters verfügbar ist.
    
    Args:
        current_version (str): Die aktuelle Versionsnummer der Anwendung
        
    Returns:
        tuple: (update_available, latest_version, changelog)
            - update_available (bool): True wenn ein Update verfügbar ist, sonst False
            - latest_version (str): Die neueste verfügbare Version
            - changelog (str): Änderungsprotokoll für die neue Version
    """
    try:
        # URL zur Version - Die URL wird dynamisch zusammengesetzt
        # Falls keine GitHub-Owner-Variable verfügbar ist, wird die aktuelle Version zurückgegeben
        if not GITHUB_REPO_OWNER:
            logger.warning("GitHub Repository Owner nicht verfügbar. Update-Check wird übersprungen.")
            return False, current_version, ""
            
        # Verwende die GitHub Releases API statt der GitHub Pages
        api_url = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/releases/latest"
        
        # Version-Info herunterladen
        response = requests.get(api_url, timeout=5)
        response.raise_for_status()
        release_info = response.json()
        
        # Extrahiere Version aus dem Tag-Namen (v0.8.0 -> 0.8.0)
        latest_version = release_info["tag_name"]
        if latest_version.startswith('v'):
            latest_version = latest_version[1:]
        
        # Lade version.json für Changelog
        assets_url = [asset["browser_download_url"] for asset in release_info["assets"] 
                     if asset["name"] == "version.json"]
        
        changelog = ""
        if assets_url:
            version_response = requests.get(assets_url[0], timeout=5)
            if version_response.status_code == 200:
                version_info = version_response.json()
                changelog = version_info.get("changelog", "")
        
        # Vergleiche Versionen
        if version.parse(latest_version) > version.parse(current_version):
            logger.info(f"Neue Version verfügbar: {latest_version} (Aktuell: {current_version})")
            return True, latest_version, changelog or release_info.get("body", "")
        else:
            logger.debug(f"Keine neue Version verfügbar. Aktuell: {current_version}, Server: {latest_version}")
            return False, latest_version, ""
            
    except Exception as e:
        logger.error(f"Fehler bei der Updateprüfung: {str(e)}")
        return False, current_version, ""

def start_updater():
    """
    Startet den Updater (gc-updater.exe) und beendet die aktuelle Anwendung.
    Setzt auch einen Marker, der anzeigt, dass ein Update durchgeführt wurde.
    
    Returns:
        bool: True wenn der Updater erfolgreich gestartet wurde, sonst False
    """
    try:
        # Markiere Update für späteres Aufräumen
        mark_update_performed()
        
        # Versuche zuerst den regulären Updater
        updater_path = os.path.join(os.path.dirname(sys.executable), "gc-updater.exe")
        
        # Als nächstes prüfen wir auf den verbesserten Updater
        fixed_updater_path = os.path.join(os.path.dirname(sys.executable), "gc-updater-fixed.exe")
        fixed_script_path = os.path.join(os.path.dirname(sys.executable), "gc-updater-fixed.py")
        
        # Für Entwicklungsumgebung (wenn nicht als exe ausgeführt)
        if not os.path.exists(updater_path) and os.path.basename(sys.executable) != "griefing_counter.exe":
            # Suche nach den Skript-Varianten
            updater_script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gc-updater.py")
            fixed_script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gc-updater-fixed.py")
            
            # Bevorzuge den verbesserten Updater
            if os.path.exists(fixed_script_path):
                logger.info(f"Starte verbesserten Updater im Entwicklungsmodus: {fixed_script_path}")
                subprocess.Popen([sys.executable, fixed_script_path], 
                               creationflags=subprocess.CREATE_NEW_CONSOLE)
                sys.exit(0)
            elif os.path.exists(updater_script_path):
                logger.info(f"Starte Updater im Entwicklungsmodus: {updater_script_path}")
                subprocess.Popen([sys.executable, updater_script_path], 
                               creationflags=subprocess.CREATE_NEW_CONSOLE)
                sys.exit(0)
        
        # In der packaged Version zuerst den verbesserten Updater versuchen
        if os.path.exists(fixed_updater_path):
            logger.info(f"Starte verbesserten Updater: {fixed_updater_path}")
            if os.name == 'nt':  # Windows
                subprocess.Popen([fixed_updater_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                subprocess.Popen([fixed_updater_path])
            sys.exit(0)
        # Dann den verbesserten Skript-Updater (falls eine Exe-Version fehlt)
        elif os.path.exists(fixed_script_path) and os.path.exists(sys.executable) and sys.executable.endswith('.exe'):
            logger.info(f"Starte verbesserten Updater-Skript: {fixed_script_path}")
            subprocess.Popen([sys.executable, fixed_script_path], 
                           creationflags=subprocess.CREATE_NEW_CONSOLE)
            sys.exit(0)
        # Schließlich den regulären Updater als Fallback
        elif os.path.exists(updater_path):
            logger.info(f"Starte Standard-Updater: {updater_path}")
            if os.name == 'nt':  # Windows
                subprocess.Popen([updater_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                subprocess.Popen([updater_path])
            sys.exit(0)
        else:
            logger.error(f"Updater nicht gefunden: weder {updater_path} noch {fixed_updater_path}")
            return False
    except Exception as e:
        logger.error(f"Fehler beim Starten des Updaters: {str(e)}")
        return False

def mark_update_performed():
    """
    Erstellt eine Markierungsdatei, die anzeigt, dass ein Update durchgeführt wurde.
    Diese Datei wird beim nächsten Start der Anwendung überprüft, um AppData zu bereinigen.
    """
    try:
        # Stelle sicher, dass das Verzeichnis existiert
        os.makedirs(os.path.dirname(UPDATE_MARKER_FILE), exist_ok=True)
        
        # Erstelle die Markierungsdatei
        with open(UPDATE_MARKER_FILE, 'w') as f:
            f.write(f"Update-Marker: {os.path.basename(sys.executable)}")
            
        logger.info(f"Update-Marker erstellt: {UPDATE_MARKER_FILE}")
    except Exception as e:
        logger.error(f"Fehler beim Erstellen des Update-Markers: {str(e)}")

def check_and_clear_after_update():
    """
    Überprüft, ob ein Update durchgeführt wurde, und bereinigt AppData, wenn ja.
    Sollte beim Start der Anwendung aufgerufen werden.
    
    Returns:
        bool: True wenn AppData nach einem Update gelöscht wurde, sonst False
    """
    import config  # Importiere hier, um zirkuläre Imports zu vermeiden
    
    try:
        if os.path.exists(UPDATE_MARKER_FILE):
            logger.info("Update-Marker gefunden - bereinige AppData")
            
            # Bereinige AppData
            clean_appdata()
            
            # Lösche den Update-Marker
            os.remove(UPDATE_MARKER_FILE)
            logger.info("Update-Marker entfernt")
            
            return True
    except Exception as e:
        logger.error(f"Fehler beim Überprüfen des Update-Markers: {str(e)}")
    
    return False

def clean_appdata():
    """
    Löscht Logs und Datenbank aus dem AppData-Verzeichnis.
    """
    import config  # Importiere hier, um zirkuläre Imports zu vermeiden
    
    try:
        # Schließe die Datenbank, falls geöffnet
        try:
            import database
            # Verwende die neu hinzugefügte close_db-Funktion
            database.close_db()
            logger.info("Datenbank wurde erfolgreich geschlossen")
        except Exception as db_error:
            logger.warning(f"Datenbank konnte nicht explizit geschlossen werden: {str(db_error)}")
            # Fortsetzung des Löschvorgangs trotz Fehler
        
        # Lösche Logs
        if os.path.exists(config.LOG_FOLDER):
            logger.info(f"Lösche Logs in: {config.LOG_FOLDER}")
            for subfolder in [config.ERROR_LOG_FOLDER, config.GENERAL_LOG_FOLDER, config.DEBUG_LOG_FOLDER]:
                if os.path.exists(subfolder):
                    for file in os.listdir(subfolder):
                        file_path = os.path.join(subfolder, file)
                        try:
                            if os.path.isfile(file_path):
                                os.unlink(file_path)
                        except Exception as e:
                            logger.error(f"Fehler beim Löschen von {file_path}: {e}")
        
        # Lösche Datenbank
        if os.path.exists(config.DB_FOLDER):
            logger.info(f"Lösche Datenbanken in: {config.DB_FOLDER}")
            for file in os.listdir(config.DB_FOLDER):
                file_path = os.path.join(config.DB_FOLDER, file)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    logger.error(f"Fehler beim Löschen von {file_path}: {e}")
    
        logger.info("AppData nach Update bereinigt")
    except Exception as e:
        logger.error(f"Fehler beim Bereinigen von AppData: {str(e)}")