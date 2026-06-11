import asyncio
import json
import os
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

from aiogram import BaseMiddleware, Bot, Dispatcher, F
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, FSInputFile, Message, TelegramObject
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv

from src.core.config import DAILY_LOAD_LIMIT, DB_PATH, MAX_EFFORT, MIN_EFFORT
from src.core.database import DatabaseManager
from src.core.logger import setup_logger
from src.core.logic import calculate_priority, check_daily_load
from src.core.models import Task, TaskStatus
from src.core.nlp_parser import parse_natural_language_task

logger = setup_logger("bot")

# Загружаем переменные окружения
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
allowed_users_str = os.getenv("TELEGRAM_ALLOWED_USERS", "")
ALLOWED_USERS = {int(x.strip()) for x in allowed_users_str.split(",") if x.strip()}

# Инициализируем БД
db = DatabaseManager(DB_PATH)
db.init_db()

if not TOKEN or TOKEN in ("YOUR_TELEGRAM_BOT_TOKEN_HERE", "your_token_here"):
    logger.critical(
        "В файле .env не указан корректный TELEGRAM_BOT_TOKEN! Пожалуйста, замените заглушку на ваш реальный токен от @BotFather."
    )
    exit(1)

bot = Bot(token=TOKEN)
dp = Dispatcher()


# Мидлварь авторизации
class AuthMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: TelegramObject, data: dict):
        user = getattr(event, "from_user", None)
        if not ALLOWED_USERS:
            if isinstance(event, Message):
                await event.answer("⚠️ Бот не настроен (отсутствует белый список).")
            elif isinstance(event, CallbackQuery):
                await event.answer("⚠️ Бот не настроен.", show_alert=True)
            return

        if not user or user.id not in ALLOWED_USERS:
            if isinstance(event, Message):
                await event.answer("❌ Доступ запрещен. Вы не находитесь в списке разрешенных пользователей.")
            elif isinstance(event, CallbackQuery):
                await event.answer("❌ Доступ запрещен.", show_alert=True)
            return
        return await handler(event, data)


dp.message.outer_middleware(AuthMiddleware())
dp.callback_query.outer_middleware(AuthMiddleware())

if ALLOWED_USERS:
    logger.info(f"Включена авторизация. Разрешенные ID: {ALLOWED_USERS}")
else:
    logger.warning(
        "TELEGRAM_ALLOWED_USERS не задан в .env! Доступ к боту заблокирован для всех пользователей (Fail-Closed)."
    )


# Определение состояний FSM для создания задачи
class AddTaskStates(StatesGroup):
    waiting_for_subject = State()
    waiting_for_description = State()
    waiting_for_deadline = State()
    waiting_for_effort = State()
    waiting_for_tags = State()


class ConfirmNLPState(StatesGroup):
    waiting_for_confirmation = State()


@dp.message(Command("cancel"))
@dp.message(F.text.casefold() == "отмена")
async def cancel_handler(message: Message, state: FSMContext) -> None:
    """Отменяет любой активный процесс создания задачи и очищает состояние FSM."""
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("ℹ️ Нет активного процесса создания задачи для отмены.")
        return

    await state.clear()
    await message.answer("❌ Создание задачи отменено.")


@dp.message(Command("start", "help"))
async def send_welcome(message: Message):
    # Регистрируем пользователя в базе данных при первом контакте
    db.register_user(message.chat.id)

    help_text = (
        "📚 *Академический дашборд Бот*\n\n"
        "Я помогу вам управлять вашим списком учебных задач прямо из Telegram! "
        "Все изменения синхронизируются с графическим интерфейсом (GUI) дашборда.\n\n"
        "📋 *Доступные команды:*\n"
        "• /list — Показать список активных задач (с кнопками выполнения)\n"
        "• /load — Показать текущую дневную нагрузку на сегодня\n"
        "• /stats — 📊 Показать дашборд статистики (KPI)\n"
        "• /grades — 🎓 Показать статистику успеваемости (GPA)\n"
        "• /done <ID> — Отметить задачу как выполненную\n"
        "• /add — Добавить новую задачу (пошаговый мастер)\n"
        "• /cancel — Отменить добавление задачи в процессе\n"
        "• /backup — Получить резервную копию базы данных (.db)\n"
    )
    await message.answer(help_text, parse_mode="Markdown")


@dp.message(Command("backup"))
async def backup_db_handler(message: Message):
    db.register_user(message.chat.id)
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


@dp.message(Command("list"))
async def list_tasks(message: Message):
    db.register_user(message.chat.id)

    tasks = db.get_all_tasks()
    active_tasks = [t for t in tasks if t.status != TaskStatus.DONE]

    if not active_tasks:
        await message.answer("🎉 У вас нет активных задач! Отличная работа!")
        return

    # Сортируем по приоритету (по убыванию)
    sorted_tasks = sorted(active_tasks, key=calculate_priority, reverse=True)

    response = "📋 *Список ваших активных задач (по приоритету):*\n\n"
    status_emoji = {TaskStatus.TODO: "📝 TODO", TaskStatus.DOING: "⚡ DOING"}

    for task in sorted_tasks:
        priority = calculate_priority(task)
        tags_str = f" `[{', '.join(task.tags)}]`" if task.tags else ""
        response += (
            f"🆔 *ID: {task.id}* | {status_emoji.get(task.status, '📝')} *{task.subject}*{tags_str}\n"
            f"🔹 *Описание:* {task.description}\n"
            f"📅 *Дедлайн:* {task.deadline} | 💪 *Сложность:* {task.effort_score} | 🌟 *Приоритет:* {priority:.2f}\n\n"
        )

    # Создаем инлайн клавиатуру для мгновенного выполнения задач
    builder = InlineKeyboardBuilder()
    for task in sorted_tasks:
        builder.button(
            text=f"✅ #{task.id} {task.subject[:12]}",
            callback_data=f"complete_{task.id}",
        )
    builder.adjust(2)  # По две кнопки в ряд

    await message.answer(response, parse_mode="Markdown", reply_markup=builder.as_markup())


@dp.callback_query(F.data.startswith("complete_"))
async def process_complete_callback(callback: CallbackQuery):
    try:
        task_id = int(callback.data.split("_")[1])
    except (IndexError, ValueError):
        await callback.answer("❌ Ошибка при чтении ID задачи.")
        return

    task = db.get_task_by_id(task_id)
    if not task:
        await callback.answer("❌ Задача не найдена!")
        return

    if task.status == TaskStatus.DONE:
        await callback.answer("ℹ️ Задача уже выполнена!")
        return

    if db.update_task_status(task_id, TaskStatus.DONE):
        await callback.answer(f"✅ Задача '{task.subject}' выполнена!")
        # Обновляем текст сообщения для подтверждения действия
        await callback.message.edit_text(
            f"🎉 *Задача выполнена!*\n"
            f"• Предмет: *{task.subject}*\n"
            f"• Описание: _{task.description}_\n\n"
            f"Отправьте команду /list, чтобы увидеть актуальный список.",
            parse_mode="Markdown",
        )
    else:
        await callback.answer("❌ Не удалось завершить задачу.")


@dp.message(Command("load"))
async def check_load(message: Message):
    today_str = date.today().isoformat()
    all_tasks = db.get_all_tasks()

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


@dp.message(Command("done"))
async def complete_task_command(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "⚠️ Пожалуйста, укажите ID задачи. Например: `/done 5`",
            parse_mode="Markdown",
        )
        return

    try:
        task_id = int(args[1].strip())
    except ValueError:
        await message.answer("❌ Некорректный ID задачи. Введите целое число.")
        return

    task = db.get_task_by_id(task_id)
    if not task:
        await message.answer(f"❌ Задача с ID {task_id} не найдена в базе данных.")
        return

    if task.status == TaskStatus.DONE:
        await message.answer(f"ℹ️ Задача *{task.subject}* (ID: {task_id}) уже выполнена!")
        return

    if db.update_task_status(task_id, TaskStatus.DONE):
        await message.answer(
            f"✅ *Задача выполнена!*\n• Предмет: *{task.subject}*\n• Описание: _{task.description}_",
            parse_mode="Markdown",
        )
    else:
        await message.answer("❌ Не удалось обновить статус задачи.")


# --- Дашборд Статистики и Оценок ---


def generate_stats_text(period: str) -> str:
    stats = db.get_kpi_stats(period)
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


@dp.message(Command("stats"))
async def stats_command_handler(message: Message):
    db.register_user(message.chat.id)
    text = generate_stats_text("week")
    markup = generate_stats_keyboard("week")
    await message.answer(text, parse_mode="Markdown", reply_markup=markup)


@dp.callback_query(F.data.startswith("stats_"))
async def process_stats_callback(callback: CallbackQuery):
    period = callback.data.split("_")[1]
    text = generate_stats_text(period)
    markup = generate_stats_keyboard(period)
    try:
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=markup)
    except Exception:
        pass
    await callback.answer()


def generate_grades_text() -> str:
    stats = db.get_grades_stats()
    subject_gpa = db.get_subject_grades_gpa()

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
        for subj, gpa in subject_gpa.items():
            text += f"• {subj}: *{gpa}*\n"
    return text


@dp.message(Command("grades"))
async def grades_command_handler(message: Message):
    db.register_user(message.chat.id)
    text = generate_grades_text()
    await message.answer(text, parse_mode="Markdown")


# --- Пошаговый FSM мастер для добавления задач ---


@dp.message(Command("add"))
async def start_add_task(message: Message, state: FSMContext) -> None:
    db.register_user(message.chat.id)
    await state.set_state(AddTaskStates.waiting_for_subject)
    await message.answer(
        "📝 *Создание новой задачи*\n\n"
        "Шаг 1: Введите *название предмета* (например: Математика, Физика):\n\n"
        "_(Отправить /cancel для отмены)_",
        parse_mode="Markdown",
    )


@dp.message(AddTaskStates.waiting_for_subject)
async def process_subject(message: Message, state: FSMContext) -> None:
    subject = message.text.strip()
    if not subject:
        await message.answer("❌ Название предмета не может быть пустым. Пожалуйста, введите предмет:")
        return

    await state.update_data(subject=subject)
    await state.set_state(AddTaskStates.waiting_for_description)
    await message.answer(f"📚 Предмет: *{subject}*\n\nШаг 2: Введите *описание задачи*:")


@dp.message(AddTaskStates.waiting_for_description)
async def process_description(message: Message, state: FSMContext) -> None:
    description = message.text.strip()
    if not description:
        await message.answer("❌ Описание не может быть пустым. Пожалуйста, введите описание задачи:")
        return

    await state.update_data(description=description)
    await state.set_state(AddTaskStates.waiting_for_deadline)
    await message.answer(
        "📅 Шаг 3: Введите *дедлайн* в формате `ГГГГ-ММ-ДД` (например: `2026-06-05`).\n\n"
        "Или напишите *«сегодня»* / *«завтра»*:"
    )


@dp.message(AddTaskStates.waiting_for_deadline)
async def process_deadline(message: Message, state: FSMContext) -> None:
    deadline_input = message.text.strip().lower()

    if deadline_input in ("сегодня", "today"):
        deadline = date.today().isoformat()
    elif deadline_input in ("завтра", "tomorrow"):
        deadline = (date.today() + timedelta(days=1)).isoformat()
    else:
        try:
            clean_date = deadline_input.split("t")[0].strip()
            parsed_date = date.fromisoformat(clean_date)
            deadline = parsed_date.isoformat()
        except ValueError:
            await message.answer(
                "❌ Неверный формат даты. Пожалуйста, введите дедлайн в формате `ГГГГ-ММ-ДД` (например: `2026-05-30`) "
                "или напишите *«сегодня»* / *«завтра»*:"
            )
            return

    await state.update_data(deadline=deadline)
    await state.set_state(AddTaskStates.waiting_for_effort)
    await message.answer(
        f"📅 Дедлайн: *{deadline}*\n\n"
        f"💪 Шаг 4: Введите *сложность* целым числом от {MIN_EFFORT} (очень легко) до {MAX_EFFORT} (очень сложно):"
    )


@dp.message(AddTaskStates.waiting_for_effort)
async def process_effort(message: Message, state: FSMContext) -> None:
    effort_input = message.text.strip()
    try:
        effort = int(effort_input)
        if not (MIN_EFFORT <= effort <= MAX_EFFORT):
            raise ValueError
    except ValueError:
        await message.answer(
            f"❌ Сложность должна быть целым числом от {MIN_EFFORT} до {MAX_EFFORT}. Введите корректное число:"
        )
        return

    await state.update_data(effort=effort)
    await state.set_state(AddTaskStates.waiting_for_tags)
    await message.answer(
        f"💪 Сложность: *{effort}*\n\n"
        f"🏷 Шаг 5: Введите *теги* через запятую (например: `Домашка, Контрольная`) "
        f"или отправьте *«нет»*, если теги не нужны:"
    )


@dp.message(AddTaskStates.waiting_for_tags)
async def process_tags(message: Message, state: FSMContext) -> None:
    tags_input = message.text.strip()
    if tags_input.lower() in ("нет", "no", "none", "-"):
        tags = []
    else:
        tags = [t.strip() for t in tags_input.split(",") if t.strip()]

    user_data = await state.get_data()
    await state.clear()

    subject = user_data["subject"]
    description = user_data["description"]
    deadline = user_data["deadline"]
    effort = user_data["effort"]

    # Сохраняем задачу
    new_task = Task(
        subject=subject,
        description=description,
        deadline=deadline,
        effort_score=effort,
        tags=tags,
        status=TaskStatus.TODO,
    )

    task_id = db.add_task(new_task)

    response = (
        f"✅ *Задача успешно добавлена с ID {task_id}!*\n\n"
        f"📚 *Предмет:* {subject}\n"
        f"📝 *Описание:* {description}\n"
        f"📅 *Дедлайн:* {deadline}\n"
        f"💪 *Сложность:* {effort}\n"
    )
    if tags:
        response += f"🏷 *Теги:* {', '.join(tags)}\n"

    # Проверяем нагрузку на дату дедлайна новой задачи
    total_load, is_overloaded = check_daily_load(db.get_all_tasks(), deadline)
    if is_overloaded:
        response += (
            f"\n⚠️ *ПРЕДУПРЕЖДЕНИЕ:* Дневная нагрузка на {deadline} превышает лимит! Текущая нагрузка: {total_load} ед."
        )

    await message.answer(response, parse_mode="Markdown")


# --- Конец пошагового FSM мастера ---

# --- Обработка естественного ввода (NLP) ---


@dp.message(F.text & ~F.text.startswith("/"))
async def handle_natural_language_message(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is not None:
        return  # Пропускаем, если активен другой процесс FSM

    db.register_user(message.chat.id)

    parsed = parse_natural_language_task(message.text)
    if not parsed:
        await message.answer(
            "ℹ️ Я не смог распознать задачу в вашем сообщении.\n"
            "Попробуйте написать в свободном формате, например:\n"
            "*«Запиши домашку по физике лаба 3 на завтра сложность 4»*",
            parse_mode="Markdown",
        )
        return

    await state.set_state(ConfirmNLPState.waiting_for_confirmation)
    await state.update_data(nlp_task=parsed)

    response = (
        f"🤖 *Распознана новая задача:*\n\n"
        f"📚 *Предмет:* {parsed['subject']}\n"
        f"📝 *Описание:* {parsed['description']}\n"
        f"📅 *Дедлайн:* {parsed['deadline']}\n"
        f"💪 *Сложность:* {parsed['effort_score']}\n\n"
        f"Всё верно? Подтвердите добавление:"
    )

    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Все верно", callback_data="nlp_confirm")
    builder.button(text="❌ Отмена", callback_data="nlp_cancel")
    builder.adjust(2)

    await message.answer(response, parse_mode="Markdown", reply_markup=builder.as_markup())


@dp.callback_query(ConfirmNLPState.waiting_for_confirmation, F.data == "nlp_confirm")
async def process_nlp_confirm(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    parsed = user_data.get("nlp_task")
    await state.clear()

    if not parsed:
        await callback.message.edit_text("❌ Данные задачи утеряны. Попробуйте заново.")
        await callback.answer()
        return

    new_task = Task(
        subject=parsed["subject"],
        description=parsed["description"],
        deadline=parsed["deadline"],
        effort_score=parsed["effort_score"],
        tags=parsed.get("tags", []),
        status=TaskStatus.TODO,
    )

    task_id = db.add_task(new_task)

    response = (
        f"✅ *Задача успешно добавлена с ID {task_id}!*\n\n"
        f"📚 *Предмет:* {parsed['subject']}\n"
        f"📝 *Описание:* {parsed['description']}\n"
        f"📅 *Дедлайн:* {parsed['deadline']}\n"
        f"💪 *Сложность:* {parsed['effort_score']}\n"
    )

    total_load, is_overloaded = check_daily_load(db.get_all_tasks(), parsed["deadline"])
    if is_overloaded:
        response += f"\n⚠️ *ПРЕДУПРЕЖДЕНИЕ:* Дневная нагрузка на {parsed['deadline']} превышает лимит! Текущая нагрузка: {total_load} ед."

    await callback.message.edit_text(response, parse_mode="Markdown")
    await callback.answer("Задача добавлена!")


@dp.callback_query(ConfirmNLPState.waiting_for_confirmation, F.data == "nlp_cancel")
async def process_nlp_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Добавление задачи отменено.")
    await callback.answer("Отменено")


@dp.callback_query(F.data.in_({"nlp_confirm", "nlp_cancel"}))
async def process_expired_nlp_callback(callback: CallbackQuery):
    await callback.answer("⚠️ Эта кнопка устарела или уже была нажата.")
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except TelegramAPIError as e:
        logger.warning(f"Error editing reply markup: {e}")


@dp.message(ConfirmNLPState.waiting_for_confirmation)
async def process_nlp_waiting_msg(message: Message):
    await message.answer(
        "⚠️ Ожидается подтверждение задачи. Воспользуйтесь кнопками под сообщением или отправьте /cancel для отмены."
    )


# --- Обработка загрузки документов (Бэкап / Восстановление) ---


@dp.message(F.document)
async def handle_document_restore(message: Message):
    db.register_user(message.chat.id)
    document = message.document
    file_name = document.file_name

    if not file_name:
        await message.answer("❌ Не удалось получить имя файла.")
        return

    ext = Path(file_name).suffix.lower()
    if ext not in (".db", ".json"):
        await message.answer(
            "❌ Поддерживаются только файлы резервных копии `.db` (SQLite) или файлы экспорта задач `.json`."
        )
        return

    temp_dir = Path(__file__).resolve().parent / "data" / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_file_path = temp_dir / file_name

    try:
        file_info = await bot.get_file(document.file_id)
        await bot.download_file(file_info.file_path, destination=temp_file_path)

        if ext == ".db":
            try:
                conn = sqlite3.connect(temp_file_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'")
                table_exists = cursor.fetchone() is not None
                if not table_exists:
                    conn.close()
                    raise ValueError("В базе данных отсутствует таблица 'tasks'.")

                cursor = conn.execute("PRAGMA table_info(tasks)")
                columns = {row["name"] for row in cursor.fetchall()}
                required = {"subject", "description", "deadline", "effort_score"}
                if not required.issubset(columns):
                    conn.close()
                    raise ValueError(
                        f"Таблица 'tasks' имеет неверную структуру. Отсутствуют обязательные колонки: {required - columns}"
                    )

                conn.close()
            except (sqlite3.Error, ValueError) as e:
                await message.answer(f"❌ Ошибка валидации базы данных: {e}")
                return

            db.rotate_local_backups()
            db.close()
            try:
                DB_PATH.with_suffix(".db-wal").unlink(missing_ok=True)
                DB_PATH.with_suffix(".db-shm").unlink(missing_ok=True)
            except OSError as e:
                logger.warning(f"Error removing WAL files: {e}")

            os.replace(temp_file_path, DB_PATH)
            db._conn = None
            db._notify_change()

            await message.answer(
                "📦 *База данных успешно восстановлена!*\n"
                "Предыдущая версия сохранена в локальной папке `data/backups/`. "
                "Интерфейс приложения обновится автоматически.",
                parse_mode="Markdown",
            )

        elif ext == ".json":
            try:
                db.import_from_json(temp_file_path)
                db._notify_change()
                await message.answer(
                    "📝 *Задачи из JSON успешно импортированы!*\n"
                    "Все новые задачи добавлены в текущую базу данных. "
                    "Интерфейс приложения обновится автоматически.",
                    parse_mode="Markdown",
                )
            except (json.JSONDecodeError, FileNotFoundError, ValueError, KeyError) as e:
                await message.answer(f"❌ Ошибка при импорте из JSON: {e}")

    except (TelegramAPIError, OSError, ValueError) as e:
        await message.answer(f"❌ Произошла ошибка при обработке файла: {e}")
    finally:
        if temp_file_path.exists():
            try:
                temp_file_path.unlink()
            except OSError as e:
                logger.warning(f"Error removing temp file: {e}")


async def send_daily_reminders():
    """Служба ежедневных напоминаний и автоматических бэкапов."""
    logger.info("Служба ежедневных напоминаний запущена.")

    # Множество для отслеживания уже отправленных напоминаний (дата + тип)
    sent_actions = set()

    while True:
        now = datetime.now()
        today_key = now.strftime("%Y-%m-%d")

        try:
            # Ежедневное напоминание в 9:00
            reminder_key = f"{today_key}_reminder"
            if now.hour >= 9 and reminder_key not in sent_actions:
                sent_actions.add(reminder_key)
                today_date = date.today()
                today_str = today_date.isoformat()
                overdue = db.get_overdue_tasks(today_str)
                today_tasks = db.get_tasks_by_date(today_str)

                if overdue or today_tasks:
                    users = db.get_all_users()
                    if users:
                        response = "🔔 *Ежедневная сводка по учебным задачам:*\n\n"
                        if overdue:
                            response += "🚨 *Просроченные задачи (сделайте в первую очередь!):*\n"
                            for task in overdue:
                                response += f"• ID {task.id} | *{task.subject}* (дедлайн: {task.deadline})\n"
                            response += "\n"
                        if today_tasks:
                            response += "📅 *Задачи на сегодня:*\n"
                            for task in today_tasks:
                                response += f"• ID {task.id} | *{task.subject}* (сложность: {task.effort_score} ед.)\n"

                        for chat_id in users:
                            try:
                                await bot.send_message(chat_id, response, parse_mode="Markdown")
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

        # Проверяем каждые 5 минут вместо часа — точнее и надёжнее
        await asyncio.sleep(300)


_bg_tasks = set()


def _reminder_done_callback(task):
    _bg_tasks.discard(task)
    if not task.cancelled():
        if task.exception():
            logger.error(f"Служба напоминаний завершилась с ошибкой: {task.exception()}. Перезапуск...")
        new_task = asyncio.create_task(send_daily_reminders())
        _bg_tasks.add(new_task)
        new_task.add_done_callback(_reminder_done_callback)


async def main_bot():
    logger.info("Запуск Telegram-бота...")
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
