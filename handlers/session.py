from aiogram import Router
from aiogram.types import CallbackQuery

from callbacks.factory import SesCB
from services.session_service import (
    pause_session, resume_session, finish_session,
    calc_elapsed, get_session,
)
from services.event_service import get_path_string_for_action
from services.user_service import get_user
from utils.time_utils import format_duration, format_local_time
from utils.timer import TimerManager
from keyboards.session_kb import running_kb, paused_kb, confirm_finish_kb

router = Router()


@router.callback_query(SesCB.filter())
async def session_control(callback: CallbackQuery, callback_data: SesCB,
                          user_id: int, timer_manager: TimerManager):
    action = callback_data.action
    session_id = callback_data.session_id

    session = await get_session(session_id)
    if session is None:
        await callback.answer("Session not found.", show_alert=True)
        return

    path_str = await get_path_string_for_action(session["user_id"], session["action_id"])
    user = await get_user(user_id)
    user_tz = user["timezone"] if user else "UTC"
    start_time = format_local_time(session["started_at"], user_tz)

    if action == "pause":
        await pause_session(session_id)
        timer_manager.stop_timer(user_id)
        elapsed = await calc_elapsed(session_id)
        await callback.message.edit_text(
            f"⏸ {path_str}\n🕐 Started: {start_time}\n⏱ {format_duration(elapsed)}",
            reply_markup=paused_kb(session_id),
        )
        await callback.answer("Paused")

    elif action == "resume":
        await resume_session(session_id)
        elapsed = await calc_elapsed(session_id)
        await callback.message.edit_text(
            f"▶️ {path_str}\n🕐 Started: {start_time}\n⏱ {format_duration(elapsed)}",
            reply_markup=running_kb(session_id),
        )
        timer_manager.start_timer(user_id, session_id)
        await callback.answer("Resumed")

    elif action == "finish":
        if user and user["confirm_finish"]:
            elapsed = await calc_elapsed(session_id)
            await callback.message.edit_text(
                f"Finish session?\n\n🎯 {path_str}\n⏱ {format_duration(elapsed)}",
                reply_markup=confirm_finish_kb(session_id),
            )
            timer_manager.stop_timer(user_id)
            await callback.answer()
        else:
            await _do_finish(callback, session_id, path_str, timer_manager, user_id)

    elif action == "confirm_finish":
        await _do_finish(callback, session_id, path_str, timer_manager, user_id)

    elif action == "cancel_finish":
        session = await get_session(session_id)
        elapsed = await calc_elapsed(session_id)
        if session["status"] == "paused":
            await callback.message.edit_text(
                f"⏸ {path_str}\n🕐 Started: {start_time}\n⏱ {format_duration(elapsed)}",
                reply_markup=paused_kb(session_id),
            )
        else:
            await callback.message.edit_text(
                f"▶️ {path_str}\n🕐 Started: {start_time}\n⏱ {format_duration(elapsed)}",
                reply_markup=running_kb(session_id),
            )
            timer_manager.start_timer(user_id, session_id)
        await callback.answer("Cancelled")


async def _do_finish(callback: CallbackQuery, session_id: int,
                     path_str: str, timer_manager: TimerManager, user_id: int):
    timer_manager.stop_timer(user_id)
    await finish_session(session_id)
    elapsed = await calc_elapsed(session_id)
    await callback.message.edit_text(
        f"✅ Finished!\n\n🎯 {path_str}\n⏱ {format_duration(elapsed)}",
    )
    await callback.answer("Session finished!")
