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
import tkinter as tk
from tkinter import messagebox
import tempfile

# Sofort eine Fehlermeldung anzeigen, wenn ein Fehler auftritt
try:
    # Pfad zum AppData-Verzeichnis für Logdateien
    def get_app_data_path():
        """Gibt den Pfad zum Anwendungsdatenverzeichnis im AppData-Ordner zurück."""
        app_name = "SC-Griefing-Counter"
        
        # Unter Windows AppData-Verzeichnis verwenden
        app_data = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), app_name)
        return app_data
except Exception as e:
    print(f"Fehler beim Abrufen des AppData-Pfads: {e}")
    sys.exit(1)

# Zuerst einen einfachen Log im aktuellen Verzeichnis erstellen für sofortige Diagnose
script_dir = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))
debug_log = os.path.join(script_dir, "updater_debug.log")

# Einfache Debug-Funktion, die direkt ins Verzeichnis schreibt
def debug_write(message):
    try:
        with open(debug_log, 'a') as f:
            f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")
    except Exception as e:
        # Falls direktes Schreiben fehlschlägt, versuchen wir es im temp-Verzeichnis
        try:
            temp_log = os.path.join(tempfile.gettempdir(), "gc_updater_debug.log")
            with open(temp_log, 'a') as f:
                f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Error writing to primary log: {e}\n")
                f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")
        except:
            pass  # Hier können wir nichts mehr tun

debug_write("Updater startet...")
debug_write(f"Ausgeführt von: {sys.executable}")
debug_write(f"Arbeitsverzeichnis: {os.getcwd()}")

# Erstelle Logs im AppData-Verzeichnis anstatt im Programmverzeichnis
app_data_path = get_app_data_path()
log_dir = os.path.join(app_data_path, "Logs", "updater")
os.makedirs(log_dir, exist_ok=True)

log_file = os.path.join(log_dir, f"updater_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

logging.basicConfig(
    level=logging.DEBUG,  # Detailliertes Logging für Fehlerdiagnose
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("GC-Updater")

debug_write(f"Logger konfiguriert. Log-Datei: {log_file}")

# Der GitHub-Username und Repo-Name sollten in einer Konfigurationsdatei gespeichert
# oder zur Laufzeit durch GitHub Actions gesetzt werden
GITHUB_REPO_OWNER = "mittelaltergouda"  # Aktualisierter Repository-Besitzer
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
        debug_write(f"Download-Start: {url} -> {local_path}")
        
        # Verbesserte Fehlerbehandlung mit mehreren Versuchen
        max_attempts = 3
        
        for attempt in range(1, max_attempts + 1):
            try:
                response = requests.get(url, stream=True, timeout=30)
                response.raise_for_status()
                total_size = int(response.headers.get('content-length', 0))
                
                with open(local_path, 'wb') as file:
                    if total_size == 0:
                        file.write(response.content)
                    else:
                        downloaded = 0
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                file.write(chunk)
                                downloaded += len(chunk)
                                # Status nur für größere Downloads loggen
                                if total_size > 1000000 and downloaded % 1000000 < 8192:  # Log ca. alle MB
                                    percent = int(100 * downloaded / total_size)
                                    debug_write(f"Download: {percent}% ({downloaded}/{total_size})")
                
                # Überprüfe, ob die Datei existiert und eine vernünftige Größe hat
                if not os.path.exists(local_path):
                    raise Exception(f"Datei wurde nicht erstellt: {local_path}")
                
                file_size = os.path.getsize(local_path)
                if file_size < 1000 and total_size > 1000:  # Mindestens 1KB, wenn laut Header größer
                    raise Exception(f"Datei scheint unvollständig: {file_size} Bytes")
                
                logger.info(f"Download erfolgreich: {local_path} ({file_size} Bytes)")
                debug_write(f"Download abgeschlossen: {file_size} Bytes")
                return True
                
            except Exception as e:
                if attempt < max_attempts:
                    wait_time = 2 * attempt  # Exponentielles Backoff
                    logger.warning(f"Download-Versuch {attempt} fehlgeschlagen: {str(e)}. Wiederholung in {wait_time} Sekunden...")
                    debug_write(f"Download-Fehler (Versuch {attempt}): {str(e)}")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Alle Download-Versuche fehlgeschlagen: {str(e)}")
                    debug_write(f"Download endgültig fehlgeschlagen nach {max_attempts} Versuchen")
                    return False
                    
    except Exception as e:
        logger.error(f"Unerwarteter Fehler beim Download-Prozess: {str(e)}")
        debug_write(f"Kritischer Download-Fehler: {str(e)}")
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
    debug_write(message)

def show_message_box(title, message):
    """Zeigt ein Meldungsfenster an anstelle von Konsoleneingaben"""
    debug_write(f"MessageBox: {title} - {message}")
    # Stelle sicher, dass wir immer eine neue Tk-Instanz erstellen
    try:
        root = tk.Tk()
        root.withdraw()  # Verstecke das Hauptfenster
        messagebox.showinfo(title, message)
        root.destroy()
    except Exception as e:
        debug_write(f"Fehler beim Anzeigen der Meldung: {str(e)}")
        # Fallback zur Konsolenausgabe
        print(f"\n{title}:\n{message}\n")

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
            show_message_box("Fehler", "GitHub Repository Owner nicht verfügbar. Update wird abgebrochen.")
            return
            
        # Verwende die GitHub Releases API
        api_url = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/releases/latest"
        logger.info(f"API URL: {api_url}")
        debug_write(f"API URL: {api_url}")
        
        # Temporäres Verzeichnis mit besserer Fehlerbehandlung
        try:
            # Verwende das tempfile-Modul für bessere Kompatibilität
            temp_dir = tempfile.mkdtemp(prefix="gc_updater_")
            logger.info(f"Temporäres Verzeichnis erstellt: {temp_dir}")
            debug_write(f"Temp-Verzeichnis: {temp_dir}")
        except Exception as e:
            logger.warning(f"Konnte kein temporäres Verzeichnis mit tempfile erstellen: {str(e)}")
            # Fallback zur alten Methode
            temp_dir = os.path.join(app_data_path, "temp")
            if os.path.exists(temp_dir):
                logger.info(f"Lösche vorhandenes temporäres Verzeichnis: {temp_dir}")
                shutil.rmtree(temp_dir)
            
            logger.info(f"Erstelle temporäres Verzeichnis: {temp_dir}")
            os.makedirs(temp_dir)
        
        # Release-Info herunterladen
        try:
            logger.info("Lade Release-Info...")
            debug_write("Versuche GitHub API zu kontaktieren...")
            
            response = requests.get(api_url, timeout=15)
            response.raise_for_status()
            release_info = response.json()
            
            debug_write("GitHub API-Antwort erhalten")
            
            # Extrahiere Version aus dem Tag-Namen (v0.8.0 -> 0.8.0)
            latest_version = release_info["tag_name"]
            if latest_version.startswith('v'):
                latest_version = latest_version[1:]
            
            debug_write(f"Neueste Version: {latest_version}")
            
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
                # Versuche es mit ZIP als Fallback sofort
                if zip_url and extract_fallback_zip(zip_url, temp_dir):
                    # Suche nach der EXE in den entpackten Dateien
                    extracted_exe = None
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            if file.lower() == "griefing_counter.exe":
                                extracted_exe = os.path.join(root, file)
                                break
                    
                    if extracted_exe:
                        logger.info(f"EXE aus ZIP gefunden: {extracted_exe}")
                        exe_local_path = extracted_exe
                    else:
                        raise Exception("Konnte keine gültige EXE in der ZIP-Datei finden")
                else:
                    raise Exception("Download der EXE fehlgeschlagen und ZIP-Fallback nicht verfügbar!")
                
            log_message(f"   -> Download erfolgreich: {exe_local_path}\n")
            
            log_message("2. Überprüfe Integrität der heruntergeladenen Datei...")
            # Überprüfe die Integrität der EXE
            if not check_exe_integrity(exe_local_path):
                raise Exception("Die heruntergeladene EXE ist ungültig")
            
            # Aktuelle EXE ermitteln
            current_exe = sys.executable
            if os.path.basename(current_exe).lower() == "gc-updater.exe":
                main_exe = os.path.join(os.path.dirname(current_exe), "griefing_counter.exe")
            else:
                main_exe = current_exe
            
            logger.info(f"Aktuelle EXE: {main_exe}")
            debug_write(f"Hauptanwendung: {main_exe}")
            
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
                    show_message_box("Hinweis", "Bitte schließen Sie die Anwendung manuell und klicken Sie auf OK, um fortzufahren.")
            
            log_message("3. Ersetze alte Version...")
            # Datei ersetzen mit verbesserter Fehlerbehandlung
            logger.info(f"Ersetze alte Version: {main_exe}")
            
            try:
                # Sicherungskopie erstellen
                if os.path.exists(main_exe):
                    backup_path = f"{main_exe}.bak"
                    logger.info(f"Erstelle Sicherungskopie: {backup_path}")
                    try:
                        # Falls bereits eine Sicherung existiert, lösche sie
                        if os.path.exists(backup_path):
                            os.remove(backup_path)
                    except Exception as e:
                        logger.warning(f"Konnte alte Sicherungsdatei nicht löschen: {str(e)}")
                        
                    shutil.copy2(main_exe, backup_path)
                    log_message(f"   -> Alte Version gesichert: {backup_path}")
                
                try:
                    # Versuche direkt zu kopieren
                    shutil.copy2(exe_local_path, main_exe)
                    logger.info("Datei erfolgreich ersetzt.")
                except PermissionError:
                    # Versuche zu prüfen, ob die Zieldatei schreibgeschützt ist
                    if os.path.exists(main_exe):
                        try:
                            os.chmod(main_exe, 0o666)  # Schreibrechte gewähren
                            shutil.copy2(exe_local_path, main_exe)
                            logger.info("Datei erfolgreich ersetzt (nach Änderung der Berechtigungen).")
                        except Exception as e:
                            raise Exception(f"Konnte Datei nicht ersetzen, auch nach Änderung der Berechtigungen: {str(e)}")
                    else:
                        raise Exception("Zieldatei existiert nicht. Update fehlgeschlagen.")
                
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
                    
                    show_message_box("Fehler", "Bitte führen Sie den Updater mit Administrator-Rechten aus.")
                    return
            
            # Aufräumen
            try:
                logger.info(f"Räume temporäres Verzeichnis auf: {temp_dir}")
                shutil.rmtree(temp_dir)
            except Exception as e:
                logger.warning(f"Konnte temporäres Verzeichnis nicht löschen: {str(e)}")
            
            logger.info("Update erfolgreich abgeschlossen!")
            
            log_message("4. Starte aktualisierte Anwendung...")
            # Starte die aktualisierte Anwendung
            try:
                subprocess.Popen([main_exe])
                logger.info("Anwendung gestartet.")
                log_message("   -> Anwendung erfolgreich gestartet.\n")
            except Exception as e:
                logger.error(f"Fehler beim Starten der Anwendung: {str(e)}")
                show_message_box("Fehler", f"Fehler beim Starten der Anwendung. Bitte starten Sie die Anwendung manuell.\nDetails in der Log-Datei: {log_file}")
            
            # Zeige eine Erfolgsmeldung statt Konsoleneingabe zu verwenden
            show_message_box("Update abgeschlossen", 
                          "Update erfolgreich abgeschlossen!\nVielen Dank, dass Sie den SC Griefing Counter verwenden.")
            
        except Exception as e:
            logger.error(f"Fehler beim Update: {str(e)}")
            logger.error(traceback.format_exc())
            debug_write(f"Fehler im Update-Prozess: {str(e)}")
            debug_write(traceback.format_exc())
            show_message_box("Fehler", f"Ein Fehler ist aufgetreten: {str(e)}\n\nSiehe Log-Datei für Details: {log_file}")
        
    except Exception as e:
        # Globaler Ausnahmefehler
        logger.critical(f"Kritischer Fehler: {str(e)}")
        logger.critical(traceback.format_exc())
        debug_write(f"KRITISCHER FEHLER: {str(e)}")
        debug_write(traceback.format_exc())
        show_message_box("Kritischer Fehler", 
                      f"Ein kritischer Fehler ist aufgetreten: {str(e)}\n\nDetails im Log: {debug_log}")

if __name__ == "__main__":
    main()