# SC-Griefing-Counter

## License
The use of this tool is subject to the terms of the license described in the [LICENSE.txt](./LICENSE.txt) file.

## Introduction
The SC-Griefing-Counter is a tool developed to track and analyze player activities in Star Citizen. It offers features such as kill counting, statistics tracking, and leaderboard displays. This tool is particularly useful for players who want to monitor their performance or create detailed reports about their activities.

## Privacy
**Important**: All user data is stored exclusively locally on your computer and is never transmitted to external servers. The SC-Griefing-Counter respects your privacy and works without an internet connection, except for optional update checks.

## Requirements
To use the SC-Griefing-Counter, you need either:
- The pre-compiled .exe file or installer from the latest release
- OR
- **Python 3.12** or higher and the following Python libraries:
  - `tkinter`
  - `logging`
  - `sqlite3`
  - `watchdog`
  - `tkcalendar` (optional, for date selection)

## Installation
1. **Installer Version (recommended)**:
   - Download the latest version of the installer (`SC-Griefing-Counter-Setup-x.x.x.exe`) from the [releases page](https://github.com/YourRepo/SC-Griefing-Counter/releases).
   - Run the installer and follow the on-screen instructions.
   - A shortcut will be created on the desktop and in the start menu.

2. **Portable Version**:
   - Download the ZIP archive (`SC-Griefing-Counter-x.x.x.zip`) from the [releases page](https://github.com/YourRepo/SC-Griefing-Counter/releases).
   - Extract the archive to any location.
   - Start the application by double-clicking on `griefing_counter.exe`.

3. **Source Code Version**:
   - Make sure Python 3.12 or higher is installed on your system. You can download Python from [python.org](https://www.python.org/).
   - Install the required libraries with the following command:
     ```bash
     pip install watchdog tkcalendar
     ```
   - Clone or download the repository.
   - Run the `y_start_griefing_counter.bat` file or start the program directly from the command line:
     ```bash
     python griefing_counter_tk.py
     ```

## Starting the Program
1. **Installed Version**:
   - Click on the desktop shortcut or find the application in the start menu.

2. **Portable Version**:
   - Navigate to the directory where you extracted the program.
   - Double-click on the `griefing_counter.exe` file.

3. **Source Code Version**:
   - Run the `y_start_griefing_counter.bat` file.
   - Alternatively, you can start the program directly from the command line:
     ```bash
     python griefing_counter_tk.py
     ```

## Features
- **Kill and Death Tracking**:
  - Track your kills and deaths in Star Citizen.
  - View leaderboards with the best players.

- **Statistics and Reports**:
  - Create detailed reports about your activities.
  - Filter data by date and other criteria.

- **Live Log Processing**:
  - The tool monitors your Star Citizen logs in real-time and updates statistics automatically.

## Notes
- **Configuration File**:
  - The `config.txt` file contains user-specific settings such as player name and logging options.
  - This file is created automatically if it does not exist.

- **Database**:
  - All data is stored in a SQLite database located in the `databases/` folder.
  - **Privacy**: Your data is stored exclusively locally and never transmitted to external servers.

- **Logs**:
  - Error and activity logs are saved in the `Logs/` folder.

- **Automatic Updates**:
  - The application can check for updates when an internet connection is available.
  - The update must be manually confirmed and no data is transmitted without your consent.

## Support
If you have questions or issues, please contact the developer or consult the documentation.

---

# SC-Griefing-Counter

## Lizenz
Die Nutzung dieses Tools unterliegt den Bedingungen der Lizenz, die in der Datei [LICENSE.txt](./LICENSE.txt) beschrieben ist.

## Einführung
Der SC-Griefing-Counter ist ein Tool, das entwickelt wurde, um Spieleraktivitäten in Star Citizen zu verfolgen und zu analysieren. Es bietet Funktionen wie das Zählen von Kills, das Verfolgen von Statistiken und das Anzeigen von Leaderboards. Dieses Tool ist besonders nützlich für Spieler, die ihre Performance überwachen oder detaillierte Berichte über ihre Aktivitäten erstellen möchten.

## Datenschutz
**Wichtig**: Alle Nutzerdaten werden ausschließlich lokal auf Ihrem Computer gespeichert und zu keinem Zeitpunkt an externe Server übermittelt. Der SC-Griefing-Counter respektiert Ihre Privatsphäre und arbeitet ohne Internetverbindung, außer für optionale Update-Prüfungen.

## Voraussetzungen
Um den SC-Griefing-Counter nutzen zu können, benötigen Sie entweder:
- Die vorkompilierte .exe-Datei oder den Installer aus dem neuesten Release
- ODER
- **Python 3.12** oder höher und die folgenden Python-Bibliotheken:
  - `tkinter`
  - `logging`
  - `sqlite3`
  - `watchdog`
  - `tkcalendar` (optional, für die Datumsauswahl)

## Installation
1. **Installer-Version (empfohlen)**:
   - Laden Sie die neueste Version des Installers (`SC-Griefing-Counter-Setup-x.x.x.exe`) von der [Releases-Seite](https://github.com/IhreRepo/SC-Griefing-Counter/releases) herunter.
   - Führen Sie den Installer aus und folgen Sie den Anweisungen auf dem Bildschirm.
   - Eine Verknüpfung wird auf dem Desktop und im Startmenü erstellt.

2. **Portable Version**:
   - Laden Sie das ZIP-Archiv (`SC-Griefing-Counter-x.x.x.zip`) von der [Releases-Seite](https://github.com/IhreRepo/SC-Griefing-Counter/releases) herunter.
   - Entpacken Sie das Archiv an einen beliebigen Ort.
   - Starten Sie die Anwendung durch Doppelklick auf `griefing_counter.exe`.

3. **Quellcode-Version**:
   - Stellen Sie sicher, dass Python 3.12 oder höher auf Ihrem System installiert ist. Sie können Python von [python.org](https://www.python.org/) herunterladen.
   - Installieren Sie die benötigten Bibliotheken mit folgendem Befehl:
     ```bash
     pip install watchdog tkcalendar
     ```
   - Klonen oder laden Sie das Repository herunter.
   - Führen Sie die Datei `y_start_griefing_counter.bat` aus oder starten Sie das Programm direkt über die Kommandozeile:
     ```bash
     python griefing_counter_tk.py
     ```

## Starten des Programms
1. **Installierte Version**:
   - Klicken Sie auf die Desktop-Verknüpfung oder finden Sie die Anwendung im Startmenü.

2. **Portable Version**:
   - Navigieren Sie zum Verzeichnis, in dem Sie das Programm entpackt haben.
   - Doppelklicken Sie auf die Datei `griefing_counter.exe`.

3. **Quellcode-Version**:
   - Führen Sie die Datei `y_start_griefing_counter.bat` aus.
   - Alternativ können Sie das Programm auch direkt über die Kommandozeile starten:
     ```bash
     python griefing_counter_tk.py
     ```

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
  - **Datenschutz**: Ihre Daten werden ausschließlich lokal gespeichert und niemals an externe Server übertragen.

- **Logs**:
  - Fehler- und Aktivitätslogs werden im Ordner `Logs/` gespeichert.

- **Automatische Updates**:
  - Die Anwendung kann nach Updates suchen, wenn eine Internetverbindung besteht.
  - Das Update muss manuell bestätigt werden und es werden keine Daten ohne Ihre Zustimmung übertragen.

## Support
Falls Sie Fragen oder Probleme haben, wenden Sie sich bitte an den Entwickler oder konsultieren Sie die Dokumentation.
