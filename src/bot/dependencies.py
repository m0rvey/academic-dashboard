import os
import sys

from aiogram import Bot
from dotenv import load_dotenv

from src.bot.state import BotState
from src.core.config import DB_PATH, ENV_PATH
from src.core.database import DatabaseManager
from src.core.logger import setup_logger

logger = setup_logger("bot")

load_dotenv(dotenv_path=ENV_PATH)
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
allowed_users_str = os.getenv("TELEGRAM_ALLOWED_USERS", "")
ALLOWED_USERS = set()
for x in allowed_users_str.split(","):
    x_clean = x.strip()
    if x_clean:
        try:
            ALLOWED_USERS.add(int(x_clean))
        except ValueError:
            logger.warning(f"Некорректный ID пользователя в TELEGRAM_ALLOWED_USERS: '{x_clean}' (должно быть целым числом)")

admin_users_str = os.getenv("TELEGRAM_ADMIN_USERS", "")
ADMIN_USERS = set()
for x in admin_users_str.split(","):
    x_clean = x.strip()
    if x_clean:
        try:
            ADMIN_USERS.add(int(x_clean))
        except ValueError:
            logger.warning(f"Некорректный ID администратора в TELEGRAM_ADMIN_USERS: '{x_clean}' (должно быть целым числом)")

# Fallback to ALLOWED_USERS if ADMIN_USERS is not set
if not ADMIN_USERS:
    ADMIN_USERS = ALLOWED_USERS

db = DatabaseManager(DB_PATH)
db.init_db()

if not TOKEN or TOKEN in ("YOUR_TELEGRAM_BOT_TOKEN_HERE", "your_token_here"):
    logger.warning(
        "В файле .env не указан корректный TELEGRAM_BOT_TOKEN! Бот отключен."
    )
    bot = None
    state = None
else:
    bot = Bot(token=TOKEN)
    state = BotState(db)
