import asyncio
import sys

from aiogram import Dispatcher
from aiogram.types import BotCommand

from src.bot.dependencies import ALLOWED_USERS, bot, db, logger, state
from src.bot.handlers import commands, dashboards, files, tasks
from src.bot.middlewares.auth import AuthMiddleware
from src.bot.middlewares.dependencies import DependencyMiddleware
from src.bot.middlewares.throttling import RateLimitMiddleware
from src.bot.scheduler import send_daily_reminders

dp = Dispatcher()

# Регистрация Middlewares
dp.message.outer_middleware(RateLimitMiddleware(limit=1.0))
dp.message.outer_middleware(AuthMiddleware())
dp.message.outer_middleware(DependencyMiddleware(db, state))
dp.callback_query.outer_middleware(AuthMiddleware())
dp.callback_query.outer_middleware(DependencyMiddleware(db, state))

# Регистрация Routers
dp.include_router(commands.router)
dp.include_router(dashboards.router)
dp.include_router(files.router)
dp.include_router(tasks.router)

_bg_tasks = set()


def _reminder_done_callback(task):
    _bg_tasks.discard(task)
    if not task.cancelled():
        if task.exception():
            logger.error(f"Служба напоминаний завершилась с ошибкой: {task.exception()}. Перезапуск...")
        new_task = asyncio.create_task(send_daily_reminders())
        _bg_tasks.add(new_task)
        new_task.add_done_callback(_reminder_done_callback)


async def set_bot_commands():
    bot_commands = [
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="help", description="Показать справку"),
        BotCommand(command="add", description="Добавить задачу"),
        BotCommand(command="list", description="Показать список активных задач"),
        BotCommand(command="stats", description="Дашборд статистики (KPI)"),
        BotCommand(command="grades", description="Дашборд успеваемости (GPA)"),
        BotCommand(command="load", description="Нагрузка на сегодня"),
        BotCommand(command="backup", description="Резервная копия базы данных"),
        BotCommand(command="cancel", description="Отменить создание задачи"),
    ]
    await bot.set_my_commands(bot_commands)


async def main_bot():
    if ALLOWED_USERS:
        logger.info(f"Включена авторизация. Разрешенные ID: {ALLOWED_USERS}")
    else:
        logger.warning(
            "TELEGRAM_ALLOWED_USERS не задан в .env! Доступ к боту заблокирован для всех пользователей (Fail-Closed)."
        )

    logger.info("Запуск Telegram-бота...")
    await set_bot_commands()

    # Запускаем корутину ежедневных напоминаний
    task = asyncio.create_task(send_daily_reminders())
    _bg_tasks.add(task)
    task.add_done_callback(_reminder_done_callback)

    await dp.start_polling(bot)


import threading

bot_thread = None
bot_loop = None


def is_bot_active() -> bool:
    global bot_thread, bot_loop
    if bot_thread is not None and bot_thread.is_alive() and bot_loop is not None and bot_loop.is_running():
        return True
    return False


def start_bot_in_thread():
    global bot_thread, bot_loop
    if bot is None:
        logger.warning("Бот не запущен, так как не настроен TELEGRAM_BOT_TOKEN.")
        return

    def _run():
        global bot_loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        bot_loop = loop
        try:
            loop.run_until_complete(main_bot())
        except Exception as e:
            logger.error(f"Ошибка в потоке бота: {e}")
        finally:
            loop.close()

    bot_thread = threading.Thread(target=_run, daemon=True)
    bot_thread.start()
    logger.info("Поток Telegram-бота запущен.")


def stop_bot_in_thread():
    global bot_loop, bot_thread
    if bot_loop and bot_loop.is_running():
        asyncio.run_coroutine_threadsafe(stop_bot(), bot_loop)
    if bot_thread:
        bot_thread.join(timeout=2.0)
        logger.info("Поток Telegram-бота остановлен.")


async def stop_bot():
    logger.info("Остановка Telegram-бота...")
    await dp.stop_polling()
    await bot.session.close()


if __name__ == "__main__":
    if bot is None:
        logger.critical("Невозможно запустить бота: токен отсутствует.")
        sys.exit(1)
    try:
        asyncio.run(main_bot())
    except KeyboardInterrupt:
        logger.info("Бот остановлен.")
