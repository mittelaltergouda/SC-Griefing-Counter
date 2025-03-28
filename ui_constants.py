"""UI Constants and Configuration"""
from enum import Enum

class Colors(Enum):
    HYPERLINK = "blue"
    PROGRESS = "green"
    LOADING = "blue"

class Fonts:
    DEFAULT_FAMILY = "Helvetica"
    DEFAULT_SIZE = 10
    
class WindowSettings:
    DEFAULT_SIZE = "1200x600"  # Größere Standardgröße für bessere Darstellung aller Elemente
    MIN_WIDTH = 800
    MIN_HEIGHT = 600

class RefreshSettings:
    DEFAULT_INTERVAL = 10
    MIN_INTERVAL = 1
    MAX_INTERVAL = 10000

class BoardSettings:
    KILL_BOARD_WIDTH = 400  # Standardbreite für das Kill Leaderboard
    RECENT_KILLS_WIDTH = 400  # Standardbreite für die Recent Kills-Anzeige
    STATISTICS_WIDTH = 400  # Standardbreite für die Statistiken
