from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from src.bot.state import BotState
from src.core.database import DatabaseManager


class DependencyMiddleware(BaseMiddleware):
    """Внедряет db и state в data каждого хендлера через Aiogram DI."""

    def __init__(self, db: DatabaseManager, state: BotState):
        self.db = db
        self.state = state

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        data["db"] = self.db
        data["state"] = self.state
        return await handler(event, data)
