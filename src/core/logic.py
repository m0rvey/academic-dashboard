from datetime import date
from typing import List

from src.core.config import DAILY_LOAD_LIMIT, EXAM_PRIORITY_MULTIPLIER, EXAM_TAGS
from src.core.models import Task, TaskStatus, get_clean_date


def calculate_priority(task: Task) -> float:
    """Вычисляет приоритет задачи.

    Формула: effort_score / (days_left + 1) * EXAM_PRIORITY_MULTIPLIER если есть теги из EXAM_TAGS.
    Чтобы избежать деления на ноль и некорректных значений для просроченных задач,
    разница в днях (days_left) ограничивается снизу нулем.
    """
    deadline_date = task.deadline_date

    today = date.today()
    days_left = (deadline_date - today).days

    # Ограничиваем days_left снизу нулем, чтобы сегодняшние и просроченные задачи
    # имели наивысший приоритет и не вызывали ошибку деления на ноль.
    days_left = max(0, days_left)

    priority = task.effort_score / (days_left + 1)
    if any(tag in task.tags for tag in EXAM_TAGS):
        priority *= EXAM_PRIORITY_MULTIPLIER

    return priority


def get_daily_load(tasks: List[Task]) -> int:
    """Возвращает сумму effort_score всех невыполненных задач (статус не равен DONE) из переданного списка."""
    return sum(task.effort_score for task in tasks if task.status != TaskStatus.DONE)


def check_daily_load(tasks: List[Task], target_date: str) -> tuple:
    """Проверяет дневную нагрузку на указанную дату.

    Возвращает кортеж (total_load, is_overloaded).
    """
    try:
        target_date_obj = date.fromisoformat(get_clean_date(target_date))
    except ValueError:
        target_date_obj = date.today()
    day_tasks = [t for t in tasks if t.deadline_date == target_date_obj]
    total_load = get_daily_load(day_tasks)
    return total_load, total_load > DAILY_LOAD_LIMIT
