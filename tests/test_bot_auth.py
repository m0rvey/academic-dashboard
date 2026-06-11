from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.types import CallbackQuery, Message, User

from bot import ALLOWED_USERS, AuthMiddleware


@pytest.mark.asyncio
async def test_auth_middleware_allowed_user():
    # Setup mock ALLOWED_USERS for testing
    original_allowed = set(ALLOWED_USERS)
    ALLOWED_USERS.clear()
    ALLOWED_USERS.add(12345)

    try:
        middleware = AuthMiddleware()
        handler = AsyncMock(return_value="success")

        # Mock user and message
        user = MagicMock(spec=User)
        user.id = 12345
        message = MagicMock(spec=Message)
        message.from_user = user

        result = await middleware(handler, message, {})

        assert result == "success"
        handler.assert_called_once_with(message, {})
    finally:
        # Restore original
        ALLOWED_USERS.clear()
        ALLOWED_USERS.update(original_allowed)


@pytest.mark.asyncio
async def test_auth_middleware_blocked_user():
    original_allowed = set(ALLOWED_USERS)
    ALLOWED_USERS.clear()
    ALLOWED_USERS.add(12345)

    try:
        middleware = AuthMiddleware()
        handler = AsyncMock()

        # Mock user and message with blocked ID
        user = MagicMock(spec=User)
        user.id = 99999
        message = MagicMock(spec=Message)
        message.from_user = user
        message.answer = AsyncMock()

        result = await middleware(handler, message, {})

        assert result is None
        handler.assert_not_called()
        message.answer.assert_called_once_with(
            "❌ Доступ запрещен. Вы не находитесь в списке разрешенных пользователей."
        )
    finally:
        ALLOWED_USERS.clear()
        ALLOWED_USERS.update(original_allowed)


@pytest.mark.asyncio
async def test_auth_middleware_blocked_callback():
    original_allowed = set(ALLOWED_USERS)
    ALLOWED_USERS.clear()
    ALLOWED_USERS.add(12345)

    try:
        middleware = AuthMiddleware()
        handler = AsyncMock()

        # Mock user and callback query
        user = MagicMock(spec=User)
        user.id = 99999
        callback = MagicMock(spec=CallbackQuery)
        callback.from_user = user
        callback.answer = AsyncMock()

        result = await middleware(handler, callback, {})

        assert result is None
        handler.assert_not_called()
        callback.answer.assert_called_once_with("❌ Доступ запрещен.", show_alert=True)
    finally:
        ALLOWED_USERS.clear()
        ALLOWED_USERS.update(original_allowed)


@pytest.mark.asyncio
async def test_auth_middleware_empty_whitelist_message():
    original_allowed = set(ALLOWED_USERS)
    ALLOWED_USERS.clear()

    try:
        middleware = AuthMiddleware()
        handler = AsyncMock()

        user = MagicMock(spec=User)
        user.id = 12345
        message = MagicMock(spec=Message)
        message.from_user = user
        message.answer = AsyncMock()

        result = await middleware(handler, message, {})

        assert result is None
        handler.assert_not_called()
        message.answer.assert_called_once_with("⚠️ Бот не настроен (отсутствует белый список).")
    finally:
        ALLOWED_USERS.clear()
        ALLOWED_USERS.update(original_allowed)


@pytest.mark.asyncio
async def test_auth_middleware_empty_whitelist_callback():
    original_allowed = set(ALLOWED_USERS)
    ALLOWED_USERS.clear()

    try:
        middleware = AuthMiddleware()
        handler = AsyncMock()

        user = MagicMock(spec=User)
        user.id = 12345
        callback = MagicMock(spec=CallbackQuery)
        callback.from_user = user
        callback.answer = AsyncMock()

        result = await middleware(handler, callback, {})

        assert result is None
        handler.assert_not_called()
        callback.answer.assert_called_once_with("⚠️ Бот не настроен.", show_alert=True)
    finally:
        ALLOWED_USERS.clear()
        ALLOWED_USERS.update(original_allowed)
