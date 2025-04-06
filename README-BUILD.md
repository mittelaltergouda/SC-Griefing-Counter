# SC Griefing Counter - Release-Prozess

Diese Dokumentation beschreibt den Prozess zum Erstellen eines neuen Releases für den Star Citizen Griefing Counter.

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
5. Wendet PyArmor an, um den Code zu obfuskieren
6. Kompiliert das Programm mit Nuitka (Fallback: PyInstaller)
7. Generiert einen SHA256-Hash der ausführbaren Datei
8. Erstellt ein ZIP-Archiv mit allen erforderlichen Dateien
9. Veröffentlicht das Release auf GitHub Releases
10. Aktualisiert die GitHub Pages mit der neuen Version

## Bekannte Probleme und Lösungen

### Problem: Nuitka-Kompilierung schlägt fehl

Wenn die Nuitka-Kompilierung mit einem Fehler fehlschlägt, überprüfen Sie die Fehlerprotokolle. Häufige Probleme sind:

- Falsche Parameter für Nuitka (--windows-console-mode vs. --windows-disable-console)
- Fehlende Abhängigkeiten
- Probleme mit dem MinGW64-Compiler

Der Build-Prozess wird automatisch auf PyInstaller zurückfallen, wenn Nuitka fehlschlägt.

## Manuelle Ausführung des Workflows

Sie können den Build-Prozess auch manuell über den "Actions"-Tab auf GitHub auslösen, ohne ein neues Tag zu erstellen:

1. Gehen Sie zum "Actions"-Tab
2. Wählen Sie den Workflow "Build und Release Star Citizen Griefing Counter"
3. Klicken Sie auf "Run workflow"
4. Wählen Sie den Branch aus und starten Sie den Workflow

---

Diese Dokumentation wurde zuletzt am 6. April 2025 aktualisiert.