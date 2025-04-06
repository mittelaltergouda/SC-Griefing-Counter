#!/usr/bin/env python
"""
Debug-Tool für den Star Citizen Griefing Counter
Dieses Skript versucht, die Anwendung zu starten und protokolliert Fehler
"""

import os
import sys
import traceback
import subprocess
import time
from datetime import datetime

# Erstelle Debug-Verzeichnis
debug_dir = "Logs/debug_launcher"
os.makedirs(debug_dir, exist_ok=True)
debug_log = os.path.join(debug_dir, f"launcher_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

with open(debug_log, "w") as log_file:
    try:
        log_file.write(f"=== Star Citizen Griefing Counter Debug Launcher ===\n")
        log_file.write(f"Zeitstempel: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        log_file.write(f"Arbeitsverzeichnis: {os.getcwd()}\n")
        log_file.write(f"Python-Version: {sys.version}\n")
        log_file.write(f"Plattform: {sys.platform}\n\n")
        
        # Suche nach der Hauptanwendung
        exe_path = "griefing_counter.exe"
        if not os.path.exists(exe_path):
            # Suche in aktuellen Verzeichnis
            files = os.listdir(".")
            log_file.write(f"Dateien im aktuellen Verzeichnis:\n")
            for file in files:
                log_file.write(f"  - {file}\n")
            
            log_file.write(f"\nHauptanwendung {exe_path} nicht gefunden! Prüfe Pfade...\n")
            
            # Prüfe einige andere mögliche Speicherorte
            possible_locations = [
                os.path.join("dist", "griefing_counter", "griefing_counter.exe"),
                os.path.join("dist", "griefing_counter.exe"),
                os.path.join("..", "griefing_counter.exe")
            ]
            
            for loc in possible_locations:
                log_file.write(f"Prüfe {loc}: {'Gefunden' if os.path.exists(loc) else 'Nicht gefunden'}\n")
                if os.path.exists(loc):
                    exe_path = loc
                    break
        
        if os.path.exists(exe_path):
            log_file.write(f"\nGefundene Anwendung: {exe_path}\n")
            log_file.write(f"Dateigröße: {os.path.getsize(exe_path)} Bytes\n")
            log_file.write(f"Letzte Änderung: {datetime.fromtimestamp(os.path.getmtime(exe_path))}\n\n")
            
            # Versuche, die Anwendung zu starten
            log_file.write(f"Versuche, die Anwendung zu starten...\n")
            
            try:
                # Methode 1: Direkter Start
                log_file.write("Methode 1: Direkter Start mit subprocess.Popen\n")
                process = subprocess.Popen([exe_path], 
                                          stdout=subprocess.PIPE, 
                                          stderr=subprocess.PIPE,
                                          universal_newlines=True)
                
                # Warte kurz und prüfe, ob der Prozess noch läuft
                time.sleep(2)
                if process.poll() is None:
                    log_file.write("  -> Prozess läuft noch nach 2 Sekunden (gut)\n")
                else:
                    stdout, stderr = process.communicate()
                    log_file.write(f"  -> Prozess hat sich beendet. Rückgabecode: {process.returncode}\n")
                    if stdout:
                        log_file.write(f"  -> Stdout: {stdout}\n")
                    if stderr:
                        log_file.write(f"  -> Stderr: {stderr}\n")
                
                # Warte etwas länger
                time.sleep(3)
                if process.poll() is None:
                    log_file.write("  -> Prozess läuft noch nach 5 Sekunden (gut)\n")
                    # Wir beenden den Prozess, falls er läuft
                    process.terminate()
                else:
                    stdout, stderr = process.communicate()
                    log_file.write(f"  -> Prozess hat sich beendet. Rückgabecode: {process.returncode}\n")
                    if stdout:
                        log_file.write(f"  -> Stdout: {stdout}\n")
                    if stderr:
                        log_file.write(f"  -> Stderr: {stderr}\n")
                
                # Methode 2: Start mit shell=True
                log_file.write("\nMethode 2: Start über Shell mit subprocess.call\n")
                result = subprocess.call(f'"{exe_path}"', shell=True)
                log_file.write(f"  -> Rückgabecode: {result}\n")
                
                # Methode 3: Start über os.system
                log_file.write("\nMethode 3: Start über os.system\n")
                result = os.system(f'"{exe_path}"')
                log_file.write(f"  -> Rückgabecode: {result}\n")
                
                # Methode 4: Start mit Befehlszeilenargumenten
                log_file.write("\nMethode 4: Start mit --debug Parameter\n")
                process = subprocess.Popen([exe_path, "--debug"], 
                                          stdout=subprocess.PIPE, 
                                          stderr=subprocess.PIPE,
                                          universal_newlines=True)
                
                time.sleep(2)
                stdout, stderr = process.communicate(timeout=3)
                log_file.write(f"  -> Rückgabecode: {process.returncode}\n")
                if stdout:
                    log_file.write(f"  -> Stdout: {stdout}\n")
                if stderr:
                    log_file.write(f"  -> Stderr: {stderr}\n")
                
            except Exception as e:
                log_file.write(f"Fehler beim Starten der Anwendung: {str(e)}\n")
                log_file.write(traceback.format_exc())
        else:
            log_file.write(f"Konnte die Hauptanwendung nicht finden!\n")
        
        # Prüfe auf DLL-Abhängigkeiten
        log_file.write("\n=== Prüfe DLL-Abhängigkeiten ===\n")
        try:
            # Verwende dumpbin (wenn verfügbar)
            dumpbin_result = subprocess.run(["dumpbin", "/DEPENDENTS", exe_path], 
                                          stdout=subprocess.PIPE, 
                                          stderr=subprocess.PIPE,
                                          universal_newlines=True,
                                          shell=True)
            
            if dumpbin_result.returncode == 0:
                log_file.write("dumpbin-Ausgabe:\n")
                log_file.write(dumpbin_result.stdout)
            else:
                log_file.write(f"dumpbin nicht verfügbar oder fehlgeschlagen: {dumpbin_result.stderr}\n")
                
                # Alternative: Suche nach DLLs im gleichen Verzeichnis
                exe_dir = os.path.dirname(os.path.abspath(exe_path))
                log_file.write(f"\nDateien im Anwendungsverzeichnis ({exe_dir}):\n")
                for file in os.listdir(exe_dir):
                    if file.lower().endswith(".dll"):
                        log_file.write(f"  - {file}\n")
        except Exception as e:
            log_file.write(f"Fehler bei der Abhängigkeitsprüfung: {str(e)}\n")
        
    except Exception as e:
        log_file.write(f"Kritischer Fehler im Debug-Tool: {str(e)}\n")
        log_file.write(traceback.format_exc())
    
    log_file.write("\n=== Debug-Sitzung abgeschlossen ===\n")

print(f"Debug-Informationen wurden in {debug_log} gespeichert.")
print("Bitte führen Sie dieses Skript aus dem Verzeichnis aus, in dem sich die griefing_counter.exe befindet.")
print("Drücken Sie Enter, um fortzufahren...")
input()