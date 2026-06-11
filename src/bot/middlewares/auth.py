from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from src.bot.dependencies import ALLOWED_USERS


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
