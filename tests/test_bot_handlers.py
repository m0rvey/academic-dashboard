from unittest.mock import AsyncMock, patch

import pytest
from aiogram.types import Chat, Message, User

from src.bot.handlers.commands import backup_db_handler


@pytest.mark.asyncio
async def test_backup_db_handler_not_admin():
    msg = AsyncMock(spec=Message)
    msg.from_user = User(id=999, is_bot=False, first_name="Test")
    msg.chat = Chat(id=999, type="private")
    msg.answer = AsyncMock()

    mock_db = AsyncMock()
    with patch("src.bot.handlers.commands.ADMIN_USERS", {123}):
        await backup_db_handler(msg, db=mock_db)
        msg.answer.assert_called_once_with(
            "⛔ У вас нет прав для выполнения этой команды. Доступ разрешен только администраторами."
        )
        mock_db.register_user.assert_called_once_with(999)


@pytest.mark.asyncio
async def test_backup_db_handler_admin():
    msg = AsyncMock(spec=Message)
    msg.from_user = User(id=123, is_bot=False, first_name="Admin")
    msg.chat = Chat(id=123, type="private")
    msg.answer_document = AsyncMock()

    mock_db = AsyncMock()
    with patch("src.bot.handlers.commands.ADMIN_USERS", {123}):
        with patch("src.bot.handlers.commands.DB_PATH") as mock_path:
            mock_path.exists.return_value = True
            with patch("src.bot.handlers.commands.FSInputFile"):
                await backup_db_handler(msg, db=mock_db)
                msg.answer_document.assert_called_once()
                mock_db.register_user.assert_called_once_with(123)
