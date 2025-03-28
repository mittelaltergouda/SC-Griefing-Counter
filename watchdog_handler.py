from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import config
import log_processor
import os

class GameLogHandler(FileSystemEventHandler):
    """Watches the Game.log for modifications or creation."""

    def on_modified(self, event):
        if event.is_directory:
            return
        if os.path.basename(event.src_path).lower() == config.GAME_LOG_FILENAME.lower():
            log_processor.process_log_file(event.src_path)

    def on_created(self, event):
        if event.is_directory:
            return
        if os.path.basename(event.src_path).lower() == config.GAME_LOG_FILENAME.lower():
            log_processor.process_log_file(event.src_path)

def start_watchdog():
    """Starts a watchdog observer on LIVE_FOLDER and returns it."""
    if not os.path.isdir(config.LIVE_FOLDER):
        print("[WARNING] LIVE_FOLDER does not exist.")
        return None
    observer = Observer()
    handler = GameLogHandler()
    observer.schedule(handler, config.LIVE_FOLDER, recursive=False)
    observer.start()
    return observer
