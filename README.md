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