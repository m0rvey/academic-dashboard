import time
from typing import Any, Awaitable, Callable, Dict, Union

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message


class RateLimitMiddleware(BaseMiddleware):
    """Middleware для ограничения частоты запросов (Messages и CallbackQueries)."""

    def __init__(self, limit: float = 1.0, cleanup_interval: int = 300):
        self.limit = limit
        self.cleanup_interval = cleanup_interval
        self.users: Dict[int, float] = {}
        self._last_cleanup = time.time()

    async def __call__(
        self,
        handler: Callable[[Union[Message, CallbackQuery], Dict[str, Any]], Awaitable[Any]],
        event: Union[Message, CallbackQuery],
        data: Dict[str, Any],
    ) -> Any:
        user = getattr(event, "from_user", None)
        if not user:
            return await handler(event, data)

        user_id = user.id
        current_time = time.time()

        # Периодическая очистка устаревших записей (prevent memory leak)
        if current_time - self._last_cleanup > self.cleanup_interval:
            self._cleanup(current_time)
            self._last_cleanup = current_time

        if user_id in self.users:
            time_passed = current_time - self.users[user_id]
            if time_passed < self.limit:
                if time_passed > (self.limit / 2):
                    if isinstance(event, Message):
                        await event.answer("⚠️ Слишком частые запросы. Пожалуйста, подождите.")
                    elif isinstance(event, CallbackQuery):
                        await event.answer("⚠️ Слишком частые запросы.", show_alert=False)
                return

        self.users[user_id] = current_time
        return await handler(event, data)

    def _cleanup(self, current_time: float) -> None:
        """Удаляет записи пользователей, которые не отправляли запросы > 2× cleanup_interval."""
        stale_threshold = current_time - (self.cleanup_interval * 2)
        stale_keys = [uid for uid, ts in self.users.items() if ts < stale_threshold]
        for uid in stale_keys:
            del self.users[uid]
