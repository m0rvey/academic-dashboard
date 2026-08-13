from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.types import Chat, Document, Message, User

from src.bot.handlers.files import handle_document_restore
from src.core.database import DatabaseManager


@pytest.mark.asyncio
async def test_document_restore_rejects_non_admin():
    msg = AsyncMock(spec=Message)
    msg.from_user = User(id=999, is_bot=False, first_name="User")
    msg.chat = Chat(id=999, type="private")
    msg.document = Document(file_id="123", file_unique_id="u123", file_name="backup.db")
    msg.answer = AsyncMock()

    mock_db = MagicMock(spec=DatabaseManager)
    mock_state = MagicMock()

    with patch("src.bot.handlers.files.ADMIN_USERS", {100}):
        await handle_document_restore(msg, db=mock_db, app_state=mock_state)

    msg.answer.assert_called_once()
    assert "⛔ У вас нет прав" in msg.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_document_restore_path_traversal_sanitization():
    msg = AsyncMock(spec=Message)
    msg.from_user = User(id=100, is_bot=False, first_name="Admin")
    msg.chat = Chat(id=100, type="private")
    # Simulated malicious traversal filename
    msg.document = Document(file_id="123", file_unique_id="u123", file_name="../../malicious.db")
    msg.answer = AsyncMock()

    mock_db = MagicMock(spec=DatabaseManager)
    mock_state = MagicMock()
    mock_bot = AsyncMock()
    file_info = MagicMock()
    file_info.file_path = "tg_files/malicious.db"
    mock_bot.get_file.return_value = file_info

    with patch("src.bot.handlers.files.ADMIN_USERS", {100}), patch(
        "src.bot.handlers.files.bot", mock_bot
    ), patch("sqlite3.connect") as mock_sql_connect:
        mock_conn = MagicMock()
        mock_conn.execute.return_value.fetchone.return_value = ("tasks",)
        mock_conn.execute.return_value.fetchall.return_value = [
            {"name": "subject"},
            {"name": "description"},
            {"name": "deadline"},
            {"name": "effort_score"},
        ]
        mock_sql_connect.return_value = mock_conn

        await handle_document_restore(msg, db=mock_db, app_state=mock_state)

        mock_bot.download_file.assert_called_once()
        dest_path = mock_bot.download_file.call_args[1]["destination"]

        # Ensure the destination path does not escape data/temp
        assert isinstance(dest_path, Path)
        assert ".." not in str(dest_path)
        assert dest_path.name.startswith("restore_")
        assert dest_path.name.endswith("malicious.db")
        assert "data/temp" in str(dest_path).replace("\\", "/")


def test_proxy_url_credentials_masking():
    from src.bot.utils import mask_url_credentials

    raw_socks = "socks5://user:secret_pass_123@192.168.1.1:1080"
    masked_socks = mask_url_credentials(raw_socks)
    assert "secret_pass_123" not in masked_socks
    assert masked_socks == "socks5://user:***@192.168.1.1:1080"

    raw_http = "http://admin:my_strong_p@ss@proxy.domain.com:8080"
    masked_http = mask_url_credentials(raw_http)
    assert "my_strong_p@ss" not in masked_http
    assert masked_http == "http://admin:***@proxy.domain.com:8080"

    no_auth = "http://127.0.0.1:8080"
    assert mask_url_credentials(no_auth) == no_auth

