import unittest
import sys
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Pfad zum Projektverzeichnis hinzufügen, damit die Module importiert werden können
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import log_processor
import config
import database


class TestLogProcessor(unittest.TestCase):
    """Testklasse für Log-Verarbeitungsfunktionen"""
    
    def setUp(self):
        """Testkonfiguration vorbereiten"""
        # Original-Konfiguration sichern
        self.original_db_folder = config.DB_FOLDER
        self.original_player_name = config.CURRENT_PLAYER_NAME
        
        # Temporäre Verzeichnisse für Tests erstellen
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_logs_dir = os.path.join(self.temp_dir.name, "logs")
        self.temp_backup_dir = os.path.join(self.temp_dir.name, "backups")
        os.makedirs(self.temp_logs_dir, exist_ok=True)
        os.makedirs(self.temp_backup_dir, exist_ok=True)
        
        # Konfiguration für Tests anpassen
        config.DB_FOLDER = self.temp_dir.name
        config.CURRENT_PLAYER_NAME = "test_player"
        config.LIVE_FOLDER = self.temp_logs_dir
        config.BACKUP_FOLDER = self.temp_backup_dir
        
        # Datenbank initialisieren
        database.init_db()
    
    def tearDown(self):
        """Testumgebung bereinigen"""
        # Originalkonfiguration wiederherstellen
        config.DB_FOLDER = self.original_db_folder
        config.CURRENT_PLAYER_NAME = self.original_player_name
        
        # Temporäres Verzeichnis löschen
        self.temp_dir.cleanup()
    
    def test_parse_log_line(self):
        """Test für das Parsen einer einzelnen Log-Zeile"""
        # Gültige Log-Zeile
        valid_log_line = "<2025-03-01 12:00:00> [SC] <Actor Death> An Actor died! 'victim1' [123] in zone 'TestZone' killed by 'test_player' [456] using 'TestWeapon' [Class TestClass] with damage type 'TestDamage'"
        
        # Ungültige Log-Zeile
        invalid_log_line = "<2025-03-01 12:00:00> [SC] Some other log message that doesn't match the pattern"
        
        # Test gültige Zeile
        result = log_processor.parse_log_line(valid_log_line)
        self.assertIsNotNone(result, "Gültige Log-Zeile wurde nicht erkannt")
        self.assertEqual(result["killed_player"], "victim1", "Falscher killed_player-Wert")
        self.assertEqual(result["killer"], "test_player", "Falscher killer-Wert")
        self.assertEqual(result["zone"], "TestZone", "Falsche Zone")
        self.assertEqual(result["weapon"], "TestWeapon", "Falsche Waffe")
        self.assertEqual(result["class"], "TestClass", "Falsche Klasse")
        self.assertEqual(result["damage_type"], "TestDamage", "Falscher Schadenstyp")
        
        # Test ungültige Zeile
        result = log_processor.parse_log_line(invalid_log_line)
        self.assertIsNone(result, "Ungültige Log-Zeile wurde fälschlicherweise erkannt")
    
    def test_process_log_file(self):
        """Test für die Verarbeitung einer Log-Datei"""
        # Eine Test-Log-Datei erstellen
        test_log_path = os.path.join(self.temp_logs_dir, config.GAME_LOG_FILENAME)
        with open(test_log_path, "w") as f:
            f.write("<2025-03-01 12:00:00> [SC] Some irrelevant log message\n")
            f.write("<2025-03-01 12:01:00> [SC] <Actor Death> An Actor died! 'victim1' [123] in zone 'TestZone' killed by 'test_player' [456] using 'TestWeapon' [Class TestClass] with damage type 'TestDamage'\n")
            f.write("<2025-03-01 12:02:00> [SC] <Actor Death> An Actor died! 'test_player' [456] in zone 'TestZone' killed by 'enemy1' [789] using 'EnemyWeapon' [Class EnemyClass] with damage type 'EnemyDamage'\n")
            f.write("<2025-03-01 12:03:00> [SC] <Actor Death> An Actor died! 'other1' [111] in zone 'OtherZone' killed by 'other2' [222] using 'OtherWeapon' [Class OtherClass] with damage type 'OtherDamage'\n")
        
        # Log-Datei verarbeiten
        log_processor.process_log_file(test_log_path)
        
        # Prüfen, ob die relevanten Ereignisse in der Datenbank gespeichert wurden
        result = database.fetch_query("SELECT COUNT(*) FROM kills")
        self.assertEqual(result[0][0], 2, "Es sollten genau 2 Kill-Ereignisse gespeichert werden")
        
        # Prüfen, ob die Dateiposition gespeichert wurde
        result = database.fetch_query(
            "SELECT last_offset FROM file_positions WHERE file_path = ?",
            (test_log_path,)
        )
        self.assertIsNotNone(result, "Dateiposition wurde nicht gespeichert")
        self.assertGreater(result[0][0], 0, "Dateiposition sollte größer als 0 sein")
    
    def test_get_backup_log_progress(self):
        """Test für die Fortschrittsberechnung bei Backup-Logs"""
        # Einige Test-Backup-Logs erstellen
        backup_logs = ["backup1.log", "backup2.log", "backup3.log"]
        for log_name in backup_logs:
            with open(os.path.join(self.temp_backup_dir, log_name), "w") as f:
                f.write("Some test content\n")
        
        # Für einige Logs Dateiposition speichern
        database.execute_query(
            "INSERT INTO file_positions (file_path, last_offset) VALUES (?, ?)",
            (os.path.join(self.temp_backup_dir, backup_logs[0]), 10)
        )
        database.execute_query(
            "INSERT INTO file_positions (file_path, last_offset) VALUES (?, ?)",
            (os.path.join(self.temp_backup_dir, backup_logs[1]), 20)
        )
        
        # Fortschritt abrufen
        imported, total = log_processor.get_backup_log_progress()
        
        # Prüfen
        self.assertEqual(total, 3, "Insgesamt sollten 3 Backup-Logs erkannt werden")
        self.assertEqual(imported, 2, "2 Logs sollten als importiert gezählt werden")
    
    @patch('npc_handler.save_npc_category')
    def test_npc_categorization(self, mock_save_category):
        """Test für die automatische NPC-Kategorisierung während der Logverarbeitung"""
        # Eine Test-Log-Datei mit NPC-Ereignissen erstellen
        test_log_path = os.path.join(self.temp_logs_dir, config.GAME_LOG_FILENAME)
        with open(test_log_path, "w") as f:
            f.write("<2025-03-01 12:01:00> [SC] <Actor Death> An Actor died! 'pu_human_enemy_npc_pilot_123' [123] in zone 'TestZone' killed by 'test_player' [456] using 'TestWeapon' [Class TestClass] with damage type 'TestDamage'\n")
            f.write("<2025-03-01 12:02:00> [SC] <Actor Death> An Actor died! 'test_player' [456] in zone 'TestZone' killed by 'vlk_enemy_456' [789] using 'EnemyWeapon' [Class EnemyClass] with damage type 'EnemyDamage'\n")
        
        # Log-Datei verarbeiten
        log_processor.process_log_file(test_log_path)
        
        # Prüfen, ob die NPC-Kategorisierungsfunktion aufgerufen wurde
        # Dies sollte zweimal aufgerufen werden (für jeden NPC)
        self.assertEqual(mock_save_category.call_count, 2, "NPC-Kategorisierungsfunktion wurde nicht korrekt aufgerufen")


if __name__ == "__main__":
    unittest.main()