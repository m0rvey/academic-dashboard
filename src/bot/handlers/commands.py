from datetime import date, datetime

from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message

from src.bot.dependencies import ADMIN_USERS
from src.bot.state import BotState
from src.core.config import DAILY_LOAD_LIMIT, DB_PATH
from src.core.database import DatabaseManager
from src.core.logic import check_daily_load

router = Router()


@router.message(Command("cancel"))
@router.message(F.text.casefold() == "отмена")
async def cancel_handler(message: Message, state: FSMContext) -> None:
    """Отменяет любой активный процесс создания задачи и очищает состояние FSM."""
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("ℹ️ Нет активного процесса создания задачи для отмены.")
        return

    await state.clear()
    await message.answer("❌ Создание задачи отменено.")


@router.message(Command("start", "help"))
async def send_welcome(message: Message, db: DatabaseManager):
    db.register_user(message.chat.id)

    help_text = (
        "📚 *Академический дашборд Бот*\n\n"
        "Я помогу вам управлять вашим списком учебных задач прямо из Telegram! "
        "Все изменения синхронизируются с графическим интерфейсом (GUI) дашборда.\n\n"
        "📋 *Доступные команды:*\n"
        "• /list — Показать список активных задач (с кнопками управления)\n"
        "• /done — Завершить задачу (в один клик или по номеру: `/done 1`)\n"
        "• /load — Показать текущую дневную нагрузку на сегодня\n"
        "• /stats — 📊 Показать дашборд статистики (KPI)\n"
        "• /grades — 🎓 Показать статистику успеваемости (GPA)\n"
        "• /add — Добавить новую задачу (пошаговый мастер или фразой)\n"
        "• /settings — Настроить время ежедневных напоминаний\n"
        "• /backup — Получить резервную копию базы данных (.db)\n"
        "• /cancel — Отменить добавление задачи в процессе\n"
    )
    await message.answer(help_text, parse_mode="Markdown")


@router.message(Command("backup"))
async def backup_db_handler(message: Message, db: DatabaseManager):
    db.register_user(message.chat.id)
    if message.from_user.id not in ADMIN_USERS:
        await message.answer("⛔ У вас нет прав для выполнения этой команды. Доступ разрешен только администраторами.")
        return
    if not DB_PATH.exists():
        await message.answer("❌ Файл базы данных не найден.")
        return
    try:
        document = FSInputFile(DB_PATH)
        await message.answer_document(
            document,
            caption=f"📦 *Резервная копия базы данных*\n📅 Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            parse_mode="Markdown",
        )
    except (TelegramAPIError, OSError) as e:
        await message.answer(f"❌ Ошибка при создании резервной копии: {e}")


@router.message(Command("load"))
async def check_load(message: Message, db: DatabaseManager, app_state: BotState):
    db.register_user(message.chat.id)
    today_str = date.today().isoformat()
    all_tasks = app_state.get_active_tasks()

    total_load, is_overloaded = check_daily_load(all_tasks, today_str)

    response = (
        f"📅 *Нагрузка на сегодня ({today_str}):*\n"
        f"Текущий уровень нагрузки: `{total_load} / {DAILY_LOAD_LIMIT}` ед.\n\n"
    )

    if is_overloaded:
        response += f"⚠️ *ВНИМАНИЕ:* Дневная нагрузка превышает лимит! Перегрузка на {total_load - DAILY_LOAD_LIMIT} ед."
    elif total_load > 0:
        response += f"🟢 Нагрузка в пределах нормы (<= {DAILY_LOAD_LIMIT} ед.). Всё под контролем!"
    else:
        response += "🎉 Сегодня у вас нет невыполненных задач с дедлайном. Отдыхайте!"

    await message.answer(response, parse_mode="Markdown")



def build_settings_keyboard(current_hour: int):
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    text = (
        "⚙️ *Настройки ежедневных напоминаний*\n\n"
        f"Текущее время рассылки: *{current_hour:02d}:00*\n\n"
        "Выберите удобное время для получения сводки по задачам:"
    )
    hours = [8, 9, 10, 12, 18, 21]
    builder = InlineKeyboardBuilder()
    for h in hours:
        label = f"✅ {h:02d}:00" if h == current_hour else f"{h:02d}:00"
        builder.button(text=label, callback_data=f"set_rem_{h}")
    builder.adjust(3)
    return text, builder.as_markup()


@router.message(Command("settings"))
async def settings_command(message: Message, db: DatabaseManager):
    db.register_user(message.chat.id)
    curr_hour = db.get_user_reminder_hour(message.chat.id)
    text, markup = build_settings_keyboard(curr_hour)
    await message.answer(text, parse_mode="Markdown", reply_markup=markup)


@router.callback_query(F.data.startswith("set_rem_"))
async def process_set_reminder_callback(callback: CallbackQuery, db: DatabaseManager):
    try:
        hour = int(callback.data.split("_")[-1])

    except (IndexError, ValueError):
        await callback.answer("❌ Ошибка при выборе времени.")
        return

    chat_id = callback.message.chat.id
    if db.set_user_reminder_hour(chat_id, hour):
        await callback.answer(f"⏰ Время напоминания установлено на {hour:02d}:00!")
        text, markup = build_settings_keyboard(hour)
        try:
            await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=markup)
        except Exception:
            pass
    else:
        await callback.answer("❌ Не удалось сохранить настройки.")

