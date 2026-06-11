import os
import sys

from aiogram import Bot
from dotenv import load_dotenv

from src.bot.state import BotState
from src.core.config import DB_PATH
from src.core.database import DatabaseManager
from src.core.logger import setup_logger

logger = setup_logger("bot")

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
allowed_users_str = os.getenv("TELEGRAM_ALLOWED_USERS", "")
ALLOWED_USERS = {int(x.strip()) for x in allowed_users_str.split(",") if x.strip()}

admin_users_str = os.getenv("TELEGRAM_ADMIN_USERS", "")
ADMIN_USERS = {int(x.strip()) for x in admin_users_str.split(",") if x.strip()}
# Fallback to ALLOWED_USERS if ADMIN_USERS is not set
if not ADMIN_USERS:
    ADMIN_USERS = ALLOWED_USERS

if not TOKEN or TOKEN in ("YOUR_TELEGRAM_BOT_TOKEN_HERE", "your_token_here"):
    logger.critical(
        "В файле .env не указан корректный TELEGRAM_BOT_TOKEN! Пожалуйста, замените заглушку на ваш реальный токен от @BotFather."
    )
    sys.exit(1)

bot = Bot(token=TOKEN)
db = DatabaseManager(DB_PATH)
db.init_db()
state = BotState(db)
