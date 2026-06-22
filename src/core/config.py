"""Конфигурационные константы проекта Academic Dashboard."""

from pathlib import Path

import sys
from pathlib import Path

# Определяем, запущено ли приложение в скомпилированном виде (PyInstaller)
IS_BUNDLED = hasattr(sys, "_MEIPASS")

if IS_BUNDLED:
    # На macOS сохраняем данные в стандартную папку пользователя Application Support
    DATA_DIR = Path.home() / "Library" / "Application Support" / "AcademicDashboard"
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DB_PATH = DATA_DIR / "planner.db"
    
    # Ищем .env сначала в папке Application Support, затем рядом с запускаемым .app
    app_dir = Path(sys.executable).parent
    if ".app/Contents/MacOS" in str(app_dir):
        app_root = app_dir.parent.parent.parent
    else:
        app_root = app_dir

    local_env = app_root / ".env"
    app_support_env = DATA_DIR / ".env"
    
    if local_env.exists() and not app_support_env.exists():
        try:
            import shutil
            shutil.copy2(local_env, app_support_env)
        except Exception:
            pass
            
    ENV_PATH = app_support_env
else:
    # Корневая директория проекта
    PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent
    DB_PATH = PROJECT_ROOT / "data" / "planner.db"
    ENV_PATH = PROJECT_ROOT / ".env"

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
