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
from packaging import version

logger = logging.getLogger(__name__)

# Der GitHub-Username und Repo-Name sollten in einer Konfigurationsdatei gespeichert
# oder zur Laufzeit durch GitHub Actions gesetzt werden
GITHUB_REPO_OWNER = os.environ.get('GITHUB_REPOSITORY_OWNER', '')
GITHUB_REPO_NAME = "SC-Griefing-Counter" # Verwende das Hauptrepo statt eines separaten Release-Repos

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
    Startet den Updater (gc-updater.exe) und beendet die aktuelle Anwendung
    
    Returns:
        bool: True wenn der Updater erfolgreich gestartet wurde, sonst False
    """
    try:
        # Pfad zum Updater
        updater_path = os.path.join(os.path.dirname(sys.executable), "gc-updater.exe")
        
        # Für Entwicklungsumgebung (wenn nicht als exe ausgeführt)
        if not os.path.exists(updater_path) and os.path.basename(sys.executable) != "griefing_counter.exe":
            updater_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gc-updater.exe")
            
        if not os.path.exists(updater_path):
            logger.error(f"Updater nicht gefunden: {updater_path}")
            return False
            
        # Starte Updater
        logger.info(f"Starte Updater: {updater_path}")
        subprocess.Popen([updater_path])
        
        # Beende aktuelle Anwendung
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Fehler beim Starten des Updaters: {str(e)}")
        return False