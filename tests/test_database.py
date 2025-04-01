import unittest
import sys
import os
import sqlite3
import tempfile

# Pfad zum Projektverzeichnis hinzufügen, damit die Module importiert werden können
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database
import config


class TestDatabase(unittest.TestCase):
    """Testklasse für Datenbank-Funktionen"""
    
    def setUp(self):
        """Testkonfiguration vorbereiten - temporäre DB erstellen"""
        # Original-DB-Pfad sichern
        self.original_db_folder = config.DB_FOLDER
        self.original_player_name = config.CURRENT_PLAYER_NAME
        
        # Temporäres Verzeichnis für Tests erstellen
        self.temp_dir = tempfile.TemporaryDirectory()
        config.DB_FOLDER = self.temp_dir.name
        config.CURRENT_PLAYER_NAME = "test_player"
        
        # Datenbank initialisieren
        database.init_db()
    
    def tearDown(self):
        """Testumgebung bereinigen"""
        # Originalkonfiguration wiederherstellen
        config.DB_FOLDER = self.original_db_folder
        config.CURRENT_PLAYER_NAME = self.original_player_name
        
        # Temporäres Verzeichnis löschen
        self.temp_dir.cleanup()
    
    def test_init_db(self):
        """Test für die Datenbankinitialisierung"""
        # DB sollte bereits in setUp initialisiert worden sein
        db_path = config.get_db_name()
        self.assertTrue(os.path.exists(db_path), "Datenbank-Datei wurde nicht erstellt")
        
        # Prüfen, ob alle erwarteten Tabellen vorhanden sind
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Tabellen auflisten
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        self.assertIn("kills", tables, "Tabelle 'kills' wurde nicht erstellt")
        self.assertIn("file_positions", tables, "Tabelle 'file_positions' wurde nicht erstellt")
        self.assertIn("npc_categories", tables, "Tabelle 'npc_categories' wurde nicht erstellt")
        
        conn.close()
    
    def test_execute_query(self):
        """Test für Ausführung von SQL-Abfragen"""
        # Test-Daten einfügen
        database.execute_query(
            "INSERT INTO kills (timestamp, killed_player, killer, zone, weapon, damage_class, damage_type) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("2025-03-01 12:00:00", "victim1", "test_player", "TestZone", "TestWeapon", "TestClass", "TestDamage")
        )
        
        # Daten abfragen
        result = database.fetch_query("SELECT COUNT(*) FROM kills")
        self.assertEqual(result[0][0], 1, "Datensatz wurde nicht korrekt eingefügt")
        
        # Daten mit Bedingung abfragen
        result = database.fetch_query(
            "SELECT killer FROM kills WHERE killed_player = ?",
            ("victim1",)
        )
        self.assertEqual(result[0][0], "test_player", "Abfrage liefert nicht die erwarteten Daten")
    
    def test_execute_many(self):
        """Test für Batch-Ausführung von SQL-Abfragen"""
        # Mehrere Test-Datensätze vorbereiten
        test_data = [
            ("2025-03-01 12:00:00", "victim1", "test_player", "TestZone", "TestWeapon", "TestClass", "TestDamage"),
            ("2025-03-01 12:01:00", "victim2", "test_player", "TestZone", "TestWeapon", "TestClass", "TestDamage"),
            ("2025-03-01 12:02:00", "victim3", "test_player", "TestZone", "TestWeapon", "TestClass", "TestDamage")
        ]
        
        # Batch-Ausführung testen
        database.execute_many(
            "INSERT INTO kills (timestamp, killed_player, killer, zone, weapon, damage_class, damage_type) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            test_data
        )
        
        # Ergebnis prüfen
        result = database.fetch_query("SELECT COUNT(*) FROM kills")
        self.assertEqual(result[0][0], 3, "Nicht alle Datensätze wurden eingefügt")
    
    def test_get_db_size_kb(self):
        """Test für die Datenbankgrößenberechnung"""
        # Einige Testdaten einfügen, um die DB-Größe zu erhöhen
        test_data = []
        for i in range(100):
            test_data.append((
                f"2025-03-01 12:{i:02d}:00", 
                f"victim{i}", 
                "test_player", 
                "TestZone", 
                "TestWeapon", 
                "TestClass", 
                "TestDamage"
            ))
        
        database.execute_many(
            "INSERT INTO kills (timestamp, killed_player, killer, zone, weapon, damage_class, damage_type) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            test_data
        )
        
        # DB-Größe prüfen
        size = database.get_db_size_kb()
        self.assertGreater(size, 0, "Datenbank-Größe sollte größer als 0 sein")


if __name__ == "__main__":
    unittest.main()