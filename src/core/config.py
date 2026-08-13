"""Конфигурационные константы проекта Academic Dashboard."""

from pathlib import Path

# Корневая директория проекта
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent

# Пути к данным и конфигурации
DATA_DIR: Path = PROJECT_ROOT / "data"
DB_PATH: Path = DATA_DIR / "planner.db"
ENV_PATH: Path = PROJECT_ROOT / ".env"
LOG_FILE_PATH: Path = DATA_DIR / "app.log"

# Гарантируем существование директории данных
DATA_DIR.mkdir(parents=True, exist_ok=True)

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

INVALID_TOKENS: set[str] = {
    "",
    "YOUR_TELEGRAM_BOT_TOKEN_HERE",
    "your_token_here",
}

INVALID_USERS: set[str] = {
    "",
    "YOUR_TELEGRAM_CHAT_ID_HERE",
}



def validate_env(exit_on_error: bool = True) -> bool:
    """Проверяет наличие и корректность файла .env.
    Если файл отсутствует или не настроен, выводит понятную инструкцию в консоль
    и завершает работу без вызова Flet.
    """
    import os
    import shutil
    import sys

    from dotenv import load_dotenv

    env_exists = ENV_PATH.exists()

    if not env_exists:
        example_path = PROJECT_ROOT / ".env.example"
        if example_path.exists():
            try:
                shutil.copy(example_path, ENV_PATH)
            except Exception:
                pass

        msg = (
            "\n❌ ERROR: .env file not found!\n\n"
            "A template .env file was automatically created from .env.example.\n"
            "Please open the .env file in a text editor and specify your TELEGRAM_BOT_TOKEN and TELEGRAM_ALLOWED_USERS.\n\n"
            "📖 Read detailed setup instructions in README.md on GitHub:\n"
            "https://github.com/m0rvey/academic-dashboard\n\n"
            "----------------------------------------------------------------------\n\n"
            "❌ ОШИБКА: Файл .env не найден!\n\n"
            "Был автоматически создан файл .env из шаблона .env.example.\n"
            "Пожалуйста, откройте файл .env в текстовом редакторе и укажите ваш TELEGRAM_BOT_TOKEN и TELEGRAM_ALLOWED_USERS.\n\n"
            "📖 Прочитайте подробную инструкцию по настройке в README.md на GitHub:\n"
            "https://github.com/m0rvey/academic-dashboard\n"
        )
        print(msg)
        if exit_on_error and "pytest" not in sys.modules:
            sys.exit(1)
        return False

    load_dotenv(dotenv_path=ENV_PATH, override=True)
    token = (os.getenv("TELEGRAM_BOT_TOKEN") or "").strip()
    allowed_users = (os.getenv("TELEGRAM_ALLOWED_USERS") or "").strip()

    if not token or token in INVALID_TOKENS or not allowed_users or allowed_users in INVALID_USERS:
        msg = (
            "\n❌ ERROR: .env file is not properly configured!\n\n"
            "Please open the .env file in a text editor and set valid credentials for:\n"
            "  • TELEGRAM_BOT_TOKEN (get from @BotFather)\n"
            "  • TELEGRAM_ALLOWED_USERS (your Telegram Chat ID, get from @userinfobot)\n\n"
            "📖 Read detailed setup instructions in README.md on GitHub:\n"
            "https://github.com/m0rvey/academic-dashboard\n\n"
            "----------------------------------------------------------------------\n\n"
            "❌ ОШИБКА: Файл .env не настроен!\n\n"
            "Пожалуйста, откройте файл .env в текстовом редакторе и установите валидные значения:\n"
            "  • TELEGRAM_BOT_TOKEN (получить у @BotFather)\n"
            "  • TELEGRAM_ALLOWED_USERS (ваш Telegram Chat ID, можно узнать у @userinfobot)\n\n"
            "📖 Прочитайте подробную инструкцию по настройке в README.md на GitHub:\n"
            "https://github.com/m0rvey/academic-dashboard\n"
        )
        print(msg)
        if exit_on_error and "pytest" not in sys.modules:
            sys.exit(1)
        return False


    return True

