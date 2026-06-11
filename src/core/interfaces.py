from abc import ABC, abstractmethod
from typing import List, Optional

from .models import Task, TaskStatus


class IDatabaseManager(ABC):
    @abstractmethod
    def close(self) -> None:
        """Закрывает соединение с базой данных."""
        pass

    @abstractmethod
    def add_task(self, task: Task, notify: bool = True) -> int:
        """Добавляет задачу в базу данных и возвращает её ID."""
        pass

    @abstractmethod
    def get_all_tasks(self) -> List[Task]:
        """Получает все задачи из базы данных."""
        pass

    @abstractmethod
    def get_active_tasks(self) -> List[Task]:
        """Получает только невыполненные задачи из базы данных."""
        pass

    @abstractmethod
    def get_tasks_with_grades(self) -> List[Task]:
        """Получает только выполненные задачи, у которых выставлена оценка."""
        pass

    @abstractmethod
    def update_task_status(self, task_id: int, status: TaskStatus) -> bool:
        """Обновляет статус задачи по её ID. Возвращает True в случае успеха."""
        pass

    @abstractmethod
    def update_task_grade(self, task_id: int, grade: Optional[int]) -> bool:
        """Обновляет оценку задачи по её ID. Возвращает True в случае успеха."""
        pass

    @abstractmethod
    def update_task(self, task: Task) -> bool:
        """Обновляет всю информацию о задаче."""
        pass

    @abstractmethod
    def delete_task(self, task_id: int) -> bool:
        """Удаляет задачу по ID."""
        pass

    @abstractmethod
    def export_to_json(self, filepath: str) -> None:
        """Экспортирует все задачи в JSON файл."""
        pass

    @abstractmethod
    def import_from_json(self, filepath: str) -> None:
        """Импортирует задачи из JSON файла (добавляет к существующим)."""
        pass

    @abstractmethod
    def get_task_by_id(self, task_id: int) -> Optional[Task]:
        """Получает задачу по её ID. Возвращает None, если задача не найдена."""
        pass

    @abstractmethod
    def register_user(self, chat_id: int) -> None:
        """Регистрирует chat_id пользователя Telegram в базе данных."""
        pass

    @abstractmethod
    def get_all_tags(self) -> List[str]:
        """Получает список всех уникальных тегов из базы данных."""
        pass

    @abstractmethod
    def get_all_users(self) -> List[int]:
        """Получает список всех зарегистрированных chat_id пользователей."""
        pass

    @abstractmethod
    def unregister_user(self, chat_id: int) -> bool:
        """Удаляет chat_id пользователя из базы данных."""
        pass

    @abstractmethod
    def get_filtered_tasks(
        self,
        search_query: Optional[str] = None,
        status: Optional[TaskStatus] = None,
        tag: Optional[str] = None,
        sort_by: Optional[str] = None,
    ) -> List[Task]:
        """Получает отфильтрованные и отсортированные задачи непосредственно из БД."""
        pass

    @abstractmethod
    def get_daily_load_for_date(self, target_date: str) -> tuple:
        """Вычисляет суммарную нагрузку на указанную дату на уровне БД.
        Возвращает кортеж (total_load, is_overloaded)."""
        pass

    @abstractmethod
    def get_kpi_stats(self, period: str = "all") -> dict:
        """Получает агрегированную KPI-статистику по задачам."""
        pass

    @abstractmethod
    def get_subject_load(self, period: str = "all") -> dict:
        """Получает распределение нагрузки по предметам."""
        pass

    @abstractmethod
    def get_tag_load(self, period: str = "all") -> dict:
        """Получает распределение нагрузки по тегам."""
        pass

    @abstractmethod
    def get_completed_tasks_by_day_last_7_days(self) -> dict:
        """Получает количество выполненных задач по дням за последние 7 дней (от date('now', '-6 days') до date('now'))."""
        pass

    @abstractmethod
    def get_grades_stats(self) -> dict:
        """Получает общую успеваемость."""
        pass

    @abstractmethod
    def get_subject_grades_gpa(self) -> dict:
        """Получает средний балл по каждому предмету."""
        pass

    @abstractmethod
    def get_overdue_tasks(self, today_date_str: str) -> List[Task]:
        """Получает все просроченные невыполненные задачи на указанную дату."""
        pass

    @abstractmethod
    def get_tasks_by_date(self, target_date_str: str) -> List[Task]:
        """Получает все невыполненные задачи на указанную дату."""
        pass

    @abstractmethod
    def get_all_tasks_by_date(self, target_date_str: str) -> List[Task]:
        """Получает абсолютно все задачи (включая выполненные) на указанную дату дедлайна."""
        pass

    @abstractmethod
    def get_tasks_in_date_range(self, start_date_str: str, end_date_str: str) -> List[Task]:
        """Получает все задачи с дедлайном в указанном диапазоне дат."""
        pass

    @abstractmethod
    def rotate_local_backups(self) -> None:
        """Создает резервную копию базы данных и оставляет только MAX_BACKUPS последних бэкапов."""
        pass
