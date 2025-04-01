import tkinter as tk
from tkinter import ttk
import tkinter.font as tkFont
import threading
import time
import os
import webbrowser
import logging
from logging.handlers import RotatingFileHandler
from dataclasses import dataclass
from typing import List, Tuple
import config
import database
import log_processor
import stats
from watchdog_handler import start_watchdog
from datetime import datetime
from ui_constants import Colors, Fonts, WindowSettings, RefreshSettings
import logger

# Um den Kalender zu benutzen, benötigst du das Paket tkcalendar
# Installiere es mit: pip install tkcalendar
try:
    from tkcalendar import DateEntry
    CALENDAR_AVAILABLE = True
except ImportError:
    CALENDAR_AVAILABLE = False

# Setup logging
if config.LOGGING_ENABLED:
    logger.setup_logging(config.GENERAL_LOG_FOLDER, config.ERROR_LOG_FOLDER, config.DEBUG_LOG_FOLDER, config.LOGGING_LEVEL)
else:
    logging.getLogger().addHandler(logging.NullHandler())

# UI Constants
UI_CONSTANTS = {
    'WINDOW_SIZE': "1200x600",
    'FONT_FAMILY': "Helvetica",
    'FONT_SIZE': 10,
    'REFRESH_INTERVAL': 5,
}

@dataclass
class LeaderboardEntry:
    name: str
    count: int

class LeaderboardWidget(ttk.Frame):
    """Extracted Leaderboard component"""
    def __init__(self, parent, title: str, height: int = 10):
        super().__init__(parent)
        self.title = title
        self.setup_ui(height)

    def setup_ui(self, height: int):
        ttk.Label(self, text=f"{self.title} (Top 10):").pack(anchor="nw", pady=(0, 5))
        # Replace Listbox with Text widget for better formatting control
        self.text = tk.Text(
            self,
            height=height,
            cursor="arrow",
            font=tkFont.Font(family=UI_CONSTANTS['FONT_FAMILY'], 
                           size=UI_CONSTANTS['FONT_SIZE'])
        )
        self.text.pack(fill=tk.X, padx=5, pady=(0, 10))
        
        # Configure tags for different text styles
        self.text.tag_configure("hyperlink", 
                              foreground="blue",
                              underline=True,
                              font=tkFont.Font(family=UI_CONSTANTS['FONT_FAMILY'],
                                             size=UI_CONSTANTS['FONT_SIZE']))
        self.text.tag_configure("normal",
                              font=tkFont.Font(family=UI_CONSTANTS['FONT_FAMILY'],
                                             size=UI_CONSTANTS['FONT_SIZE']))
        
        self.text.bind("<Button-1>", self.on_click)
        self.text.config(state="disabled")
        
    def update_data(self, entries: List[LeaderboardEntry]):
        self.text.config(state="normal")
        self.text.delete("1.0", tk.END)
        for entry in entries:
            # Insert player name with hyperlink formatting
            self.text.insert(tk.END, entry.name, "hyperlink")
            # Insert kill count with normal formatting
            self.text.insert(tk.END, f"  {entry.count}\n", "normal")
        self.text.config(state="disabled")
    
    def on_click(self, event):
        """Handle click events on the text widget"""
        index = self.text.index(f"@{event.x},{event.y}")
        tags = self.text.tag_names(index)
        if "hyperlink" in tags:
            # Get the clicked line
            line_start = self.text.index(f"{index} linestart")
            line_end = self.text.index(f"{index} lineend")
            line = self.text.get(line_start, line_end)
            # Extract player name (everything before the last two space-separated items)
            player_name = line.split()[0]
            if self.winfo_toplevel().open_citizen_page:
                self.winfo_toplevel().open_citizen_page(player_name)

class GriefingCounterApp(tk.Tk):
    """
    Tkinter GUI mit:
    - Verbesserter Logimport-Statusanzeige
    - Countdown-Timer, der sich an der Refresh-Zeit orientiert
    - Zwei Leaderboards (Kill Leaderboard, Death Leaderboard) mit klickbaren (hyperlink-ähnlichen) Spielernamen
    - Recent Kill Events werden in einem Text-Widget angezeigt, wobei nur die Spielernamen als Hyperlinks formatiert werden
    - Priorisierte Verarbeitung: Zuerst wird die Live‑Log-Datei verarbeitet (sodass neue Events sofort angezeigt werden),
      Backup‑Logs werden asynchron in einem separaten Thread eingelesen.
    - Beim manuellen Refresh wird die Scrollposition beibehalten.
    """
    def __init__(self):
        super().__init__()
        self.title("Griefing Counter")
        self.geometry(WindowSettings.DEFAULT_SIZE)
        self.minsize(WindowSettings.MIN_WIDTH, WindowSettings.MIN_HEIGHT)
        
        # Initialize logging
        self.logger = logging.getLogger(__name__)
        
        # Initialisiere die Datenbank hier bereits
        database.init_db()
        
        # Speichere die aktiven Filter als Instanzvariablen
        # Setze standardmäßig kein Datum (Clear)
        self.active_start_date = None
        self.active_end_date = None
        
        # Initialize UI components
        self.setup_ui()
        self.setup_observers()

    def setup_ui(self):
        """Separate UI initialization"""
        self.setup_top_frame()
        self.setup_main_frame()
        self.setup_footer()

    def setup_footer(self):
        """Erstellt den Footer-Bereich mit Log- und DB-Informationen."""
        self.footer_frame = tk.Frame(self, height=20, bg="lightgrey")
        self.footer_frame.pack(side=tk.BOTTOM, fill=tk.X)

        # Labels für Logs und DB-Informationen
        self.logs_label = tk.Label(self.footer_frame, text="Gelesene Logs: 0", bg="lightgrey")
        self.logs_label.pack(side=tk.LEFT, padx=10)

        self.db_size_label = tk.Label(self.footer_frame, text="DB-Größe: 0 KB", bg="lightgrey")
        self.db_size_label.pack(side=tk.RIGHT, padx=10)

        # Initialisiere die Anzeige
        self.update_footer()

    def update_footer(self):
        """Aktualisiert die Informationen im Footer."""
        imported, total = log_processor.get_backup_log_progress()
        percent = (imported / total * 100) if total > 0 else 100
        db_size = database.get_db_size_kb()

        self.logs_label.config(text=f"Gelesene Logs: {imported}/{total} ({percent:.1f}%)")
        self.db_size_label.config(text=f"DB-Größe: {db_size:.1f} KB")

        # Aktualisiere den Footer regelmäßig
        self.after(5000, self.update_footer)

    def setup_top_frame(self):
        """Setup top frame UI components"""
        self.top_frame = tk.Frame(self)
        self.top_frame.pack(side=tk.TOP, fill=tk.X, pady=5)

        # Player Name
        ttk.Label(self.top_frame, text="Player Name:").pack(side=tk.LEFT, padx=5)
        self.var_player_name = tk.StringVar(value=config.CURRENT_PLAYER_NAME)
        self.entry_player_name = ttk.Entry(self.top_frame, textvariable=self.var_player_name, width=20)
        self.entry_player_name.pack(side=tk.LEFT, padx=5)

        self.btn_apply = ttk.Button(self.top_frame, text="Apply", command=self.on_apply_player_name)
        self.btn_apply.pack(side=tk.LEFT, padx=5)

        # Refresh Interval
        self.var_refresh_interval = tk.IntVar(value=config.REFRESH_INTERVAL)
        self.spin_refresh = ttk.Spinbox(
            self.top_frame, from_=RefreshSettings.MIN_INTERVAL, 
            to=RefreshSettings.MAX_INTERVAL, 
            textvariable=self.var_refresh_interval, width=5
        )
        self.spin_refresh.pack(side=tk.LEFT, padx=5)

        # Countdown Label
        self.var_countdown = tk.StringVar(value="Next refresh: -- sec")
        self.lbl_countdown = ttk.Label(self.top_frame, textvariable=self.var_countdown, 
                                       foreground=Colors.LOADING.value)
        self.lbl_countdown.pack(side=tk.LEFT, padx=10)

        # Manual Refresh Button
        self.btn_refresh = ttk.Button(self.top_frame, text="Manual Refresh", command=self.refresh_data)
        self.btn_refresh.pack(side=tk.LEFT, padx=5)

        # Progress (Log Import Status)
        self.var_progress = tk.StringVar(value="")
        self.lbl_progress = ttk.Label(self.top_frame, textvariable=self.var_progress, 
                                      foreground=Colors.PROGRESS.value)
        self.lbl_progress.pack(side=tk.LEFT, padx=10)

        # Erstelle einen Frame für die Datumsauswahl
        self.date_frame = ttk.LabelFrame(self.top_frame, text="Filter by Date")
        self.date_frame.pack(side=tk.LEFT, padx=10, fill=tk.X)

        # Start Date Selector
        start_date_frame = ttk.Frame(self.date_frame)
        start_date_frame.pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Label(start_date_frame, text="Start Date:").pack(side=tk.TOP, anchor="w")
        
        # End Date Selector
        end_date_frame = ttk.Frame(self.date_frame)
        end_date_frame.pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Label(end_date_frame, text="End Date:").pack(side=tk.TOP, anchor="w")
        
        # Verwende DateEntry, wenn verfügbar, sonst normale Entry-Widgets
        self.var_start_date = tk.StringVar()
        self.var_end_date = tk.StringVar()
        
        if CALENDAR_AVAILABLE:
            # Kalender-Widget für das Startdatum
            self.entry_start_date = DateEntry(
                start_date_frame, 
                width=12, 
                background='darkblue',
                foreground='white', 
                borderwidth=2,
                date_pattern='yyyy-mm-dd',
                textvariable=self.var_start_date
            )
            self.entry_start_date.pack(side=tk.TOP, padx=5, pady=2)
            # Setze das Datum auf leer (durch leeren der Variable)
            self.var_start_date.set("")
            
            # Kalender-Widget für das Enddatum
            self.entry_end_date = DateEntry(
                end_date_frame, 
                width=12, 
                background='darkblue',
                foreground='white', 
                borderwidth=2,
                date_pattern='yyyy-mm-dd',
                textvariable=self.var_end_date
            )
            self.entry_end_date.pack(side=tk.TOP, padx=5, pady=2)
            # Setze das Datum auf leer (durch leeren der Variable)
            self.var_end_date.set("")
            
        else:
            # Standard-Textfelder, wenn kein Kalender verfügbar ist
            self.entry_start_date = ttk.Entry(start_date_frame, textvariable=self.var_start_date, width=12)
            self.entry_start_date.pack(side=tk.TOP, padx=5, pady=2)
            ttk.Label(start_date_frame, text="(YYYY-MM-DD)", font=("Helvetica", 7)).pack(side=tk.TOP)
            
            self.entry_end_date = ttk.Entry(end_date_frame, textvariable=self.var_end_date, width=12)
            self.entry_end_date.pack(side=tk.TOP, padx=5, pady=2)
            ttk.Label(end_date_frame, text="(YYYY-MM-DD)", font=("Helvetica", 7)).pack(side=tk.TOP)

        # Filter Button
        self.btn_filter = ttk.Button(self.date_frame, text="Apply Filter", command=self.apply_date_filter)
        self.btn_filter.pack(side=tk.LEFT, padx=10, pady=5)
        
        # Clear Filter Button
        self.btn_clear_filter = ttk.Button(self.date_frame, text="Clear Filter", command=self.clear_date_filter)
        self.btn_clear_filter.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Entity Filter Frame für Spieler und NPC-Kategorien
        # Einen neuen separaten Frame für die Entity-Filter unter dem Date-Filter erstellen
        self.filter_section = tk.Frame(self)
        self.filter_section.pack(side=tk.TOP, fill=tk.X, pady=5, padx=10)
        
        # Entity-Filter-Frame
        self.entity_filter_frame = ttk.LabelFrame(self.filter_section, text="Entity Filter")
        self.entity_filter_frame.pack(fill=tk.X, padx=5)
        
        # Erstelle einen horizontalen Frame für alle Filter
        horizontal_filter_frame = tk.Frame(self.entity_filter_frame)
        horizontal_filter_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Wir verwenden Checkboxen für die Entity-Filter
        self.entity_filters = {}
        
        # Select All Filter
        self.var_select_all = tk.BooleanVar(value=True)
        select_all_cb = ttk.Checkbutton(horizontal_filter_frame, text="Select All", 
                       variable=self.var_select_all,
                       command=self.toggle_all_filters)
        select_all_cb.pack(side=tk.LEFT, padx=5)
        
        # Spieler-Filter
        self.var_players_filter = tk.BooleanVar(value=True)
        self.entity_filters["players"] = self.var_players_filter
        ttk.Checkbutton(horizontal_filter_frame, text="Players", 
                       variable=self.var_players_filter,
                       command=self.apply_entity_filter).pack(side=tk.LEFT, padx=5)
        
        # Unknown-Filter
        self.var_unknown_filter = tk.BooleanVar(value=True)
        self.entity_filters["unknown"] = self.var_unknown_filter
        ttk.Checkbutton(horizontal_filter_frame, text="Unknown", 
                       variable=self.var_unknown_filter,
                       command=self.apply_entity_filter).pack(side=tk.LEFT, padx=5)
        
        # Trennlinie
        ttk.Separator(horizontal_filter_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=10, fill='y')
        
        # NPC-Filter-Label
        ttk.Label(horizontal_filter_frame, text="NPCs:").pack(side=tk.LEFT, padx=5)
        
        # Alle NPC-Kategorien horizontal anordnen
        for category in config.NPC_CATEGORIES:
            var = tk.BooleanVar(value=True)
            self.entity_filters[f"npc_{category}"] = var
            ttk.Checkbutton(horizontal_filter_frame, text=category.capitalize(), 
                          variable=var,
                          command=self.apply_entity_filter).pack(side=tk.LEFT, padx=5)

    def apply_date_filter(self):
        """Apply date filter and refresh data."""
        start_date = self.var_start_date.get().strip()
        end_date = self.var_end_date.get().strip()
        
        self.logger.info(f"Anwenden des Datumfilters: Start={start_date}, Ende={end_date}")
        
        try:
            # Speichere die Datumsfilter in den Instanzvariablen
            self.active_start_date = datetime.strptime(start_date, '%Y-%m-%d') if start_date else None
            self.active_end_date = datetime.strptime(end_date, '%Y-%m-%d') if end_date else None
            self.logger.info(f"Verarbeitete Daten: Start={self.active_start_date}, Ende={self.active_end_date}")
        except ValueError as e:
            error_msg = f"Ungültiges Datumsformat: {str(e)}"
            self.logger.error(error_msg)
            self.show_error("Invalid date format. Use YYYY-MM-DD.")
            return
        
        self.logger.info("Starte Datenladung mit Filtern...")
        threading.Thread(target=self.load_data_with_filters, args=(self.active_start_date, self.active_end_date), daemon=True).start()

    def load_data_with_filters(self, start_date, end_date):
        """Load data with date filters."""
        try:
            # Hole aktuelle Entity-Filter
            entity_filters = {}
            for key, var in self.entity_filters.items():
                entity_filters[key] = var.get()
                
            self.logger.info(f"Lade Daten mit Filtern: Start={start_date}, Ende={end_date}, Entities={entity_filters}")
            stats_text, recent_text = stats.get_stats(start_date, end_date, entity_filters)
            self.logger.info("Statistiken erfolgreich geladen")
            
            # Status-Update in der GUI - direkt über die tkinter Variable aktualisieren
            self.var_stats.set(stats_text)

            # Update recent kill events - direkt in die GUI schreiben
            self.logger.info("Aktualisiere Recent Kill Events")
            self.kill_text.config(state="normal")
            self.kill_text.delete("1.0", tk.END)
            for line in recent_text.split("\n"):
                if line.lower().startswith("killer:"):
                    self.kill_text.insert(tk.END, "Killer: ", "normal")
                    name = line[len("Killer: "):].strip()
                    self.kill_text.insert(tk.END, name + "\n", "hyperlink")
                elif line.lower().startswith("killed:"):
                    self.kill_text.insert(tk.END, "Killed: ", "normal")
                    name = line[len("Killed: "):].strip()
                    self.kill_text.insert(tk.END, name + "\n", "hyperlink")
                else:
                    self.kill_text.insert(tk.END, line + "\n", "normal")
            self.kill_text.config(state="disabled")

            # Update leaderboards mit den aktuellen Filtern
            self.logger.info("Aktualisiere Leaderboards mit Filtern")
            kill_leaderboard, death_leaderboard = stats.get_leaderboards(start_date, end_date, entity_filters)
            # Aktualisiere die Anzeige explizit
            self.after(0, lambda: self.kill_leaderboard_widget.update_data([LeaderboardEntry(name, count) for name, count in kill_leaderboard]))
            self.after(0, lambda: self.death_leaderboard_widget.update_data([LeaderboardEntry(name, count) for name, count in death_leaderboard]))
            
            self.logger.info("Datenaktualisierung mit Filtern abgeschlossen")
        except Exception as e:
            self.logger.error(f"Fehler beim Laden von Daten mit Filtern: {str(e)}", exc_info=True)
            self.show_error(f"Failed to load data with filters: {str(e)}")

    def setup_main_frame(self):
        """Setup main frame UI components"""
        self.main_frame = tk.Frame(self)
        self.main_frame.pack(expand=True, fill=tk.BOTH)

        # Linke Spalte: Statistics
        self.left_frame = tk.Frame(self.main_frame)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)

        ttk.Label(self.left_frame, text="Statistics:").pack(anchor="nw")
        self.var_stats = tk.StringVar()
        self.lbl_stats = ttk.Label(
            self.left_frame, textvariable=self.var_stats, justify="left", anchor="nw", padding=(5, 5)
        )
        self.lbl_stats.pack(anchor="nw", fill=tk.BOTH, expand=True)

        # Mittlere Spalte: Leaderboards
        self.middle_frame = tk.Frame(self.main_frame)
        self.middle_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)

        self.kill_leaderboard_widget = LeaderboardWidget(self.middle_frame, "Kill Leaderboard")
        self.kill_leaderboard_widget.pack(fill=tk.X)

        self.death_leaderboard_widget = LeaderboardWidget(self.middle_frame, "Death Leaderboard")
        self.death_leaderboard_widget.pack(fill=tk.X)

        # Rechte Spalte: Recent Kill Events – jetzt in einem Text-Widget
        self.right_frame = tk.Frame(self.main_frame)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10)

        ttk.Label(self.right_frame, text="Recent 100 Kill Events:").pack(anchor="nw")

        self.kill_text_frame = tk.Frame(self.right_frame)
        self.kill_text_frame.pack(fill=tk.BOTH, expand=True)

        self.kill_text = tk.Text(self.kill_text_frame, wrap="word", height=20)
        self.kill_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        # Standardformatierung für normalen Text
        self.kill_text.tag_configure("normal", font=("Helvetica", 10))
        # Hyperlink-Tag: blau und unterstrichen
        self.kill_text.tag_configure("hyperlink", foreground="blue", underline=True)
        self.kill_text.config(state="disabled")
        self.kill_text.bind("<Button-1>", self.on_recent_event_click)

        self.scrollbar = ttk.Scrollbar(self.kill_text_frame, orient="vertical", command=self.kill_text.yview)
        self.kill_text.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def setup_observers(self):
        """Initialize observers and threads"""
        self.observer = None
        self.auto_refresh_running = False
        
        if config.CURRENT_PLAYER_NAME:
            try:
                threading.Thread(target=self.load_data, daemon=True).start()
                threading.Thread(target=self.auto_refresh_loop, daemon=True).start()
            except Exception as e:
                self.logger.error(f"Failed to initialize observers: {str(e)}")
                self.show_error("Failed to initialize application")

    def on_apply_player_name(self):
        """Neue Spielernamen übernehmen und alles neu initialisieren."""
        name = self.var_player_name.get().strip()
        if not name:
            return
        config.CURRENT_PLAYER_NAME = name
        config.save_config()

        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None

        threading.Thread(target=self.load_data, daemon=True).start()

    def start_loading_animation(self):
        """Diese Methode tut nichts mehr, da die Loading-Animation entfernt wurde."""
        pass

    def stop_loading_animation(self):
        """Diese Methode tut nichts mehr, da die Loading-Animation entfernt wurde."""
        pass

    def load_data(self):
        """Enhanced data loading with error handling"""
        try:
            live_log = os.path.join(config.LIVE_FOLDER, config.GAME_LOG_FILENAME)
            
            if not os.path.exists(live_log):
                self.logger.warning(f"Live log file not found: {live_log}")
                return
                
            log_processor.process_log_file(live_log)
            threading.Thread(target=log_processor.parse_all_backup_logs, daemon=True).start()
            
            # Hole die aktuellen Entity-Filter
            entity_filters = {}
            for key, var in self.entity_filters.items():
                entity_filters[key] = var.get()
                
            # Wende automatisch einen leeren Filter an (entspricht "Clear Filter"), 
            # damit die Daten direkt angezeigt werden
            self.active_start_date = None
            self.active_end_date = None
            
            # Wichtig: Wir rufen die Methode direkt auf und verwenden after(0), 
            # um zu gewährleisten, dass die GUI-Updates im Hauptthread erfolgen
            self.after(0, lambda: self.load_data_with_filters(None, None))
            
            # Update der Daten mit aktiven Filtern
            self.update_stats()
            self.update_progress_info()
            
            # Aktualisiere die Anzeige der aktiven Filter in den Eingabefeldern, falls sie von außen gesetzt wurden
            if self.active_start_date:
                self.var_start_date.set(self.active_start_date.strftime('%Y-%m-%d'))
            if self.active_end_date:
                self.var_end_date.set(self.active_end_date.strftime('%Y-%m-%d'))
        except Exception as e:
            self.logger.error(f"Error loading data: {str(e)}")
            self.show_error("Failed to load data")

    def refresh_data(self):
        """Manueller Refresh."""
        threading.Thread(target=self.load_data_with_scroll_memory, daemon=True).start()

    def load_data_with_scroll_memory(self):
        """Refresh-Daten laden und dabei die Scrollposition des Recent-Events-Text-Widgets beibehalten."""
        current_scroll = self.kill_text.yview()
        # Verwende die aktiven Filter auch beim manuellen Refresh
        self.load_data()
        self.kill_text.yview_moveto(current_scroll[0])

    def auto_refresh_loop(self):
        while True:
            interval = self.var_refresh_interval.get()
            self.current_countdown = interval + 1
            while self.current_countdown > 1:
                self.var_countdown.set(f"Next refresh: {self.current_countdown - 1} sec")
                time.sleep(1)
                new_interval = self.var_refresh_interval.get()
                if new_interval != interval:
                    interval = new_interval
                    self.current_countdown = interval + 1
                else:
                    self.current_countdown -= 1
            self.var_countdown.set("Refreshing...")
            self.refresh_data()

    def update_stats(self):
        """Aktualisiert Stats, Leaderboards und Recent Kill Events in der GUI."""
        # Hole aktuelle Entity-Filter
        entity_filters = {}
        for key, var in self.entity_filters.items():
            entity_filters[key] = var.get()
            
        # Verwende die gespeicherten Filter, falls vorhanden
        stats_text, recent_text = stats.get_stats(self.active_start_date, self.active_end_date, entity_filters)
        self.var_stats.set(stats_text)

        # Leaderboards aktualisieren mit den aktiven Filtern
        kill_leaderboard, death_leaderboard = stats.get_leaderboards(
            self.active_start_date, self.active_end_date, entity_filters)
            
        # Alle Leaderboard-Einträge anzeigen, ohne den Unknwon-Filter
        self.kill_leaderboard_widget.update_data([LeaderboardEntry(name, count) for name, count in kill_leaderboard])
        self.death_leaderboard_widget.update_data([LeaderboardEntry(name, count) for name, count in death_leaderboard])

        # Recent Kill Events in das Text-Widget einfügen, mit separater Formatierung:
        self.kill_text.config(state="normal")
        self.kill_text.delete("1.0", tk.END)
        # Wir verarbeiten die Zeilen einzeln, sodass nur die Spielernamen in den Zeilen "Killer:" und "Killed:" den Hyperlink-Tag bekommen.
        for line in recent_text.split("\n"):
            if line.lower().startswith("killer:"):
                self.kill_text.insert(tk.END, "Killer: ", "normal")
                name = line[len("Killer: "):].strip()
                self.kill_text.insert(tk.END, name + "\n", "hyperlink")
            elif line.lower().startswith("killed:"):
                self.kill_text.insert(tk.END, "Killed: ", "normal")
                name = line[len("Killed: "):].strip()
                self.kill_text.insert(tk.END, name + "\n", "hyperlink")
            else:
                self.kill_text.insert(tk.END, line + "\n", "normal")
        self.kill_text.config(state="disabled")

    def update_progress_info(self):
        """Entfernt die alte Anzeige der Logs und DB-Größe."""
        pass

    def open_citizen_page(self, player_name):
        """Öffnet die Citizen-Seite im Standard-Webbrowser für den gegebenen Spielernamen."""
        url = f"https://robertsspaceindustries.com/en/citizens/{player_name}"
        webbrowser.open(url)

    def on_leaderboard_item_click(self, event):
        """Handler für Doppelklick in den Leaderboard-Listboxes."""
        widget = event.widget
        selection = widget.curselection()
        if selection:
            index = selection[0]
            text = widget.get(index)
            # Format: "PlayerName  Count" – Spielername extrahieren
            player_name = text.split()[0]
            self.open_citizen_page(player_name)

    def on_recent_event_click(self, event):
        """Handler für Klick in der Recent Kill Events Text-Ansicht.
        Prüft, ob an der Klickposition das Tag 'hyperlink' gesetzt ist und öffnet dann die Citizen-Seite."""
        index = self.kill_text.index(f"@{event.x},{event.y}")
        tags = self.kill_text.tag_names(index)
        if "hyperlink" in tags:
            # Ermittle das Wort an dieser Position
            start = self.kill_text.search(r'\S+', index, regexp=True, backwards=True)
            end = self.kill_text.search(r'\s', index, regexp=True)
            if not end:
                end = tk.END
            player_name = self.kill_text.get(start, end).strip()
            self.open_citizen_page(player_name)

    def show_error(self, message: str):
        """Display error message to user"""
        # ...implement error dialog...
        pass

    def clear_date_filter(self):
        """Löscht die aktiven Filter und aktualisiert die Daten."""
        self.logger.info("Lösche aktive Datumsfilter")
        self.active_start_date = None
        self.active_end_date = None
        self.var_start_date.set("")
        self.var_end_date.set("")
        
        # Daten neu laden ohne Filter
        threading.Thread(target=self.load_data_with_filters, args=(None, None), daemon=True).start()

    def apply_entity_filter(self):
        """Wendet die ausgewählten Entity-Filter an und aktualisiert die Anzeige."""
        self.logger.info("Anwenden der Entity-Filter")
        
        # Erstelle ein Dictionary der aktuellen Filter-Zustände
        entity_filters = {}
        for key, var in self.entity_filters.items():
            entity_filters[key] = var.get()
            
        self.logger.info(f"Aktive Entity-Filter: {entity_filters}")
        
        # Starte Datenladung mit aktualisierten Filtern
        threading.Thread(target=self.load_data_with_all_filters, daemon=True).start()
    
    def load_data_with_all_filters(self):
        """Lädt Daten mit allen aktiven Filtern (Datum und Entity)."""
        try:
            # Erstelle Entity-Filter-Dictionary
            entity_filters = {}
            for key, var in self.entity_filters.items():
                entity_filters[key] = var.get()
                
            # Lade Daten mit allen Filtern
            self.logger.info(f"Lade Daten mit Filtern: Start={self.active_start_date}, Ende={self.active_end_date}, Entities={entity_filters}")
            stats_text, recent_text = stats.get_stats(self.active_start_date, self.active_end_date, entity_filters)
            
            # Aktualisiere die Anzeige
            self.var_stats.set(stats_text)
            
            # Aktualisiere Recent Kill Events
            self.kill_text.config(state="normal")
            self.kill_text.delete("1.0", tk.END)
            for line in recent_text.split("\n"):
                if line.lower().startswith("killer:"):
                    self.kill_text.insert(tk.END, "Killer: ", "normal")
                    name = line[len("Killer: "):].strip()
                    self.kill_text.insert(tk.END, name + "\n", "hyperlink")
                elif line.lower().startswith("killed:"):
                    self.kill_text.insert(tk.END, "Killed: ", "normal")
                    name = line[len("Killed: "):].strip()
                    self.kill_text.insert(tk.END, name + "\n", "hyperlink")
                else:
                    self.kill_text.insert(tk.END, line + "\n", "normal")
            self.kill_text.config(state="disabled")
            
            # Aktualisiere Leaderboards
            kill_leaderboard, death_leaderboard = stats.get_leaderboards(self.active_start_date, self.active_end_date, entity_filters)
            # Aktualisiere die Leaderboard-Widgets im Hauptthread
            self.after(0, lambda: self.kill_leaderboard_widget.update_data(
                [LeaderboardEntry(name, count) for name, count in kill_leaderboard]))
            self.after(0, lambda: self.death_leaderboard_widget.update_data(
                [LeaderboardEntry(name, count) for name, count in death_leaderboard]))
            
            self.logger.info("Datenaktualisierung mit allen Filtern abgeschlossen")
        except Exception as e:
            self.logger.error(f"Fehler beim Laden von Daten mit allen Filtern: {str(e)}", exc_info=True)
            self.show_error(f"Failed to load data with filters: {str(e)}")

    def toggle_all_filters(self):
        """Aktiviert oder deaktiviert alle Entity-Filter basierend auf der 'Select All'-Checkbox."""
        # Status aller Checkboxen auf den Wert der "Select All"-Checkbox setzen
        select_all_value = self.var_select_all.get()
        
        # Für alle Filter (Spieler, Unknown und NPC-Kategorien)
        for key, var in self.entity_filters.items():
            var.set(select_all_value)
            
        # Nach dem Ändern aller Filter die Daten aktualisieren
        self.apply_entity_filter()

def start_gui():
    """Entry point für die Tkinter-App."""
    app = GriefingCounterApp()
    app.mainloop()

if __name__ == "__main__":
    start_gui()
