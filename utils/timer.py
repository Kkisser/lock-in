import asyncio
import logging

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from services.session_service import calc_elapsed, get_session
from services.event_service import get_path_string
from utils.time_utils import format_duration
from keyboards.session_kb import running_kb, paused_kb

logger = logging.getLogger(__name__)


class TimerManager:
    def __init__(self, bot: Bot):
        self.bot = bot
        self._tasks: dict[int, asyncio.Task] = {}  # user_id -> Task

    def start_timer(self, user_id: int, session_id: int):
        self.stop_timer(user_id)
        task = asyncio.create_task(self._tick(user_id, session_id))
        self._tasks[user_id] = task

    def stop_timer(self, user_id: int):
        task = self._tasks.pop(user_id, None)
        if task and not task.done():
            task.cancel()

    async def _tick(self, user_id: int, session_id: int):
        try:
            while True:
                await asyncio.sleep(5)
                session = await get_session(session_id)
                if session is None or session["status"] == "finished":
                    break

                elapsed = await calc_elapsed(session_id)
                path_str = await get_path_string(session["node_id"])
                status_icon = "▶️" if session["status"] == "running" else "⏸"
                text = f"{status_icon} {path_str}\n⏱ {format_duration(elapsed)}"

                kb = running_kb(session_id) if session["status"] == "running" else paused_kb(session_id)

                try:
                    await self.bot.edit_message_text(
                        chat_id=session["timer_chat_id"],
                        message_id=session["timer_message_id"],
                        text=text,
                        reply_markup=kb,
                    )
                except TelegramAPIError:
                    pass
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.exception("Timer error for user %s, session %s", user_id, session_id)
