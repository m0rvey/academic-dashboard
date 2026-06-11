import asyncio

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


if __name__ == "__main__":
    try:
        asyncio.run(main_bot())
    except KeyboardInterrupt:
        logger.info("Бот остановлен.")
