from watchdog.events import FileSystemEventHandler


class DBChangeHandler(FileSystemEventHandler):
    """Наблюдатель за изменениями базы данных academic.db с фильтрацией лишних событий."""

    def __init__(self, schedule_refresh_callback):
        self.schedule_refresh = schedule_refresh_callback

    def on_modified(self, event):
        # Реагируем только на изменения файлов SQLite базы данных
        if any(event.src_path.endswith(ext) for ext in (".db_change", "academic.db", "academic.db-wal", "academic.db-shm")):
            self.schedule_refresh()
