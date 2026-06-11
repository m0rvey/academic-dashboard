import asyncio

from watchdog.events import FileSystemEventHandler


class DBChangeHandler(FileSystemEventHandler):
    def __init__(self, schedule_refresh_callback):
        self.schedule_refresh = schedule_refresh_callback

    def on_modified(self, event):
        if any(event.src_path.endswith(ext) for ext in (".db_change", "planner.db", "planner.db-wal")):
            loop = asyncio.get_running_loop()
            loop.call_soon_threadsafe(self.schedule_refresh)
