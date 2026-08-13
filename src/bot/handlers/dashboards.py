from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.bot.dependencies import logger
from src.bot.state import BotState
from src.bot.utils import escape_md
from src.core.database import DatabaseManager

router = Router()


def generate_stats_text(period: str, app_state: BotState) -> str:
    stats = app_state.get_kpi_stats(period)
    period_names = {
        "all": "За всё время",
        "today": "Сегодня",
        "week": "За неделю",
        "month": "За месяц",
    }
    period_name = period_names.get(period, "За всё время")

    total = stats.get("total", 0)
    completed = stats.get("completed", 0)
    overdue = stats.get("overdue", 0)
    high_priority = stats.get("high_priority", 0)
    completion_rate = round((completed / total * 100)) if total > 0 else 0

    return (
        f"📊 *KPI Дашборд ({period_name})*\n\n"
        f"✅ Выполнено задач: *{completed}*\n"
        f"🔥 Срочных задач: *{high_priority}*\n"
        f"🚨 Просрочено: *{overdue}*\n\n"
        f"🔄 Всего задач: *{total}* | Эффективность: *{completion_rate}%*"
    )


def generate_stats_keyboard(current_period: str):
    builder = InlineKeyboardBuilder()
    periods = {
        "today": "Сегодня",
        "week": "Неделя",
        "month": "Месяц",
        "all": "Всё время",
    }
    for p_key, p_name in periods.items():
        marker = "✅ " if p_key == current_period else ""
        builder.button(text=f"{marker}{p_name}", callback_data=f"stats_{p_key}")
    builder.adjust(2)
    return builder.as_markup()


@router.message(Command("stats"))
async def stats_command_handler(message: Message, db: DatabaseManager, app_state: BotState):
    db.register_user(message.chat.id)
    text = generate_stats_text("week", app_state)
    markup = generate_stats_keyboard("week")
    await message.answer(text, parse_mode="Markdown", reply_markup=markup)


@router.callback_query(F.data.startswith("stats_"))
async def process_stats_callback(callback: CallbackQuery, app_state: BotState):
    period = callback.data.split("_")[1]
    text = generate_stats_text(period, app_state)
    markup = generate_stats_keyboard(period)
    try:
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=markup)
    except TelegramAPIError as ex:
        logger.warning(f"Error editing stats message: {ex}")
    await callback.answer()


def generate_grades_text(app_state: BotState) -> str:
    stats = app_state.get_grades_stats()
    subject_gpa = app_state.get_subject_grades_gpa()

    if not stats:
        return "🎓 *Успеваемость (GPA)*\n\nНет данных об оценках."

    gpa = round(stats.get("gpa", 0), 2)
    total_grades = stats.get("total_count", 0)
    c5 = stats.get("count_5", 0)
    c4 = stats.get("count_4", 0)
    c3 = stats.get("count_3", 0)
    c2 = stats.get("count_2", 0)

    text = (
        f"🎓 *Успеваемость (GPA)*\n\n"
        f"Общий GPA: *{gpa}*\n"
        f"Всего оценок: *{total_grades}*\n"
        f"Отлично (5): *{c5}*\n"
        f"Хорошо (4): *{c4}*\n"
        f"Удовл. (3): *{c3}*\n"
        f"Неудовл. (2): *{c2}*\n\n"
        f"📚 *По предметам:*\n"
    )
    if not subject_gpa:
        text += "Нет данных по предметам."
    else:
        for subj, val in subject_gpa.items():
            if isinstance(val, dict):
                score = round(val.get("gpa", 0.0), 2)
                cnt = val.get("count", 0)
                text += f"• {escape_md(subj)}: *{score:.2f}* ({cnt} оц.)\n"
            else:
                score = round(float(val), 2)
                text += f"• {escape_md(subj)}: *{score:.2f}*\n"
    return text


@router.message(Command("grades"))
async def grades_command_handler(message: Message, db: DatabaseManager, app_state: BotState):
    db.register_user(message.chat.id)
    text = generate_grades_text(app_state)
    await message.answer(text, parse_mode="Markdown")
