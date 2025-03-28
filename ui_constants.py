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
    DEFAULT_SIZE = "1500x700"  # Größere Standardgröße für bessere Darstellung aller Elemente
    MIN_WIDTH = 1200
    MIN_HEIGHT = 600

class RefreshSettings:
    DEFAULT_INTERVAL = 5
    MIN_INTERVAL = 1
    MAX_INTERVAL = 60
