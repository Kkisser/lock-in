import asyncio
import logging

from typing import Any, Callable, Awaitable

from aiogram import Bot, Dispatcher, BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from db.schema import init_db
from db.connection import close_db
from handlers import setup_routers
from services.user_service import ensure_user
from utils.timer import TimerManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnsureUserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if user:
            if isinstance(event, Message):
                chat_id = event.chat.id
            elif isinstance(event, CallbackQuery) and event.message:
                chat_id = event.message.chat.id
            else:
                chat_id = user.id
            display_name = user.full_name or user.username or str(user.id)
            internal_id = await ensure_user(user.id, chat_id, display_name)
            data["user_id"] = internal_id
        return await handler(event, data)


async def main():
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    await init_db()

    timer_manager = TimerManager(bot)
    dp["timer_manager"] = timer_manager

    root_router = setup_routers()
    root_router.message.middleware(EnsureUserMiddleware())
    root_router.callback_query.middleware(EnsureUserMiddleware())
    dp.include_router(root_router)

    logger.info("Bot starting...")
    try:
        await dp.start_polling(bot)
    finally:
        await close_db()
        logger.info("Bot stopped.")


if __name__ == "__main__":
    asyncio.run(main())
