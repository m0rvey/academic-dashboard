from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.types import Chat, Message, User

from src.core.models import Task, TaskStatus


def _make_message(text: str, user_id: int = 123) -> MagicMock:
    msg = MagicMock(spec=Message)
    msg.text = text
    msg.from_user = MagicMock(spec=User)
    msg.from_user.id = user_id
    msg.chat = MagicMock(spec=Chat)
    msg.chat.id = user_id
    msg.answer = AsyncMock()
    msg.answer_document = AsyncMock()
    return msg


@pytest.mark.asyncio
async def test_start_handler_registers_user():
    from src.bot.handlers.commands import send_welcome

    msg = _make_message("/start")
    mock_db = MagicMock()
    await send_welcome(msg, db=mock_db)
    mock_db.register_user.assert_called_once_with(123)
    msg.answer.assert_called_once()
    assert "📚" in msg.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_load_handler_no_tasks():
    from src.bot.handlers.commands import check_load

    msg = _make_message("/load")
    mock_db = MagicMock()
    mock_state = MagicMock()
    mock_state.get_active_tasks.return_value = []

    await check_load(msg, db=mock_db, app_state=mock_state)
    msg.answer.assert_called_once()
    response = msg.answer.call_args[0][0]
    assert "🎉" in response


@pytest.mark.asyncio
async def test_load_handler_with_tasks():
    from src.bot.handlers.commands import check_load

    msg = _make_message("/load")
    task = Task(subject="Мат", description="Дз", deadline=date.today().isoformat(), effort_score=3)
    mock_db = MagicMock()
    mock_state = MagicMock()
    mock_state.get_active_tasks.return_value = [task]

    await check_load(msg, db=mock_db, app_state=mock_state)
    msg.answer.assert_called_once()
    response = msg.answer.call_args[0][0]
    assert "3" in response


@pytest.mark.asyncio
async def test_list_handler_no_tasks():
    from src.bot.handlers.tasks import list_tasks

    msg = _make_message("/list")
    mock_db = MagicMock()
    mock_state = MagicMock()
    mock_state.get_sorted_active_tasks.return_value = []

    await list_tasks(msg, db=mock_db, app_state=mock_state)
    msg.answer.assert_called_once()
    response = msg.answer.call_args[0][0]
    assert "🎉" in response


@pytest.mark.asyncio
async def test_list_handler_with_tasks():
    from src.bot.handlers.tasks import list_tasks

    msg = _make_message("/list")
    task = Task(id=1, subject="Мат", description="Дз", deadline=date.today().isoformat(), effort_score=5)
    mock_db = MagicMock()
    mock_state = MagicMock()
    mock_state.get_sorted_active_tasks.return_value = [task]

    await list_tasks(msg, db=mock_db, app_state=mock_state)
    msg.answer.assert_called_once()
    response = msg.answer.call_args[0][0]
    assert "Мат" in response


@pytest.mark.asyncio
async def test_done_handler_invalid_id():
    from src.bot.handlers.tasks import complete_task_command

    msg = _make_message("/done abc")
    mock_db = MagicMock()
    mock_state = MagicMock()
    await complete_task_command(msg, db=mock_db, app_state=mock_state)
    msg.answer.assert_called_once()
    assert "❌" in msg.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_done_handler_task_not_found():
    from src.bot.handlers.tasks import complete_task_command

    msg = _make_message("/done 999")
    mock_db = MagicMock()
    mock_db.get_task_by_id.return_value = None
    mock_state = MagicMock()

    await complete_task_command(msg, db=mock_db, app_state=mock_state)
    msg.answer.assert_called_once()
    assert "не найдена" in msg.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_done_handler_task_already_done():
    from src.bot.handlers.tasks import complete_task_command

    msg = _make_message("/done 1")
    task = Task(id=1, subject="Мат", description="Дз", deadline="2099-01-01", effort_score=5, status=TaskStatus.DONE)
    mock_db = MagicMock()
    mock_db.get_task_by_id.return_value = task
    mock_state = MagicMock()

    await complete_task_command(msg, db=mock_db, app_state=mock_state)
    msg.answer.assert_called_once()
    assert "ℹ️" in msg.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_done_handler_success():
    from src.bot.handlers.tasks import complete_task_command

    msg = _make_message("/done 1")
    task = Task(id=1, subject="Мат", description="Дз", deadline="2099-01-01", effort_score=5, status=TaskStatus.TODO)
    mock_db = MagicMock()
    mock_db.get_task_by_id.return_value = task
    mock_db.update_task_status.return_value = True
    mock_state = MagicMock()

    await complete_task_command(msg, db=mock_db, app_state=mock_state)
    msg.answer.assert_called_once()
    assert "✅" in msg.answer.call_args[0][0]
    mock_state.invalidate.assert_called_once()


@pytest.mark.asyncio
async def test_add_handler_starts_fsm():
    from src.bot.handlers.tasks import start_add_task

    msg = _make_message("/add")
    fsm_state = AsyncMock()
    fsm_state.get_state = AsyncMock(return_value=None)
    mock_db = MagicMock()

    await start_add_task(msg, state=fsm_state, db=mock_db)
    fsm_state.set_state.assert_called_once()
    msg.answer.assert_called_once()
    assert "📝" in msg.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_stats_handler():
    from src.bot.handlers.dashboards import stats_command_handler

    msg = _make_message("/stats")
    mock_db = MagicMock()
    mock_state = MagicMock()
    mock_state.get_kpi_stats.return_value = {"total": 10, "completed": 5, "overdue": 2, "high_priority": 3}

    await stats_command_handler(msg, db=mock_db, app_state=mock_state)
    msg.answer.assert_called_once()
    response = msg.answer.call_args[0][0]
    assert "📊" in response


@pytest.mark.asyncio
async def test_grades_handler_no_data():
    from src.bot.handlers.dashboards import grades_command_handler

    msg = _make_message("/grades")
    mock_db = MagicMock()
    mock_state = MagicMock()
    mock_state.get_grades_stats.return_value = {}
    mock_state.get_subject_grades_gpa.return_value = {}

    await grades_command_handler(msg, db=mock_db, app_state=mock_state)
    msg.answer.assert_called_once()
    response = msg.answer.call_args[0][0]
    assert "Нет данных" in response


@pytest.mark.asyncio
async def test_process_doing_callback():
    from aiogram.types import CallbackQuery

    from src.bot.handlers.tasks import process_doing_callback

    cb = MagicMock(spec=CallbackQuery)
    cb.data = "task_doing_1"
    cb.answer = AsyncMock()
    cb.message = MagicMock()
    cb.message.edit_text = AsyncMock()

    mock_db = MagicMock()
    task = Task(id=1, subject="Физика", description="Лаба", deadline=date.today().isoformat(), effort_score=4)
    mock_db.get_task_by_id.return_value = task
    mock_db.update_task_status.return_value = True

    mock_state = MagicMock()
    mock_state.get_sorted_active_tasks.return_value = [task]

    await process_doing_callback(cb, db=mock_db, app_state=mock_state)
    mock_db.update_task_status.assert_called_once_with(1, TaskStatus.DOING)
    cb.answer.assert_called_once()
    assert "в процессе" in cb.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_process_delete_callback():
    from aiogram.types import CallbackQuery

    from src.bot.handlers.tasks import process_delete_callback

    cb = MagicMock(spec=CallbackQuery)
    cb.data = "task_del_1"
    cb.answer = AsyncMock()
    cb.message = MagicMock()
    cb.message.edit_text = AsyncMock()

    mock_db = MagicMock()
    task = Task(id=1, subject="Физика", description="Лаба", deadline=date.today().isoformat(), effort_score=4)
    mock_db.get_task_by_id.return_value = task
    mock_db.delete_task.return_value = True

    mock_state = MagicMock()
    mock_state.get_sorted_active_tasks.return_value = []

    await process_delete_callback(cb, db=mock_db, app_state=mock_state)
    mock_db.delete_task.assert_called_once_with(1)
    cb.answer.assert_called_once()
    assert "удалена" in cb.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_settings_command():
    from src.bot.handlers.commands import settings_command

    msg = _make_message("/settings")
    mock_db = MagicMock()
    mock_db.get_user_reminder_hour.return_value = 9

    await settings_command(msg, db=mock_db)
    mock_db.register_user.assert_called_once_with(123)
    msg.answer.assert_called_once()
    assert "Настройки" in msg.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_process_set_reminder_callback():
    from aiogram.types import CallbackQuery

    from src.bot.handlers.commands import process_set_reminder_callback

    cb = MagicMock(spec=CallbackQuery)
    cb.data = "set_rem_18"
    cb.answer = AsyncMock()
    cb.message = MagicMock()
    cb.message.chat = MagicMock()
    cb.message.chat.id = 123
    cb.message.edit_text = AsyncMock()

    mock_db = MagicMock()
    mock_db.set_user_reminder_hour.return_value = True

    await process_set_reminder_callback(cb, db=mock_db)
    mock_db.set_user_reminder_hour.assert_called_once_with(123, 18)
    cb.answer.assert_called_once()
    assert "18:00" in cb.answer.call_args[0][0]


