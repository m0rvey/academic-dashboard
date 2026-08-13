import os

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
    from aiogram.client.session.aiohttp import AiohttpSession
    from aiogram.client.telegram import TelegramAPIServer

    proxy = os.getenv("TELEGRAM_PROXY")
    api_server = os.getenv("TELEGRAM_API_SERVER")
    if api_server:
        api_server = api_server.strip()
        if api_server and not (api_server.startswith("http://") or api_server.startswith("https://")):
            api_server = "https://" + api_server

    session = None
    if proxy or api_server:
        api = TelegramAPIServer.from_base(api_server) if api_server else TelegramAPIServer.from_base("https://api.telegram.org")
        if proxy:
            proxy_lower = proxy.lower()
            if proxy_lower.startswith("socks5://") or proxy_lower.startswith("socks4://") or proxy_lower.startswith("socks://"):
                try:
                    from aiohttp_socks import ProxyConnector
                    connector = ProxyConnector.from_url(proxy)
                    session = AiohttpSession(connector=connector, api=api)
                    logger.info(f"Инициализирована SOCKS-сессия для Telegram бота через прокси: {proxy}")
                except Exception as ex:
                    logger.error(f"Не удалось инициализировать SOCKS прокси с помощью aiohttp_socks: {ex}. Пробуем обычное подключение.")
                    session = AiohttpSession(proxy=proxy, api=api)
            else:
                session = AiohttpSession(proxy=proxy, api=api)
                logger.info(f"Инициализирована HTTP-сессия для Telegram бота через прокси: {proxy}")
        else:
            session = AiohttpSession(api=api)
            logger.info(f"Инициализирована сессия для Telegram бота с кастомным сервером API: {api_server}")

    if session:
        bot = Bot(token=TOKEN, session=session)
    else:
        bot = Bot(token=TOKEN)
    state = BotState(db)
