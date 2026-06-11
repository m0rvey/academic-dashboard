from typing import Dict, List, Optional

from src.core.database import DatabaseManager
from src.core.logger import setup_logger
from src.core.logic import calculate_priority
from src.core.models import Task

logger = setup_logger("bot_state")


class BotState:
    """Кэшированное состояние для Telegram-бота. Анолог AppState для GUI."""

    def __init__(self, db: DatabaseManager):
        self.db = db
        self._active_tasks: Optional[List[Task]] = None
        self._all_tasks: Optional[List[Task]] = None
        self._tags: Optional[List[str]] = None
        self._kpi_cache: Dict[str, dict] = {}
        self._grades_cache: Optional[dict] = None
        self._subject_gpa_cache: Optional[dict] = None

    def invalidate(self) -> None:
        """Сбрасывает весь кэш. Вызывать после изменений данных."""
        self._active_tasks = None
        self._all_tasks = None
        self._tags = None
        self._kpi_cache.clear()
        self._grades_cache = None
        self._subject_gpa_cache = None

    def get_active_tasks(self) -> List[Task]:
        if self._active_tasks is None:
            self._active_tasks = self.db.get_active_tasks()
        return self._active_tasks

    def get_all_tasks(self) -> List[Task]:
        if self._all_tasks is None:
            self._all_tasks = self.db.get_all_tasks()
        return self._all_tasks

    def get_tags(self) -> List[str]:
        if self._tags is None:
            self._tags = self.db.get_all_tags()
        return self._tags

    def get_kpi_stats(self, period: str = "all") -> dict:
        if period not in self._kpi_cache:
            self._kpi_cache[period] = self.db.get_kpi_stats(period)
        return self._kpi_cache[period]

    def get_grades_stats(self) -> dict:
        if self._grades_cache is None:
            self._grades_cache = self.db.get_grades_stats()
        return self._grades_cache

    def get_subject_grades_gpa(self) -> dict:
        if self._subject_gpa_cache is None:
            self._subject_gpa_cache = self.db.get_subject_grades_gpa()
        return self._subject_gpa_cache

    def get_sorted_active_tasks(self) -> List[Task]:
        """Возвращает активные задачи, отсортированные по приоритету (кэшируется)."""
        tasks = self.get_active_tasks()
        return sorted(tasks, key=calculate_priority, reverse=True)
