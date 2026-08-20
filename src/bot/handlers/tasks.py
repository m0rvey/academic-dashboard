from datetime import date, timedelta

from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.bot.dependencies import logger
from src.bot.state import BotState
from src.bot.utils import escape_md
from src.core.config import MAX_EFFORT, MIN_EFFORT
from src.core.database import DatabaseManager
from src.core.logic import calculate_priority, check_daily_load
from src.core.models import Task, TaskStatus
from src.core.nlp_parser import parse_natural_language_task

router = Router()


class AddTaskStates(StatesGroup):
    waiting_for_subject = State()
    waiting_for_description = State()
    waiting_for_deadline = State()
    waiting_for_effort = State()
    waiting_for_tags = State()


class ConfirmNLPState(StatesGroup):
    waiting_for_confirmation = State()


def build_task_list_payload(app_state: BotState):
    """Генерирует текст списка задач и интерактивную inline-клавиатуру действий."""
    sorted_tasks = app_state.get_sorted_active_tasks()
    if not sorted_tasks:
        text = "🎉 *У вас нет активных задач! Отличная работа!*"
        builder = InlineKeyboardBuilder()
        builder.button(text="➕ Добавить задачу", callback_data="add_task_start")
        builder.button(text="🔄 Обновить", callback_data="refresh_list")
        builder.adjust(2)
        return text, builder.as_markup()

    max_display_tasks = 25
    display_tasks = sorted_tasks[:max_display_tasks]

    response = "📋 *Список активных задач (по приоритету):*\n\n"
    status_emoji = {TaskStatus.TODO: "📝", TaskStatus.DOING: "⚡"}

    for idx, task in enumerate(display_tasks, start=1):
        priority = calculate_priority(task)
        tags_str = f" `[{', '.join(task.tags)}]`" if task.tags else ""
        escaped_subj = escape_md(task.subject)
        escaped_desc = escape_md(task.description)
        st_icon = status_emoji.get(task.status, "📝")
        response += (
            f"*{idx}.* {st_icon} *{escaped_subj}*{tags_str}\n"
            f"   🔹 *Описание:* {escaped_desc}\n"
            f"   📅 *Дедлайн:* {task.deadline} | 💪 *Сложность:* {task.effort_score} | 🌟 *Приоритет:* {priority:.2f}\n\n"
        )

    if len(sorted_tasks) > max_display_tasks:
        response += f"ℹ️ _Показаны первые {max_display_tasks} из {len(sorted_tasks)} задач._\n\n"

    builder = InlineKeyboardBuilder()
    for idx, task in enumerate(display_tasks, start=1):
        if task.status == TaskStatus.DOING:
            builder.button(text=f"📝 #{idx} Todo", callback_data=f"task_todo_{task.id}")
        else:
            builder.button(text=f"⚡ #{idx} В процесс", callback_data=f"task_doing_{task.id}")

        builder.button(text=f"✅ #{idx} Готово", callback_data=f"complete_{task.id}")
        builder.button(text=f"🗑️ #{idx}", callback_data=f"task_del_{task.id}")

    builder.button(text="🔄 Обновить список", callback_data="refresh_list")
    builder.button(text="➕ Новая задача", callback_data="add_task_start")

    button_counts = [3] * len(display_tasks) + [2]
    builder.adjust(*button_counts)

    return response, builder.as_markup()


@router.message(Command("list"))
async def list_tasks(message: Message, db: DatabaseManager, app_state: BotState):
    db.register_user(message.chat.id)
    text, markup = build_task_list_payload(app_state)
    await message.answer(text, parse_mode="Markdown", reply_markup=markup)


@router.callback_query(F.data == "refresh_list")
async def process_refresh_callback(callback: CallbackQuery, app_state: BotState):
    app_state.invalidate()
    text, markup = build_task_list_payload(app_state)
    try:
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=markup)
        await callback.answer("🔄 Список обновлен!")
    except Exception:
        await callback.answer("ℹ️ Список актуален.")


@router.callback_query(F.data == "add_task_start")
async def process_add_task_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer("📝 Введите название предмета (например: Математика):")
    await state.set_state(AddTaskStates.waiting_for_subject)


@router.callback_query(F.data.startswith("complete_") | F.data.startswith("task_done_"))
async def process_complete_callback(callback: CallbackQuery, db: DatabaseManager, app_state: BotState):
    try:
        task_id = int(callback.data.split("_")[-1])
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
        app_state.invalidate()
        await callback.answer(f"✅ Задача #{task_id} выполнена!")
        text, markup = build_task_list_payload(app_state)
        try:
            await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=markup)
        except Exception:
            pass
    else:
        await callback.answer("❌ Не удалось завершить задачу.")


@router.callback_query(F.data.startswith("task_doing_"))
async def process_doing_callback(callback: CallbackQuery, db: DatabaseManager, app_state: BotState):
    try:
        task_id = int(callback.data.split("_")[-1])
    except (IndexError, ValueError):
        await callback.answer("❌ Ошибка при чтении ID задачи.")
        return

    task = db.get_task_by_id(task_id)
    if not task:
        await callback.answer("❌ Задача не найдена!")
        return

    if db.update_task_status(task_id, TaskStatus.DOING):
        app_state.invalidate()
        await callback.answer(f"⚡ Задача #{task_id} в процессе!")
        text, markup = build_task_list_payload(app_state)
        try:
            await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=markup)
        except Exception:
            pass
    else:
        await callback.answer("❌ Ошибка при изменении статуса.")


@router.callback_query(F.data.startswith("task_todo_"))
async def process_todo_callback(callback: CallbackQuery, db: DatabaseManager, app_state: BotState):
    try:
        task_id = int(callback.data.split("_")[-1])
    except (IndexError, ValueError):
        await callback.answer("❌ Ошибка при чтении ID задачи.")
        return

    task = db.get_task_by_id(task_id)
    if not task:
        await callback.answer("❌ Задача не найдена!")
        return

    if db.update_task_status(task_id, TaskStatus.TODO):
        app_state.invalidate()
        await callback.answer(f"📝 Задача #{task_id} переведена в TODO!")
        text, markup = build_task_list_payload(app_state)
        try:
            await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=markup)
        except Exception:
            pass
    else:
        await callback.answer("❌ Ошибка при изменении статуса.")


@router.callback_query(F.data.startswith("task_del_"))
async def process_delete_callback(callback: CallbackQuery, db: DatabaseManager, app_state: BotState):
    try:
        task_id = int(callback.data.split("_")[-1])
    except (IndexError, ValueError):
        await callback.answer("❌ Ошибка при чтении ID задачи.")
        return

    task = db.get_task_by_id(task_id)
    if not task:
        await callback.answer("❌ Задача не найдена!")
        return

    if db.delete_task(task_id):
        app_state.invalidate()
        await callback.answer(f"🗑️ Задача #{task_id} удалена!")
        text, markup = build_task_list_payload(app_state)
        try:
            await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=markup)
        except Exception:
            pass
    else:
        await callback.answer("❌ Ошибка при удалении задачи.")



@router.message(Command("done"))
async def complete_task_command(message: Message, db: DatabaseManager, app_state: BotState):
    db.register_user(message.chat.id)
    sorted_tasks = app_state.get_sorted_active_tasks()
    args = message.text.split(maxsplit=1)

    if len(args) < 2:
        if not sorted_tasks:
            await message.answer("🎉 *У вас нет активных задач для выполнения!*", parse_mode="Markdown")
            return

        builder = InlineKeyboardBuilder()
        for idx, task in enumerate(sorted_tasks, start=1):
            builder.button(text=f"✅ {idx}. {task.subject[:12]}", callback_data=f"complete_{task.id}")
        builder.adjust(2)

        await message.answer(
            "🎯 *Выберите задачу для завершения:*\n\n_(Или укажите номер, например: `/done 1`)_",
            parse_mode="Markdown",
            reply_markup=builder.as_markup(),
        )
        return

    raw_arg = args[1].strip()
    try:
        num = int(raw_arg)
    except ValueError:
        await message.answer(
            "❌ Пожалуйста, укажите номер задачи из списка (например: `/done 1`).",
            parse_mode="Markdown",
        )
        return

    # Check ordinal number first (1 <= num <= len(sorted_tasks))
    target_task = None
    if 1 <= num <= len(sorted_tasks):
        target_task = sorted_tasks[num - 1]
    else:
        # Fallback to database ID lookup
        target_task = db.get_task_by_id(num)

    if not target_task:
        await message.answer(
            f"❌ Задача с номером или ID `{num}` не найдена.\n"
            "Посмотрите актуальный список активных задач по команде /list.",
            parse_mode="Markdown",
        )
        return

    if target_task.status == TaskStatus.DONE:
        await message.answer(
            f"ℹ️ Задача *{escape_md(target_task.subject)}* уже выполнена!",
            parse_mode="Markdown",
        )
        return

    if db.update_task_status(target_task.id, TaskStatus.DONE):
        app_state.invalidate()
        await message.answer(
            f"✅ *Задача выполнена!*\n• Предмет: *{escape_md(target_task.subject)}*\n• Описание: _{escape_md(target_task.description)}_",
            parse_mode="Markdown",
        )
    else:
        await message.answer("❌ Не удалось обновить статус задачи.")


@router.message(Command("add"))
async def start_add_task(message: Message, state: FSMContext, db: DatabaseManager) -> None:
    db.register_user(message.chat.id)
    await state.set_state(AddTaskStates.waiting_for_subject)
    await message.answer(
        "📝 *Создание новой задачи*\n\n"
        "Шаг 1: Введите *название предмета* (например: Математика, Физика):\n\n"
        "_(Отправить /cancel для отмены)_",
        parse_mode="Markdown",
    )


@router.message(AddTaskStates.waiting_for_subject)
async def process_subject(message: Message, state: FSMContext) -> None:
    subject = message.text.strip()
    if not subject:
        await message.answer("❌ Название предмета не может быть пустым. Пожалуйста, введите предмет:")
        return

    await state.update_data(subject=subject)
    await state.set_state(AddTaskStates.waiting_for_description)
    await message.answer(
        f"📚 Предмет: *{escape_md(subject)}*\n\nШаг 2: Введите *описание задачи*:", parse_mode="Markdown"
    )


@router.message(AddTaskStates.waiting_for_description)
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


@router.message(AddTaskStates.waiting_for_deadline)
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
        f"📅 Дедлайн: *{deadline}*\n\n" f"💪 Шаг 4: Введите *сложность* целым числом от {MIN_EFFORT} до {MAX_EFFORT}:"
    )


@router.message(AddTaskStates.waiting_for_effort)
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


@router.message(AddTaskStates.waiting_for_tags)
async def process_tags(message: Message, state: FSMContext, db: DatabaseManager, app_state: BotState) -> None:
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
        f"📚 *Предмет:* {escape_md(subject)}\n"
        f"📝 *Описание:* {escape_md(description)}\n"
        f"📅 *Дедлайн:* {deadline}\n"
        f"💪 *Сложность:* {effort}\n"
    )
    if tags:
        response += f"🏷 *Теги:* {escape_md(', '.join(tags))}\n"

    total_load, is_overloaded = check_daily_load(app_state.get_active_tasks(), deadline)
    if is_overloaded:
        response += (
            f"\n⚠️ *ПРЕДУПРЕЖДЕНИЕ:* Дневная нагрузка на {deadline} превышает лимит! Текущая нагрузка: {total_load} ед."
        )

    app_state.invalidate()
    await message.answer(response, parse_mode="Markdown")


@router.message(F.text & ~F.text.startswith("/"))
async def handle_natural_language_message(message: Message, state: FSMContext, db: DatabaseManager) -> None:
    current_state = await state.get_state()
    if current_state is not None:
        return

    db.register_user(message.chat.id)

    try:
        parsed = parse_natural_language_task(message.text)
    except Exception as e:
        logger.warning(f"Error parsing natural language input: {e}")
        parsed = None

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
        f"📚 *Предмет:* {escape_md(parsed['subject'])}\n"
        f"📝 *Описание:* {escape_md(parsed['description'])}\n"
        f"📅 *Дедлайн:* {parsed['deadline']}\n"
        f"💪 *Сложность:* {parsed['effort_score']}\n\n"
        f"Всё верно? Подтвердите добавление:"
    )

    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Все верно", callback_data="nlp_confirm")
    builder.button(text="❌ Отмена", callback_data="nlp_cancel")
    builder.adjust(2)

    await message.answer(response, parse_mode="Markdown", reply_markup=builder.as_markup())


@router.callback_query(ConfirmNLPState.waiting_for_confirmation, F.data == "nlp_confirm")
async def process_nlp_confirm(callback: CallbackQuery, state: FSMContext, db: DatabaseManager, app_state: BotState):
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
        f"📚 *Предмет:* {escape_md(parsed['subject'])}\n"
        f"📝 *Описание:* {escape_md(parsed['description'])}\n"
        f"📅 *Дедлайн:* {parsed['deadline']}\n"
        f"💪 *Сложность:* {parsed['effort_score']}\n"
    )

    total_load, is_overloaded = check_daily_load(app_state.get_active_tasks(), parsed["deadline"])
    if is_overloaded:
        response += f"\n⚠️ *ПРЕДУПРЕЖДЕНИЕ:* Дневная нагрузка на {parsed['deadline']} превышает лимит! Текущая нагрузка: {total_load} ед."

    app_state.invalidate()
    await callback.message.edit_text(response, parse_mode="Markdown")
    await callback.answer("Задача добавлена!")


@router.callback_query(ConfirmNLPState.waiting_for_confirmation, F.data == "nlp_cancel")
async def process_nlp_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Добавление задачи отменено.")
    await callback.answer("Отменено")


@router.callback_query(F.data.in_({"nlp_confirm", "nlp_cancel"}))
async def process_expired_nlp_callback(callback: CallbackQuery):
    await callback.answer("⚠️ Эта кнопка устарела или уже была нажата.")
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except TelegramAPIError as e:
        logger.warning(f"Error editing reply markup: {e}")


@router.message(ConfirmNLPState.waiting_for_confirmation)
async def process_nlp_waiting_msg(message: Message):
    await message.answer(
        "⚠️ Ожидается подтверждение задачи. Воспользуйтесь кнопками под сообщением или отправьте /cancel для отмены."
    )
