# SC Griefing Counter - Release Process

## Prerequisites

- GitHub account with write access to the repository
- Git client installed on local machine
- Up-to-date source code ready for release

## Release Process Overview

The release process is largely automated through GitHub Actions. The following steps are required:

1. Update version number in the codebase
2. Push code to GitHub
3. Create a Git tag for the new version
4. Push tag to GitHub (triggers automatic build process)
5. Monitor release status

## Detailed Instructions

### 1. Update Version Number

The version number must be updated in the `gui.py` file:

```python
APP_VERSION = "x.y.z"  # Replace x.y.z with the new version number
```

Also, you need to update the following files:
- The `CHANGELOG.md` file to include the changes for the new version. Add a new section following the format:
  ```
  ## [x.y.z] - YYYY-MM-DD
  ### Hinzugefügt
  - New feature 1
  - New feature 2
  
  ### Geändert
  - Changed feature 1
  - Changed feature 2
  
  ### Behoben
  - Fixed issue 1
  - Fixed issue 2
  ```
  The changelog entries should be based on the commits since the last release, but written in a user-friendly way that focuses on the benefits and improvements for the end user, not on technical implementation details.
- The `.github/workflows/build.yml` file under the "Create GitHub Release" section to include the relevant user-facing changes like UI improvements or new features. These changes should be summarized from the commit descriptions since the last release.
- The `SECURITY.md` file to update the supported versions table to include the new version.

### 2. Push Code to GitHub

After updating the version number, push your changes to GitHub:

```
git add gui.py
git commit -m "Updated version to x.y.z"
git push origin main
```

### 3. Create Git Tag

Create a Git tag that starts with "v" followed by the version number:

```
git tag -a vx.y.z -m "Release vx.y.z"
```

### 4. Push Tag to GitHub

Push the tag to GitHub to trigger the automatic build process:

```
git push origin vx.y.z
```

After this step, the GitHub Actions workflow will start automatically.

### 5. Monitor Release Status

You can track the status of the build in the "Actions" tab of the GitHub repository. After successful completion:

1. A new release will be created in the "Releases" section of the repository
2. The GitHub Pages will be updated with the new version
3. The version.json file will be updated for auto-updates

## If the Build Fails

If the automatic build process fails, you can take the following steps:

1. Check the error logs in the "Actions" tab
2. Fix the errors in the code
3. Delete the previous tag locally and remotely:
   ```
   git tag -d vx.y.z
   git push origin --delete vx.y.z
   ```
4. Create the tag again and push it again:
   ```
   git tag -a vx.y.z -m "Release vx.y.z"
   git push origin vx.y.z
   ```

## Automated Build Process

The automated build process performs the following steps:

1. Sets up a Windows build environment with Python 3.11
2. Installs all required dependencies
3. Extracts the version number from the Git tag
4. Creates a version.json file for the auto-updater
5. Compiles the program with PyInstaller
6. Generates a SHA256 hash of the executable
7. Creates an Inno Setup Installer
8. Creates ZIP archives with source code and compiled binaries
9. Publishes the release on GitHub Releases

## Build Process Outputs

The build process creates the following outputs:

1. **Windows Installer** (`SC-Griefing-Counter-Setup-x.y.z.exe`):
   - A complete installer with all required files
   - Creates desktop and start menu shortcuts

2. **Portable ZIP** (`SC-Griefing-Counter-x.y.z.zip`):
   - A ZIP archive with the compiled binaries
   - Can be extracted and run from any location

3. **Source Code ZIP** (`SC-Griefing-Counter-Source-x.y.z.zip`):
   - A ZIP archive with the complete source code

4. **SHA256 Hash**:
   - A file with the SHA256 hash of the executable for integrity verification

5. **version.json**:
   - A JSON file with information about the current version for the auto-updater

## Manual Execution of the Workflow

You can also trigger the build process manually through the "Actions" tab on GitHub without creating a new tag:

1. Go to the "Actions" tab
2. Select the "Build and Release Star Citizen Griefing Counter" workflow
3. Click on "Run workflow"
4. Select the branch and start the workflow

---

# SC Griefing Counter - Release-Prozess

## Voraussetzungen

- GitHub-Konto mit Schreibzugriff auf das Repository
- Git-Client auf lokalem Rechner installiert
- Aktueller Quellcode, der für den Release bereit ist

## Release-Prozess Übersicht

Der Release-Prozess ist weitgehend automatisiert durch GitHub Actions. Die folgenden Schritte sind erforderlich:

1. Versionsnummer in der Codebasis aktualisieren
2. Code auf GitHub pushen
3. Git-Tag für die neue Version erstellen
4. Tag auf GitHub pushen (löst automatischen Build-Prozess aus)
5. Release-Status überwachen

## Detaillierte Anleitung

### 1. Versionsnummer aktualisieren

Die Versionsnummer muss in der Datei `gui.py` aktualisiert werden:

```python
APP_VERSION = "x.y.z"  # Ersetze x.y.z durch die neue Versionsnummer
```

Zusätzlich müssen folgende Dateien aktualisiert werden:
- Die Datei `.github/workflows/build.yml` im Abschnitt "Create GitHub Release", um relevante benutzerrelevante Änderungen wie UI-Verbesserungen oder neue Funktionen aufzulisten. Diese Änderungen sollten aus den Commit-Beschreibungen seit dem letzten Release zusammengefasst werden.
- Die Datei `SECURITY.md`, um die Tabelle der unterstützten Versionen zu aktualisieren und die neue Version einzuschließen.

### 2. Code auf GitHub pushen

Nachdem Sie die Versionsnummer aktualisiert haben, pushen Sie Ihre Änderungen auf GitHub:

```
git add gui.py
git commit -m "Version auf x.y.z aktualisiert"
git push origin main
```

### 3. Git-Tag erstellen

Erstellen Sie einen Git-Tag, der mit "v" beginnt, gefolgt von der Versionsnummer:

```
git tag -a vx.y.z -m "Release vx.y.z"
```

### 4. Tag auf GitHub pushen

Pushen Sie den Tag auf GitHub, um den automatischen Build-Prozess auszulösen:

```
git push origin vx.y.z
```

Nach diesem Schritt wird der GitHub Actions Workflow automatisch gestartet.

### 5. Release-Status überwachen

Sie können den Status des Builds im "Actions"-Tab des GitHub-Repositories verfolgen. Nach erfolgreichem Abschluss:

1. Wird im "Releases"-Bereich des Repositories ein neuer Release erstellt
2. Die GitHub Pages werden aktualisiert mit der neuen Version
3. Die version.json-Datei wird aktualisiert für Auto-Updates

## Wenn der Build fehlschlägt

Wenn der automatische Build-Prozess fehlschlägt, können Sie folgende Schritte durchführen:

1. Prüfen Sie die Fehlerprotokolle im "Actions"-Tab
2. Beheben Sie die Fehler im Code
3. Löschen Sie den vorherigen Tag lokal und remote:
   ```
   git tag -d vx.y.z
   git push origin --delete vx.y.z
   ```
4. Erstellen Sie den Tag neu und pushen Sie ihn erneut:
   ```
   git tag -a vx.y.z -m "Release vx.y.z"
   git push origin vx.y.z
   ```

## Automatisierter Build-Prozess

Der automatisierte Build-Prozess führt folgende Schritte aus:

1. Setzt eine Windows-Build-Umgebung mit Python 3.11 auf
2. Installiert alle erforderlichen Abhängigkeiten
3. Extrahiert die Versionsnummer aus dem Git-Tag
4. Erstellt eine version.json-Datei für den Auto-Updater
5. Kompiliert das Programm mit PyInstaller
6. Generiert einen SHA256-Hash der ausführbaren Datei
7. Erstellt einen Inno Setup Installer
8. Erstellt ZIP-Archive mit Quellcode und kompilierten Binärdateien
9. Veröffentlicht das Release auf GitHub Releases

## Ausgaben des Build-Prozesses

Der Build-Prozess erstellt die folgenden Ausgaben:

1. **Windows Installer** (`SC-Griefing-Counter-Setup-x.y.z.exe`):
   - Ein vollständiger Installer mit allen erforderlichen Dateien
   - Erstellt Desktop- und Startmenüverknüpfungen

2. **Portable ZIP** (`SC-Griefing-Counter-x.y.z.zip`):
   - Ein ZIP-Archiv mit den kompilierten Binärdateien
   - Kann an einem beliebigen Ort entpackt und ausgeführt werden

3. **Quellcode ZIP** (`SC-Griefing-Counter-Source-x.y.z.zip`):
   - Ein ZIP-Archiv mit dem vollständigen Quellcode

4. **SHA256 Hash**:
   - Eine Datei mit dem SHA256-Hash der ausführbaren Datei zur Überprüfung der Integrität

5. **version.json**:
   - Eine JSON-Datei mit Informationen über die aktuelle Version für den Auto-Updater

## Manuelle Ausführung des Workflows

Sie können den Build-Prozess auch manuell über den "Actions"-Tab auf GitHub auslösen, ohne ein neues Tag zu erstellen:

1. Gehen Sie zum "Actions"-Tab
2. Wählen Sie den Workflow "Build und Release Star Citizen Griefing Counter"
3. Klicken Sie auf "Run workflow"
4. Wählen Sie den Branch aus und starten Sie den Workflow
