import asyncio

from aiogram import Bot, Dispatcher
from aiogram.types import Chat, Message, Update, User

from src.bot.handlers import tasks


async def main():
    dp = Dispatcher()
    dp.include_router(tasks.router)
    bot = Bot("12345:ABC")
    user = User(id=1700455646, is_bot=False, first_name="Test")
    chat = Chat(id=1700455646, type="private")
    msg = Message(message_id=1, date=123, chat=chat, from_user=user, text="сделай математику")
    update = Update(update_id=1, message=msg)
    try:
        await dp.feed_update(bot, update)
        print("Success!")
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")


asyncio.run(main())
