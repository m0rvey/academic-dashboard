from datetime import date
from enum import IntEnum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from src.core.config import MAX_EFFORT, MIN_EFFORT


class TaskStatus(IntEnum):
    """Статусы выполнения задачи."""

    TODO = 0
    DOING = 1
    DONE = 2


class Task(BaseModel):
    """Модель учебной задачи."""

    subject: str
    description: str
    deadline: str  # Формат: YYYY-MM-DD
    effort_score: int  # Оценка сложности/затрат (1-10)
    tags: List[str] = Field(default_factory=list)  # Список тегов
    status: TaskStatus = TaskStatus.TODO
    id: Optional[int] = None
    grade: Optional[int] = None

    model_config = {"validate_assignment": True}

    @field_validator("subject")
    @classmethod
    def validate_subject(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Предмет (subject) не может быть пустым.")
        return v

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Описание (description) не может быть пустым.")
        return v

    @field_validator("effort_score")
    @classmethod
    def validate_effort_score(cls, v: int) -> int:
        if not isinstance(v, int) or not (MIN_EFFORT <= v <= MAX_EFFORT):
            raise ValueError(
                f"Сложность (effort_score) должна быть целым числом от {MIN_EFFORT} до {MAX_EFFORT}, получено: {v}"
            )
        return v

    @field_validator("grade")
    @classmethod
    def validate_grade(cls, v: Optional[int]) -> Optional[int]:
        if v is not None:
            if not isinstance(v, int) or v not in (2, 3, 4, 5):
                raise ValueError(f"Оценка (grade) должна быть 2, 3, 4 или 5, получено: {v}")
        return v

    @property
    def deadline_date(self):
        clean = get_clean_date(self.deadline)
        try:
            return date.fromisoformat(clean)
        except ValueError:
            return date.today()


def get_clean_date(deadline: str) -> str:
    """Извлекает чистую дату YYYY-MM-DD из строки дедлайна, отсекая время если есть."""
    return deadline.split("T")[0].strip() if deadline else ""
