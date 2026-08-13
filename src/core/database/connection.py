import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path

from src.core.logger import setup_logger

logger = setup_logger("database_connection")


class DatabaseConnection:
    """Управление подключением к базе данных SQLite3."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._conn = None
        self._lock = threading.Lock()

    def notify_change(self) -> None:
        """Обновляет время изменения базы данных с помощью файла-триггера."""
        try:
            trigger_path = self.db_path.parent / ".db_change"
            trigger_path.parent.mkdir(parents=True, exist_ok=True)
            trigger_path.touch(exist_ok=True)
        except OSError as e:
            logger.warning(f"Error in notify_change: {e}")

    @contextmanager
    def connection(self):
        """Возвращает соединение с БД под блокировкой."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            if self._conn is None:
                self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
                self._conn.row_factory = sqlite3.Row
                self._conn.execute("PRAGMA journal_mode = WAL;")
                self._conn.execute("PRAGMA foreign_keys = ON;")
            yield self._conn

    def close(self) -> None:
        """Закрывает соединение с базой данных."""
        with self._lock:
            conn = self._conn
            self._conn = None
            if conn is not None:
                conn.close()
