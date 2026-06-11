import time
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.types import CallbackQuery, Message, User

from src.bot.middlewares.throttling import RateLimitMiddleware


@pytest.mark.asyncio
async def test_rate_limit_allows_first_request():
    middleware = RateLimitMiddleware(limit=1.0)
    handler = AsyncMock(return_value="ok")

    user = MagicMock(spec=User)
    user.id = 12345
    message = MagicMock(spec=Message)
    message.from_user = user

    result = await middleware(handler, message, {})
    assert result == "ok"
    handler.assert_called_once()


@pytest.mark.asyncio
async def test_rate_limit_blocks_second_request():
    middleware = RateLimitMiddleware(limit=1.0)
    handler = AsyncMock(return_value="ok")

    user = MagicMock(spec=User)
    user.id = 12345
    message = MagicMock(spec=Message)
    message.from_user = user
    message.answer = AsyncMock()

    # First request — passes
    await middleware(handler, message, {})

    # Second request immediately — blocked
    result = await middleware(handler, message, {})
    assert result is None
    handler.assert_called_once()  # Only first call went through


@pytest.mark.asyncio
async def test_rate_limit_allows_after_interval():
    middleware = RateLimitMiddleware(limit=0.1)
    handler = AsyncMock(return_value="ok")

    user = MagicMock(spec=User)
    user.id = 12345
    message = MagicMock(spec=Message)
    message.from_user = user

    # First request
    await middleware(handler, message, {})
    assert handler.call_count == 1

    # Wait for limit to expire
    time.sleep(0.15)

    # Second request — should pass now
    await middleware(handler, message, {})
    assert handler.call_count == 2


@pytest.mark.asyncio
async def test_rate_limit_blocks_callback_query():
    middleware = RateLimitMiddleware(limit=1.0)
    handler = AsyncMock(return_value="ok")

    user = MagicMock(spec=User)
    user.id = 12345
    callback = MagicMock(spec=CallbackQuery)
    callback.from_user = user
    callback.answer = AsyncMock()

    # First request — passes
    await middleware(handler, callback, {})
    assert handler.call_count == 1

    # Second request — blocked
    result = await middleware(handler, callback, {})
    assert result is None
    assert handler.call_count == 1


@pytest.mark.asyncio
async def test_rate_limit_different_users_independent():
    middleware = RateLimitMiddleware(limit=1.0)
    handler = AsyncMock(return_value="ok")

    user1 = MagicMock(spec=User)
    user1.id = 111
    msg1 = MagicMock(spec=Message)
    msg1.from_user = user1

    user2 = MagicMock(spec=User)
    user2.id = 222
    msg2 = MagicMock(spec=Message)
    msg2.from_user = user2

    # User 1 sends
    await middleware(handler, msg1, {})
    # User 2 sends immediately — different user, should pass
    await middleware(handler, msg2, {})

    assert handler.call_count == 2


@pytest.mark.asyncio
async def test_rate_limit_cleanup_removes_old_entries():
    middleware = RateLimitMiddleware(limit=1.0, cleanup_interval=0.1)
    handler = AsyncMock(return_value="ok")

    user = MagicMock(spec=User)
    user.id = 12345
    message = MagicMock(spec=Message)
    message.from_user = user

    await middleware(handler, message, {})
    assert 12345 in middleware.users

    # Simulate time passing
    middleware.users[12345] = time.time() - 1000

    # Trigger cleanup
    middleware._cleanup(time.time())
    assert 12345 not in middleware.users


@pytest.mark.asyncio
async def test_rate_limit_skips_event_without_user():
    middleware = RateLimitMiddleware(limit=1.0)
    handler = AsyncMock(return_value="ok")

    # Message without from_user
    message = MagicMock(spec=Message)
    message.from_user = None

    result = await middleware(handler, message, {})
    assert result == "ok"
    handler.assert_called_once()
