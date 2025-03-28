# SC-Griefing-Counter

## Einführung
Der SC-Griefing-Counter ist ein Tool, das entwickelt wurde, um Spieleraktivitäten in Star Citizen zu verfolgen und zu analysieren. Es bietet Funktionen wie das Zählen von Kills, das Verfolgen von Statistiken und das Anzeigen von Leaderboards. Dieses Tool ist besonders nützlich für Spieler, die ihre Performance überwachen oder detaillierte Berichte über ihre Aktivitäten erstellen möchten.

## Voraussetzungen
Um den SC-Griefing-Counter nutzen zu können, benötigen Sie:
- **Python 3.12** oder höher
- Die folgenden Python-Bibliotheken:
  - `tkinter`
  - `logging`
  - `sqlite3`
  - `watchdog`
  - `tkcalendar` (optional, für die Datumsauswahl)

## Installation
1. **Python installieren**: Stellen Sie sicher, dass Python 3.12 oder höher auf Ihrem System installiert ist. Sie können Python von [python.org](https://www.python.org/) herunterladen.
2. **Abhängigkeiten installieren**: Installieren Sie die benötigten Bibliotheken mit folgendem Befehl:
   ```bash
   pip install watchdog tkcalendar
   ```

## Starten des Programms
1. **Batch-Datei ausführen**:
   - Doppelklicken Sie auf die Datei `y_start_griefing_counter.bat`, um das Programm zu starten.
   - Alternativ können Sie das Programm auch direkt über die Kommandozeile starten:
     ```bash
     python griefing_counter_tk.py
     ```
2. **Programmoberfläche**:
   - Nach dem Start öffnet sich eine grafische Benutzeroberfläche (GUI), in der Sie die verschiedenen Funktionen des Tools nutzen können.

## Funktionen
- **Kill- und Death-Tracking**:
  - Verfolgen Sie Ihre Kills und Deaths in Star Citizen.
  - Anzeigen von Leaderboards mit den besten Spielern.

- **Statistiken und Berichte**:
  - Erstellen Sie detaillierte Berichte über Ihre Aktivitäten.
  - Filtern Sie Daten nach Datum und anderen Kriterien.

- **Live-Log-Verarbeitung**:
  - Das Tool überwacht Ihre Star Citizen-Logs in Echtzeit und aktualisiert die Statistiken automatisch.

## Hinweise
- **Konfigurationsdatei**:
  - Die Datei `config.txt` enthält benutzerspezifische Einstellungen wie den Spielernamen und Logging-Optionen.
  - Diese Datei wird automatisch erstellt, falls sie nicht existiert.

- **Datenbank**:
  - Alle Daten werden in einer SQLite-Datenbank gespeichert, die sich im Ordner `databases/` befindet.

- **Logs**:
  - Fehler- und Aktivitätslogs werden im Ordner `Logs/` gespeichert.

## Support
Falls Sie Fragen oder Probleme haben, wenden Sie sich bitte an den Entwickler oder konsultieren Sie die Dokumentation.