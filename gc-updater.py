"""
gc-updater.py

Eigenständiges Update-Tool für den Star Citizen Griefing Counter.
Lädt die neueste Version herunter, überprüft den SHA256-Hash und ersetzt die alte Version.
"""

import os
import sys
import shutil
import hashlib
import requests
import subprocess
import json
import time
import logging

# Einfaches Logging einrichten
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("GC-Updater")

# Der GitHub-Username und Repo-Name sollten in einer Konfigurationsdatei gespeichert
# oder zur Laufzeit durch GitHub Actions gesetzt werden
GITHUB_REPO_OWNER = os.environ.get('GITHUB_REPOSITORY_OWNER', '')
GITHUB_REPO_NAME = "SC-Griefing-Counter-Releases"

def get_sha256(file_path):
    """Berechnet den SHA256-Hash einer Datei"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_file(url, local_path):
    """Lädt eine Datei von einer URL herunter"""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(local_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        return True
    except Exception as e:
        logger.error(f"Fehler beim Herunterladen: {str(e)}")
        return False

def main():
    logger.info("Star Citizen Griefing Counter Updater startet...")
    
    # URL zur Version und zum Download
    if not GITHUB_REPO_OWNER:
        logger.error("GitHub Repository Owner nicht verfügbar. Update wird abgebrochen.")
        input("Drücken Sie Enter, um den Updater zu beenden...")
        return
        
    version_url = f"https://{GITHUB_REPO_OWNER}.github.io/{GITHUB_REPO_NAME}/version.json"
    
    # Temporäres Verzeichnis
    temp_dir = "update_temp"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    
    # Version-Info herunterladen
    try:
        response = requests.get(version_url)
        response.raise_for_status()
        version_info = response.json()
        
        latest_version = version_info["latest_version"]
        download_url = version_info["download_url"]
        hash_url = f"{download_url}.sha256"
        
        logger.info(f"Neueste Version: {latest_version}")
        
        # Dateien herunterladen
        exe_local_path = os.path.join(temp_dir, "griefing_counter.exe")
        hash_local_path = os.path.join(temp_dir, "griefing_counter.exe.sha256")
        
        logger.info("Lade neue Version herunter...")
        if not download_file(download_url, exe_local_path):
            raise Exception("Download der EXE fehlgeschlagen!")
        
        logger.info("Lade Hash-Datei herunter...")
        if not download_file(hash_url, hash_local_path):
            raise Exception("Download der Hash-Datei fehlgeschlagen!")
        
        # Hash überprüfen
        with open(hash_local_path, 'r') as f:
            expected_hash = f.read().strip()
        
        actual_hash = get_sha256(exe_local_path)
        
        if actual_hash != expected_hash:
            raise Exception("SHA256-Hash stimmt nicht überein! Mögliche Manipulation der Datei.")
        
        logger.info("Hash erfolgreich verifiziert.")
        
        # Aktuelle EXE ermitteln
        current_exe = sys.executable
        if os.path.basename(current_exe) == "gc-updater.exe":
            main_exe = os.path.join(os.path.dirname(current_exe), "griefing_counter.exe")
        else:
            main_exe = current_exe
        
        # Bei Bedarf Programm beenden
        if os.path.exists(main_exe) and os.path.basename(main_exe) != "gc-updater.exe":
            try:
                for proc in os.popen('tasklist').readlines():
                    if "griefing_counter.exe" in proc.lower():
                        logger.info("Beende laufende Instanz...")
                        os.system('taskkill /f /im griefing_counter.exe')
                        time.sleep(2)
                        break
            except:
                logger.warning("Konnte laufende Instanz nicht automatisch beenden.")
                print("Bitte schließen Sie die Anwendung manuell und drücken Sie Enter...")
                input()
        
        # Datei ersetzen
        logger.info("Ersetze alte Version...")
        shutil.copy2(exe_local_path, main_exe)
        
        # Aufräumen
        shutil.rmtree(temp_dir)
        
        logger.info("Update erfolgreich abgeschlossen!")
        logger.info("Starte Griefing Counter...")
        
        # Starte die aktualisierte Anwendung
        subprocess.Popen([main_exe])
        
    except Exception as e:
        logger.error(f"Fehler beim Update: {str(e)}")
    
    print("Drücken Sie Enter, um den Updater zu beenden...")
    input()

if __name__ == "__main__":
    main()