"""Конфигурационные константы проекта Academic Dashboard."""

from pathlib import Path

# Корневая директория проекта
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent

# Путь к файлу базы данных
DB_PATH: Path = PROJECT_ROOT / "data" / "planner.db"

# Лимит дневной нагрузки (сумма effort_score на один день)
DAILY_LOAD_LIMIT: int = 10

# Множитель приоритета для задач с тегами экзаменов (ОГЭ, ЕГЭ, Экзамен)
EXAM_PRIORITY_MULTIPLIER: float = 1.5

# Теги, повышающие приоритет задачи
EXAM_TAGS: tuple = ("ОГЭ", "Экзамен", "ЕГЭ")

# Диапазон сложности задачи
MIN_EFFORT: int = 1
MAX_EFFORT: int = 10

# Количество хранимых бэкапов при ротации
MAX_BACKUPS: int = 5
