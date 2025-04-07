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
import traceback
import ctypes
from datetime import datetime

# Einfaches Logging einrichten
log_dir = "Logs/updater"
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f"updater_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("GC-Updater")

# Der GitHub-Username und Repo-Name sollten in einer Konfigurationsdatei gespeichert
# oder zur Laufzeit durch GitHub Actions gesetzt werden
GITHUB_REPO_OWNER = "Eras308"  # Fester Fallback-Wert
if os.environ.get('GITHUB_REPOSITORY_OWNER'):
    GITHUB_REPO_OWNER = os.environ.get('GITHUB_REPOSITORY_OWNER')
    
GITHUB_REPO_NAME = "SC-Griefing-Counter"  # Verwende das Hauptrepo statt eines separaten Release-Repos

def is_admin():
    """Prüft, ob das Programm mit Administratorrechten läuft"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False

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
        logger.info(f"Versuche Download von: {url}")
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        with open(local_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        logger.info(f"Download erfolgreich: {local_path}")
        return True
    except Exception as e:
        logger.error(f"Fehler beim Herunterladen: {str(e)}")
        return False

def check_exe_integrity(exe_path):
    """Überprüft, ob die ausführbare Datei gültig ist"""
    if not os.path.exists(exe_path):
        logger.error(f"Datei existiert nicht: {exe_path}")
        return False
    
    if os.path.getsize(exe_path) < 1000:  # Minimale Größe für eine gültige EXE
        logger.error(f"Datei ist zu klein: {os.path.getsize(exe_path)} Bytes")
        return False
    
    # Versuche, die Datei zu öffnen (prüft auf Beschädigung)
    try:
        with open(exe_path, 'rb') as f:
            header = f.read(2)
            if header != b'MZ':  # DOS MZ header für ausführbare Dateien
                logger.error("Datei hat keinen gültigen EXE-Header")
                return False
    except Exception as e:
        logger.error(f"Fehler beim Lesen der Datei: {str(e)}")
        return False
    
    return True

def test_run_exe(exe_path):
    """Führt die EXE im Testmodus aus"""
    try:
        logger.info(f"Führe Test-Ausführung durch: {exe_path}")
        # Mit --version oder einem ähnlichen Parameter, der schnell zurückkehrt
        result = subprocess.run([exe_path, "--version"], 
                               capture_output=True, 
                               text=True, 
                               timeout=5)
        logger.info(f"Test-Ausführung Rückgabecode: {result.returncode}")
        logger.info(f"Ausgabe: {result.stdout}")
        if result.stderr:
            logger.warning(f"Fehlerausgabe: {result.stderr}")
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        logger.warning("Test-Ausführung Timeout - möglicherweise normal für GUI-Anwendung")
        return True  # Wir nehmen an, dass es funktioniert, wenn es nicht sofort zurückkehrt
    except Exception as e:
        logger.error(f"Fehler bei der Test-Ausführung: {str(e)}")
        return False

def extract_fallback_zip(zip_url, extract_dir):
    """Lädt die Zip-Datei herunter und extrahiert sie als Fallback"""
    try:
        import zipfile
        
        # Temporärer Dateiname für die Zip-Datei
        temp_zip = os.path.join(extract_dir, "temp_package.zip")
        
        # Zip-Datei herunterladen
        logger.info(f"Lade Fallback-Zip herunter: {zip_url}")
        if not download_file(zip_url, temp_zip):
            return False
        
        # Zip-Datei extrahieren
        logger.info(f"Extrahiere Zip nach: {extract_dir}")
        with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        # Aufräumen
        os.remove(temp_zip)
        
        return True
    except Exception as e:
        logger.error(f"Fehler beim Extrahieren der Zip-Datei: {str(e)}")
        return False

# Logging-Funktion für benutzerfreundliche Rückmeldungen
def log_message(message):
    print(message)

def main():
    try:
        logger.info("Star Citizen Griefing Counter Updater startet...")
        logger.info(f"Ausgeführt von: {sys.executable}")
        logger.info(f"Arbeitsverzeichnis: {os.getcwd()}")
        logger.info(f"Administratorrechte: {'Ja' if is_admin() else 'Nein'}")
        
        log_message("Starte Update-Prozess...\n")

        # URL zur Version und zum Download
        if not GITHUB_REPO_OWNER:
            logger.error("GitHub Repository Owner nicht verfügbar. Update wird abgebrochen.")
            input("Drücken Sie Enter, um den Updater zu beenden...")
            return
            
        # Verwende die GitHub Releases API statt GitHub Pages
        api_url = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/releases/latest"
        logger.info(f"API URL: {api_url}")
        
        # Temporäres Verzeichnis
        temp_dir = "update_temp"
        if os.path.exists(temp_dir):
            logger.info(f"Lösche vorhandenes temporäres Verzeichnis: {temp_dir}")
            shutil.rmtree(temp_dir)
        
        logger.info(f"Erstelle temporäres Verzeichnis: {temp_dir}")
        os.makedirs(temp_dir)
        
        # Release-Info herunterladen
        try:
            logger.info("Lade Release-Info...")
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            release_info = response.json()
            
            # Extrahiere Version aus dem Tag-Namen (v0.8.0 -> 0.8.0)
            latest_version = release_info["tag_name"]
            if latest_version.startswith('v'):
                latest_version = latest_version[1:]
            
            # Finde den Installer in den Assets
            installer_asset = None
            for asset in release_info["assets"]:
                if asset["name"].endswith(".exe") and "Setup" in asset["name"]:
                    installer_asset = asset
                    break
                    
            if not installer_asset:
                raise Exception("Keine Installer-Datei im Release gefunden!")
                
            download_url = installer_asset["browser_download_url"]
            
            # Finde die SHA256-Hash-Datei in den Assets
            hash_asset = None
            for asset in release_info["assets"]:
                if asset["name"].endswith(".sha256"):
                    hash_asset = asset
                    break
                    
            if not hash_asset:
                raise Exception("Keine SHA256-Hash-Datei im Release gefunden!")
                
            hash_url = hash_asset["browser_download_url"]
            
            # Fallback-ZIP-URL
            zip_asset = None
            for asset in release_info["assets"]:
                if asset["name"].endswith(".zip") and not "Source" in asset["name"]:
                    zip_asset = asset
                    break
                    
            zip_url = zip_asset["browser_download_url"] if zip_asset else None
            
            logger.info(f"Neueste Version: {latest_version}")
            logger.info(f"Download URL: {download_url}")
            logger.info(f"Hash URL: {hash_url}")
            logger.info(f"Zip URL (Fallback): {zip_url or 'Nicht verfügbar'}")
            
            log_message("1. Lade die neueste Version herunter...")
            # Dateien herunterladen
            exe_local_path = os.path.join(temp_dir, "griefing_counter.exe")
            hash_local_path = os.path.join(temp_dir, "griefing_counter.exe.sha256")
            
            logger.info("Lade neue Version herunter...")
            if not download_file(download_url, exe_local_path):
                raise Exception("Download der EXE fehlgeschlagen!")
            log_message(f"   -> Download erfolgreich: {exe_local_path}\n")
            
            log_message("2. Lade SHA256-Hash-Datei herunter...")
            logger.info("Lade Hash-Datei herunter...")
            if not download_file(hash_url, hash_local_path):
                raise Exception("Download der Hash-Datei fehlgeschlagen!")
            log_message(f"   -> Download erfolgreich: {hash_local_path}\n")
            
            log_message("3. Überprüfe Integrität der heruntergeladenen Datei...")
            # Hash überprüfen
            logger.info("Überprüfe Hash...")
            with open(hash_local_path, 'r') as f:
                expected_hash = f.read().strip()
            
            actual_hash = get_sha256(exe_local_path)
            logger.info(f"Erwarteter Hash: {expected_hash}")
            logger.info(f"Tatsächlicher Hash: {actual_hash}")
            
            log_message("   -> Integritätsprüfung wird durchgeführt...")
            if actual_hash != expected_hash:
                log_message("   -> Integritätsprüfung fehlgeschlagen! Die Datei könnte beschädigt oder manipuliert sein.")
                raise Exception("SHA256-Hash stimmt nicht überein! Mögliche Manipulation der Datei.")
            log_message("   -> Integritätsprüfung erfolgreich.\n")
            
            logger.info("Hash erfolgreich verifiziert.")
            
            # Überprüfe die Integrität der EXE
            if not check_exe_integrity(exe_local_path):
                logger.warning("Die heruntergeladene EXE könnte ungültig sein. Versuche Fallback mit ZIP...")
                # Versuche, die ZIP-Datei als Fallback zu verwenden
                if zip_url and extract_fallback_zip(zip_url, temp_dir):
                    # Suche nach der EXE in den entpackten Dateien
                    extracted_exe = None
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            if file.lower() == "griefing_counter.exe":
                                extracted_exe = os.path.join(root, file)
                                break
                    
                    if extracted_exe:
                        logger.info(f"Gefunden: {extracted_exe}")
                        exe_local_path = extracted_exe
                    else:
                        raise Exception("Konnte keine gültige EXE in der ZIP-Datei finden")
                else:
                    raise Exception("Fallback-Extraktion der ZIP-Datei fehlgeschlagen")
            
            # Führe einen Test der EXE durch
            test_run_exe(exe_local_path)
            
            # Aktuelle EXE ermitteln
            current_exe = sys.executable
            if os.path.basename(current_exe).lower() == "gc-updater.exe":
                main_exe = os.path.join(os.path.dirname(current_exe), "griefing_counter.exe")
            else:
                main_exe = current_exe
            
            logger.info(f"Aktuelle EXE: {main_exe}")
            
            # Bei Bedarf Programm beenden
            if os.path.exists(main_exe) and os.path.basename(main_exe).lower() != "gc-updater.exe":
                try:
                    logger.info("Suche nach laufenden Instanzen...")
                    found_process = False
                    for proc in os.popen('tasklist').readlines():
                        if "griefing_counter.exe" in proc.lower():
                            logger.info("Beende laufende Instanz...")
                            os.system('taskkill /f /im griefing_counter.exe')
                            found_process = True
                            time.sleep(2)
                            break
                    
                    if not found_process:
                        logger.info("Keine laufende Instanz gefunden.")
                except Exception as e:
                    logger.warning(f"Konnte laufende Instanz nicht automatisch beenden: {str(e)}")
                    print("Bitte schließen Sie die Anwendung manuell und drücken Sie Enter...")
                    input()
            
            log_message("4. Ersetze alte Version...")
            # Datei ersetzen
            logger.info(f"Ersetze alte Version: {main_exe}")
            
            try:
                # Sicherungskopie erstellen
                if os.path.exists(main_exe):
                    backup_path = f"{main_exe}.bak"
                    logger.info(f"Erstelle Sicherungskopie: {backup_path}")
                    shutil.copy2(main_exe, backup_path)
                    log_message(f"   -> Alte Version gesichert: {backup_path}")
                
                # Kopieren mit erhöhten Rechten wenn nötig
                shutil.copy2(exe_local_path, main_exe)
                logger.info("Datei erfolgreich ersetzt.")
                log_message("   -> Neue Version erfolgreich installiert.\n")
            except Exception as e:
                logger.error(f"Fehler beim Ersetzen der Datei: {str(e)}")
                if not is_admin():
                    logger.warning("Versuche mit Administrator-Rechten neu zu starten...")
                    
                    # Versuche, mit Admin-Rechten neu zu starten
                    if os.name == 'nt':  # Windows
                        try:
                            ctypes.windll.shell32.ShellExecuteW(
                                None, "runas", sys.executable, " ".join(sys.argv), None, 1
                            )
                            sys.exit(0)
                        except Exception as e:
                            logger.error(f"Konnte nicht mit Admin-Rechten neu starten: {str(e)}")
                    
                    print("Bitte führen Sie den Updater mit Administrator-Rechten aus.")
                    input("Drücken Sie Enter, um fortzufahren...")
                    return
            
            # Aufräumen
            logger.info(f"Räume temporäres Verzeichnis auf: {temp_dir}")
            shutil.rmtree(temp_dir)
            
            logger.info("Update erfolgreich abgeschlossen!")
            logger.info("Starte Griefing Counter...")
            
            log_message("5. Starte aktualisierte Anwendung...")
            # Starte die aktualisierte Anwendung
            try:
                subprocess.Popen([main_exe])
                logger.info("Anwendung gestartet.")
                log_message("   -> Anwendung erfolgreich gestartet.\n")
            except Exception as e:
                logger.error(f"Fehler beim Starten der Anwendung: {str(e)}")
                print(f"Fehler beim Starten der Anwendung. Details in der Log-Datei: {log_file}")
            
            log_message("Update abgeschlossen! Vielen Dank, dass Sie den SC Griefing Counter verwenden.")
            
        except Exception as e:
            logger.error(f"Fehler beim Update: {str(e)}")
            logger.error(traceback.format_exc())
            print(f"Ein Fehler ist aufgetreten. Details in der Log-Datei: {log_file}")
        
    except Exception as e:
        # Globaler Ausnahmefehler
        print(f"Kritischer Fehler: {str(e)}")
        if 'logger' in locals():
            logger.critical(f"Kritischer Fehler: {str(e)}")
            logger.critical(traceback.format_exc())
        else:
            with open("updater_critical_error.log", "w") as f:
                f.write(f"Kritischer Fehler: {str(e)}\n")
                f.write(traceback.format_exc())
    
    print(f"Die Log-Datei befindet sich unter: {log_file}")
    print("Drücken Sie Enter, um den Updater zu beenden...")
    input()

if __name__ == "__main__":
    main()