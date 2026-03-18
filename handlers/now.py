from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from callbacks.factory import NavCB, SelCB, StartCB
from services.event_service import (
    get_children, get_node, get_path_string, get_path_string_for_action,
)
from services.session_service import (
    get_active_session, start_session, calc_elapsed, update_session_message,
)
from services.today_service import get_today_time_for_action
from services.user_service import get_user
from utils.time_utils import format_duration
from utils.timer import TimerManager
from keyboards.navigation import (
    build_tree_kb, build_tree_kb_with_back, action_confirm_kb,
    empty_root_kb, empty_group_kb,
)
from keyboards.session_kb import running_kb, paused_kb

router = Router()


def _today_line(today_seconds: int) -> str:
    if today_seconds <= 0:
        return ""
    return f"\n📊 Today: {format_duration(today_seconds)}"


@router.message(F.text == "▶️ Now")
async def btn_now(message: Message, user_id: int, timer_manager: TimerManager):
    active = await get_active_session(user_id)
    if active:
        elapsed = await calc_elapsed(active["id"])
        path_str = await get_path_string_for_action(user_id, active["action_id"])
        status_icon = "▶️" if active["status"] == "running" else "⏸"

        user = await get_user(user_id)
        user_tz = user["timezone"] if user else "UTC"
        today_finished = await get_today_time_for_action(user_id, active["action_id"], user_tz)
        total_today = today_finished + elapsed

        text = (f"{status_icon} {path_str}\n"
                f"⏱ {format_duration(elapsed)}"
                f"{_today_line(total_today)}")
        kb = running_kb(active["id"]) if active["status"] == "running" else paused_kb(active["id"])
        sent = await message.answer(text, reply_markup=kb)
        await update_session_message(active["id"], sent.message_id, sent.chat.id)
        timer_manager.start_timer(user_id, active["id"])
        return

    children = await get_children(user_id, 0)
    if not children:
        await message.answer(
            "No events yet. Use Event Editor to create groups and actions.",
            reply_markup=empty_root_kb(),
        )
        return

    await message.answer("Select an event:", reply_markup=build_tree_kb(children, 0))


@router.callback_query(NavCB.filter())
async def nav_tree(callback: CallbackQuery, callback_data: NavCB, user_id: int):
    parent_id = callback_data.parent_id

    if parent_id == 0:
        children = await get_children(user_id, 0)
        if not children:
            await callback.message.edit_text(
                "No events yet. Use Event Editor to create groups and actions.",
                reply_markup=empty_root_kb(),
            )
        else:
            await callback.message.edit_text(
                "Select an event:", reply_markup=build_tree_kb(children, 0)
            )
        await callback.answer()
        return

    node = await get_node(parent_id)
    if node is None:
        await callback.answer("Event not found.", show_alert=True)
        return

    children = await get_children(user_id, parent_id)
    if not children:
        await callback.message.edit_text(
            f"📁 {node['name']} — this group is empty.",
            reply_markup=empty_group_kb(node["parent_id"]),
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        f"📁 {node['name']}",
        reply_markup=build_tree_kb_with_back(children, node["parent_id"]),
    )
    await callback.answer()


@router.callback_query(SelCB.filter())
async def select_action(callback: CallbackQuery, callback_data: SelCB, user_id: int):
    node = await get_node(callback_data.node_id)
    if node is None:
        await callback.answer("Event not found.", show_alert=True)
        return

    path_str = await get_path_string(node["id"])

    user = await get_user(user_id)
    user_tz = user["timezone"] if user else "UTC"
    today_time = await get_today_time_for_action(user_id, node["action_id"], user_tz)

    await callback.message.edit_text(
        f"🎯 {path_str}{_today_line(today_time)}\n\nStart tracking?",
        reply_markup=action_confirm_kb(node["id"], node["parent_id"]),
    )
    await callback.answer()


@router.callback_query(StartCB.filter())
async def start_action(callback: CallbackQuery, callback_data: StartCB,
                       user_id: int, timer_manager: TimerManager):
    node_id = callback_data.node_id

    node = await get_node(node_id)
    if node is None:
        await callback.answer("Event not found.", show_alert=True)
        return

    action_id = node["action_id"]
    path_str = await get_path_string(node_id)

    user = await get_user(user_id)
    user_tz = user["timezone"] if user else "UTC"
    today_finished = await get_today_time_for_action(user_id, action_id, user_tz)

    text = f"▶️ {path_str}\n⏱ {format_duration(0)}{_today_line(today_finished)}"
    await callback.message.edit_text(text)

    session_id = await start_session(
        user_id, action_id, callback.message.message_id, callback.message.chat.id
    )

    if session_id is None:
        active = await get_active_session(user_id)
        if active:
            active_path = await get_path_string_for_action(user_id, active["action_id"])
            await callback.message.edit_text(
                f"You already have an active session:\n▶️ {active_path}\n\n"
                "Finish it first before starting a new one.",
            )
        await callback.answer()
        return

    await callback.message.edit_reply_markup(reply_markup=running_kb(session_id))
    timer_manager.start_timer(user_id, session_id)
    await callback.answer("Session started!")
