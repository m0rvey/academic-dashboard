import asyncio
from datetime import date, datetime

from aiogram.exceptions import TelegramAPIError
from aiogram.types import FSInputFile

from src.bot.dependencies import bot, db, logger
from src.core.config import DB_PATH


async def send_daily_reminders():
    """Служба ежедневных напоминаний и автоматических бэкапов."""
    logger.info("Служба ежедневных напоминаний запущена.")

    sent_actions = set()

    while True:
        now = datetime.now()
        today_key = now.strftime("%Y-%m-%d")

        try:
            # Персональное ежедневное напоминание по настроенному часу пользователя
            users = db.get_all_users()
            if users:
                today_date = date.today()
                today_str = today_date.isoformat()
                overdue = db.get_overdue_tasks(today_str)
                today_tasks = db.get_tasks_by_date(today_str)

                if overdue or today_tasks:
                    from aiogram.utils.keyboard import InlineKeyboardBuilder

                    from src.bot.utils import escape_md

                    response = "🔔 *Ежедневная сводка по учебным задачам:*\n\n"
                    builder = InlineKeyboardBuilder()

                    all_reminder_tasks = list(overdue) + [t for t in today_tasks if t not in overdue]

                    if overdue:
                        response += "🚨 *Просроченные задачи:*\n"
                        for idx, task in enumerate(overdue, start=1):
                            response += f"*{idx}.* *{escape_md(task.subject)}* (дедлайн: {task.deadline})\n"
                        response += "\n"
                    if today_tasks:
                        response += "📅 *Задачи на сегодня:*\n"
                        offset = len(overdue)
                        for idx, task in enumerate(today_tasks, start=offset + 1):
                            response += f"*{idx}.* *{escape_md(task.subject)}* (сложность: {task.effort_score} ед.)\n"

                    for idx, task in enumerate(all_reminder_tasks, start=1):
                        builder.button(text=f"✅ {idx}. {task.subject[:12]}", callback_data=f"complete_{task.id}")
                    builder.adjust(2)

                    markup = builder.as_markup() if all_reminder_tasks else None

                    for chat_id in users:
                        user_hour = db.get_user_reminder_hour(chat_id)
                        reminder_key = f"{today_key}_rem_{chat_id}_{user_hour}"
                        if now.hour >= user_hour and reminder_key not in sent_actions:
                            sent_actions.add(reminder_key)
                            try:
                                await bot.send_message(chat_id, response, parse_mode="Markdown", reply_markup=markup)
                            except TelegramAPIError as e:
                                logger.warning(f"Error sending message to {chat_id}: {e}")



            # Автоматический еженедельный бэкап по воскресеньям в 10:00
            backup_key = f"{today_key}_backup"
            if now.weekday() == 6 and now.hour >= 10 and backup_key not in sent_actions:
                sent_actions.add(backup_key)
                users = db.get_all_users()
                if users and DB_PATH.exists():
                    for chat_id in users:
                        try:
                            document = FSInputFile(DB_PATH)
                            await bot.send_document(
                                chat_id,
                                document,
                                caption=f"📦 *Автоматическая еженедельная резервная копия*\n📅 Дата: {now.strftime('%Y-%m-%d %H:%M:%S')}",
                                parse_mode="Markdown",
                            )
                        except TelegramAPIError as e:
                            logger.warning(f"Error sending backup to {chat_id}: {e}")

            # Очищаем старые ключи при смене дня
            old_keys = [k for k in sent_actions if not k.startswith(today_key)]
            for k in old_keys:
                sent_actions.discard(k)

        except Exception as e:
            logger.error(f"Ошибка в службе напоминаний: {e}", exc_info=True)

        await asyncio.sleep(300)
