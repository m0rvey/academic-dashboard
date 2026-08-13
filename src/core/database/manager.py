import sqlite3
from pathlib import Path
from typing import List, Optional

from src.core.database.backup_manager import BackupManager
from src.core.database.connection import DatabaseConnection
from src.core.database.grade_repository import GradeRepository
from src.core.database.stats_repository import StatsRepository, get_period_dates
from src.core.database.task_repository import TaskRepository
from src.core.database.user_repository import UserRepository
from src.core.interfaces import IDatabaseManager
from src.core.models import Task, TaskStatus

__all__ = ["DatabaseManager", "get_period_dates"]


class DatabaseManager(IDatabaseManager):
    """Фасад управления базой данных SQLite3 для учебных задач."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._db_conn = DatabaseConnection(db_path)
        self._task_repo = TaskRepository(self._db_conn)
        self._grade_repo = GradeRepository(self._db_conn)
        self._stats_repo = StatsRepository(self._db_conn)
        self._backup_mgr = BackupManager(self._db_conn, self._task_repo, notify_callback=lambda: self._notify_change())
        self._user_repo = UserRepository(self._db_conn)

    def _connection(self):
        return self._db_conn.connection()

    def _notify_change(self) -> None:
        self._db_conn.notify_change()

    def close(self) -> None:
        self._db_conn.close()

    def init_db(self) -> None:
        """Инициализирует структуру базы данных и выполняет миграции."""
        from src.core.migrations import run_migrations

        with self._db_conn.connection() as conn:
            try:
                run_migrations(conn)
                conn.commit()
            except sqlite3.Error as e:
                conn.rollback()
                raise e

    # TaskRepository delegators
    def add_task(self, task: Task, notify: bool = True) -> int:
        return self._task_repo.add_task(task, notify=notify)

    def get_all_tasks(self) -> List[Task]:
        return self._task_repo.get_all_tasks()

    def get_active_tasks(self) -> List[Task]:
        return self._task_repo.get_active_tasks()

    def get_tasks_with_grades(self) -> List[Task]:
        return self._task_repo.get_tasks_with_grades()

    def update_task_status(self, task_id: int, status: TaskStatus) -> bool:
        return self._task_repo.update_task_status(task_id, status)

    def update_task_grade(self, task_id: int, grade: Optional[int]) -> bool:
        return self._task_repo.update_task_grade(task_id, grade)

    def update_task(self, task: Task) -> bool:
        return self._task_repo.update_task(task)

    def delete_task(self, task_id: int) -> bool:
        return self._task_repo.delete_task(task_id)

    def get_task_by_id(self, task_id: int) -> Optional[Task]:
        return self._task_repo.get_task_by_id(task_id)

    def get_all_tags(self) -> List[str]:
        return self._task_repo.get_all_tags()

    def get_filtered_tasks(
        self,
        search_query: Optional[str] = None,
        status: Optional[TaskStatus] = None,
        tag: Optional[str] = None,
        sort_by: Optional[str] = None,
    ) -> List[Task]:
        return self._task_repo.get_filtered_tasks(search_query, status, tag, sort_by)

    def get_overdue_tasks(self, today_date_str: str) -> List[Task]:
        return self._task_repo.get_overdue_tasks(today_date_str)

    def get_tasks_by_date(self, target_date_str: str) -> List[Task]:
        return self._task_repo.get_tasks_by_date(target_date_str)

    def get_all_tasks_by_date(self, target_date_str: str) -> List[Task]:
        return self._task_repo.get_all_tasks_by_date(target_date_str)

    def get_tasks_in_date_range(self, start_date_str: str, end_date_str: str) -> List[Task]:
        return self._task_repo.get_tasks_in_date_range(start_date_str, end_date_str)

    # GradeRepository delegators
    def get_grades_stats(self) -> dict:
        return self._grade_repo.get_grades_stats()

    def get_subject_grades_gpa(self) -> dict:
        return self._grade_repo.get_subject_grades_gpa()

    # StatsRepository delegators
    def get_daily_load_for_date(self, target_date: str) -> tuple:
        return self._stats_repo.get_daily_load_for_date(target_date)

    def get_kpi_stats(self, period: str = "all") -> dict:
        return self._stats_repo.get_kpi_stats(period)

    def get_subject_load(self, period: str = "all") -> dict:
        return self._stats_repo.get_subject_load(period)

    def get_tag_load(self, period: str = "all") -> dict:
        return self._stats_repo.get_tag_load(period)

    def get_completed_tasks_by_day_last_7_days(self) -> dict:
        return self._stats_repo.get_completed_tasks_by_day_last_7_days()

    # BackupManager delegators
    def export_to_json(self, filepath: str) -> None:
        return self._backup_mgr.export_to_json(filepath)

    def import_from_json(self, filepath: str) -> None:
        return self._backup_mgr.import_from_json(filepath)

    def rotate_local_backups(self) -> None:
        return self._backup_mgr.rotate_local_backups()

    # UserRepository delegators
    def register_user(self, chat_id: int) -> None:
        return self._user_repo.register_user(chat_id)

    def get_all_users(self) -> List[int]:
        return self._user_repo.get_all_users()

    def unregister_user(self, chat_id: int) -> bool:
        return self._user_repo.unregister_user(chat_id)

    def get_user_reminder_hour(self, chat_id: int) -> int:
        return self._user_repo.get_user_reminder_hour(chat_id)

    def set_user_reminder_hour(self, chat_id: int, hour: int) -> bool:
        return self._user_repo.set_user_reminder_hour(chat_id, hour)

    def get_users_with_reminder_hour(self, hour: int) -> List[int]:
        return self._user_repo.get_users_with_reminder_hour(hour)

