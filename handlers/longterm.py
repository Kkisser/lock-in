from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from callbacks.factory import (
    LtItemCB, LtCounterAddCB, LtStartTimerCB, LtHistoryCB,
    LtEndRunCB, LtDeleteCB, LtNavCB, LtSelCB, LtTypeCB, LtSkipCB, LtNoTargetCB,
)
from db import queries
from services import longterm_service
from services.event_service import get_children, get_node, get_path_string_for_action
from services.session_service import start_session, get_active_session, get_session
from services.today_service import get_today_time_for_action
from services.user_service import get_user
from states.longterm_states import LongtermFSM
from keyboards.longterm_kb import (
    longterm_list_kb, longterm_item_kb, confirm_end_run_kb,
    confirm_delete_lt_kb, history_kb, lt_tree_kb, type_choice_kb, skip_kb, no_target_kb,
)
from utils.time_utils import format_duration, format_local_time, today_range_utc, parse_iso
from utils.timer import TimerManager
from keyboards.session_kb import running_kb

router = Router()


async def _build_list(user_id: int, user_tz: str) -> tuple[str, object]:
    items = await queries.get_all_longterm_items(user_id)
    if not items:
        text = "🌱 Long-term\n\nNo items yet. Press ➕ Add to start tracking something."
        return text, longterm_list_kb([], [])
    progresses = []
    for lt in items:
        progress = await longterm_service.get_today_progress(lt, user_tz)
        progresses.append(longterm_service.format_progress(lt, progress))
    return "🌱 Long-term", longterm_list_kb(items, progresses)


async def _build_item(lt_id: int, user_id: int, user_tz: str) -> tuple[str, object] | None:
    lt = await queries.get_longterm_item(lt_id)
    if lt is None:
        return None
    progress = await longterm_service.get_today_progress(lt, user_tz)
    run_day = await longterm_service.get_run_day(lt_id)
    run = await queries.get_active_run(lt_id)

    type_labels = {"counter": "🔢 Counter", "timer": "⏱ Timer", "both": "🔢+⏱ Both"}
    text = f"🌱 {lt['action_name']}\n"
    text += f"Type: {type_labels.get(lt['tracking_type'], lt['tracking_type'])}\n"
    text += f"🔥 Day {run_day}\n" if run else "No active run\n"
    text += "\nToday:\n"

    if lt["tracking_type"] in ("counter", "both"):
        done = progress.get("counter_done", 0)
        target = lt["counter_target"]
        unit = lt["counter_unit"] or "times"
        if target:
            icon = "✅" if done >= target else "⏳"
            text += f"  {icon} {done}/{target} {unit}\n"
        else:
            text += f"  🔢 {done} {unit}\n"

    if lt["tracking_type"] in ("timer", "both"):
        done_s = progress.get("timer_done", 0)
        target_s = lt["timer_target_seconds"]
        done_min = done_s // 60
        if target_s:
            target_min = target_s // 60
            icon = "✅" if done_s >= target_s else "⏳"
            text += f"  {icon} {done_min}/{target_min} min\n"
        else:
            text += f"  ⏱ {done_min} min\n"

    kb = longterm_item_kb(lt, has_active_run=run is not None)
    return text, kb


# ── Main screens ──

@router.message(F.text == "📈 Long-term")
async def btn_longterm(message: Message, user_id: int):
    user = await get_user(user_id)
    user_tz = user["timezone"] if user else "UTC"
    text, kb = await _build_list(user_id, user_tz)
    await message.answer(text, reply_markup=kb)


@router.callback_query(F.data == "lt_back")
async def lt_back(callback: CallbackQuery, user_id: int, state: FSMContext):
    await state.clear()
    user = await get_user(user_id)
    user_tz = user["timezone"] if user else "UTC"
    text, kb = await _build_list(user_id, user_tz)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(LtItemCB.filter())
async def lt_item_detail(callback: CallbackQuery, callback_data: LtItemCB, user_id: int):
    user = await get_user(user_id)
    user_tz = user["timezone"] if user else "UTC"
    result = await _build_item(callback_data.lt_id, user_id, user_tz)
    if result is None:
        await callback.answer("Item not found.", show_alert=True)
        return
    text, kb = result
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


# ── Add flow: tree navigation ──

@router.callback_query(LtNavCB.filter())
async def lt_nav(callback: CallbackQuery, callback_data: LtNavCB,
                 user_id: int, state: FSMContext):
    parent_id = callback_data.parent_id
    children = await get_children(user_id, parent_id)

    if parent_id == 0:
        back_parent_id = None
        title = "Select action to track:"
    else:
        node = await get_node(parent_id)
        if node is None:
            await callback.answer("Not found.", show_alert=True)
            return
        back_parent_id = node["parent_id"]
        title = f"📁 {node['name']}\nSelect action:"

    if not children:
        await callback.answer("This group is empty.", show_alert=True)
        return

    kb = lt_tree_kb(children, parent_id, back_parent_id)
    await callback.message.edit_text(title, reply_markup=kb)
    await callback.answer()


@router.callback_query(LtSelCB.filter())
async def lt_sel(callback: CallbackQuery, callback_data: LtSelCB,
                 user_id: int, state: FSMContext):
    node = await get_node(callback_data.node_id)
    if node is None:
        await callback.answer("Not found.", show_alert=True)
        return

    existing = await queries.get_longterm_by_action(user_id, node["action_id"])
    if existing:
        await callback.answer("This action already has a Long-term entry.", show_alert=True)
        return

    await state.update_data(lt_node_id=callback_data.node_id)
    text = f"🎯 {node['name']}\n\nChoose tracking type:"
    await callback.message.edit_text(text, reply_markup=type_choice_kb(callback_data.node_id))
    await callback.answer()


@router.callback_query(LtTypeCB.filter())
async def lt_type_chosen(callback: CallbackQuery, callback_data: LtTypeCB,
                         state: FSMContext):
    tracking_type = callback_data.tracking_type
    await state.update_data(lt_node_id=callback_data.node_id, lt_tracking_type=tracking_type)

    if tracking_type in ("counter", "both"):
        await state.set_state(LongtermFSM.waiting_counter_target)
        await callback.message.edit_text(
            "Enter daily target count (e.g. 3, 20):",
            reply_markup=no_target_kb("counter"),
        )
    else:
        await state.set_state(LongtermFSM.waiting_timer_target)
        await callback.message.edit_text(
            "Enter daily target in minutes (e.g. 20, 30):",
            reply_markup=no_target_kb("timer"),
        )
    await callback.answer()


@router.message(LongtermFSM.waiting_counter_target)
async def lt_counter_target(message: Message, state: FSMContext):
    if not message.text.strip().isdigit() or int(message.text.strip()) <= 0:
        await message.answer("Please enter a positive number (e.g. 3):")
        return
    await state.update_data(lt_counter_target=int(message.text.strip()))
    await state.set_state(LongtermFSM.waiting_counter_unit)
    await message.answer(
        "Enter the unit (e.g. times, cups, pills) — or press Skip:",
        reply_markup=skip_kb(),
    )


@router.callback_query(LtSkipCB.filter(), LongtermFSM.waiting_counter_unit)
async def lt_skip(callback: CallbackQuery, user_id: int, state: FSMContext):
    await state.update_data(lt_counter_unit="times")
    data = await state.get_data()
    if data.get("lt_tracking_type") == "both":
        await state.set_state(LongtermFSM.waiting_timer_target)
        await callback.message.edit_text(
            "Enter daily timer target in minutes (e.g. 20):",
            reply_markup=no_target_kb("timer"),
        )
    else:
        await _finish_setup(callback.message, state, user_id)
    await callback.answer()


@router.callback_query(LtNoTargetCB.filter())
async def lt_no_target(callback: CallbackQuery, callback_data: LtNoTargetCB,
                       user_id: int, state: FSMContext):
    data = await state.get_data()
    if "lt_node_id" not in data:
        await callback.answer("Setup expired. Please start over.")
        return

    if callback_data.step == "counter":
        await state.update_data(lt_counter_target=None)
        await state.set_state(LongtermFSM.waiting_counter_unit)
        await callback.message.edit_text(
            "Enter the unit (e.g. times, cups, pills) — or press Skip:",
            reply_markup=skip_kb(),
        )
    elif callback_data.step == "timer":
        await state.update_data(lt_timer_target_seconds=None)
        await _finish_setup(callback.message, state, user_id)
    await callback.answer()


@router.message(LongtermFSM.waiting_counter_unit)
async def lt_counter_unit(message: Message, user_id: int, state: FSMContext):
    unit = message.text.strip()
    if not unit or len(unit) > 32:
        await message.answer("Please enter a unit (max 32 chars):")
        return
    await state.update_data(lt_counter_unit=unit)
    data = await state.get_data()
    if data.get("lt_tracking_type") == "both":
        await state.set_state(LongtermFSM.waiting_timer_target)
        await message.answer(
            "Enter daily timer target in minutes (e.g. 20):",
            reply_markup=no_target_kb("timer"),
        )
    else:
        await _finish_setup(message, state, user_id)


@router.message(LongtermFSM.waiting_timer_target)
async def lt_timer_target(message: Message, user_id: int, state: FSMContext):
    if not message.text.strip().isdigit() or int(message.text.strip()) <= 0:
        await message.answer("Please enter a positive number of minutes (e.g. 20):")
        return
    await state.update_data(lt_timer_target_seconds=int(message.text.strip()) * 60)
    await _finish_setup(message, state, user_id)


async def _finish_setup(msg, state: FSMContext, user_id: int):
    data = await state.get_data()
    await state.clear()

    if "lt_node_id" not in data:
        await msg.answer("Setup expired. Please start over.")
        return

    node = await get_node(data["lt_node_id"])
    if node is None:
        await msg.answer("Error: action not found.")
        return

    await longterm_service.create_item(
        user_id=user_id,
        action_id=node["action_id"],
        tracking_type=data["lt_tracking_type"],
        counter_target=data.get("lt_counter_target"),
        counter_unit=data.get("lt_counter_unit"),
        timer_target_seconds=data.get("lt_timer_target_seconds"),
    )

    user = await get_user(user_id)
    user_tz = user["timezone"] if user else "UTC"
    text, kb = await _build_list(user_id, user_tz)
    await msg.answer(f"✅ Added '{node['name']}' to Long-term!\n\n{text}", reply_markup=kb)


# ── Counter ──

@router.callback_query(LtCounterAddCB.filter())
async def lt_counter_add(callback: CallbackQuery, callback_data: LtCounterAddCB,
                         user_id: int, state: FSMContext):
    lt = await queries.get_longterm_item(callback_data.lt_id)
    if lt is None:
        await callback.answer("Item not found.", show_alert=True)
        return

    if callback_data.amount == 0:
        await state.set_state(LongtermFSM.waiting_custom_amount)
        await state.update_data(lt_custom_lt_id=callback_data.lt_id)
        await callback.message.edit_text(
            f"🌱 {lt['action_name']}\n\nEnter amount to add:"
        )
        await callback.answer()
        return

    user = await get_user(user_id)
    user_tz = user["timezone"] if user else "UTC"
    await longterm_service.add_counter(callback_data.lt_id, user_id, callback_data.amount, user_tz)
    await callback.answer(f"+{callback_data.amount} added!")

    result = await _build_item(callback_data.lt_id, user_id, user_tz)
    if result:
        text, kb = result
        await callback.message.edit_text(text, reply_markup=kb)


@router.message(LongtermFSM.waiting_custom_amount)
async def lt_custom_amount(message: Message, user_id: int, state: FSMContext):
    if not message.text.strip().isdigit() or int(message.text.strip()) <= 0:
        await message.answer("Please enter a positive number:")
        return

    data = await state.get_data()
    lt_id = data.get("lt_custom_lt_id")
    amount = int(message.text.strip())
    await state.clear()

    lt = await queries.get_longterm_item(lt_id)
    if lt is None:
        await message.answer("Item not found.")
        return

    user = await get_user(user_id)
    user_tz = user["timezone"] if user else "UTC"
    await longterm_service.add_counter(lt_id, user_id, amount, user_tz)

    result = await _build_item(lt_id, user_id, user_tz)
    if result:
        text, kb = result
        await message.answer(f"+{amount} added!\n\n{text}", reply_markup=kb)


# ── Timer: start Now session from Long-term ──

@router.callback_query(LtStartTimerCB.filter())
async def lt_start_timer(callback: CallbackQuery, callback_data: LtStartTimerCB,
                         user_id: int, timer_manager: TimerManager):
    lt = await queries.get_longterm_item(callback_data.lt_id)
    if lt is None:
        await callback.answer("Item not found.", show_alert=True)
        return

    action_id = lt["action_id"]
    session_id = await start_session(
        user_id, action_id, callback.message.message_id, callback.message.chat.id
    )

    if session_id is None:
        active = await get_active_session(user_id)
        if active:
            active_path = await get_path_string_for_action(user_id, active["action_id"])
            await callback.message.edit_text(
                f"You already have an active session:\n▶️ {active_path}\n\n"
                "Finish it first before starting a new one."
            )
        await callback.answer()
        return

    session = await get_session(session_id)
    user = await get_user(user_id)
    user_tz = user["timezone"] if user else "UTC"

    path_str = await get_path_string_for_action(user_id, action_id)
    start_time = format_local_time(session["started_at"], user_tz)
    today_finished = await get_today_time_for_action(user_id, action_id, user_tz)
    today_line = f"\n📊 Today: {format_duration(today_finished)}" if today_finished > 0 else ""

    text = (f"▶️ {path_str}\n"
            f"🕐 Started: {start_time}\n"
            f"⏱ {format_duration(0)}{today_line}")
    await callback.message.edit_text(text, reply_markup=running_kb(session_id))
    timer_manager.start_timer(user_id, session_id)
    await callback.answer("Session started!")


# ── History ──

@router.callback_query(LtHistoryCB.filter())
async def lt_history(callback: CallbackQuery, callback_data: LtHistoryCB, user_id: int):
    lt = await queries.get_longterm_item(callback_data.lt_id)
    if lt is None:
        await callback.answer("Item not found.", show_alert=True)
        return

    user = await get_user(user_id)
    user_tz = user["timezone"] if user else "UTC"
    tz = ZoneInfo(user_tz)
    now_local = datetime.now(tz)

    lines = [f"📜 {lt['action_name']} — History\n", "Last 7 days:"]

    for i in range(6, -1, -1):
        day = now_local - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        day_start_utc = day_start.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        day_end_utc = day_end.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        day_label = day.strftime("%a %d")

        parts = []
        if lt["tracking_type"] in ("counter", "both"):
            cnt = await queries.get_today_counter_total(lt["id"], day_start_utc, day_end_utc)
            target = lt["counter_target"]
            if target:
                icon = "✅" if cnt >= target else ("—" if cnt == 0 else "⏳")
                parts.append(f"{icon} {cnt}/{target}")
            else:
                parts.append(f"🔢 {cnt}" if cnt > 0 else "—")
        if lt["tracking_type"] in ("timer", "both"):
            timer_s = await queries.get_today_duration_for_action(
                user_id, lt["action_id"], day_start_utc, day_end_utc
            )
            done_min = timer_s // 60
            target_s = lt["timer_target_seconds"]
            if target_s:
                target_min = target_s // 60
                icon = "✅" if timer_s >= target_s else ("—" if timer_s == 0 else "⏳")
                parts.append(f"{icon} {done_min}/{target_min}min")
            else:
                parts.append(f"⏱ {done_min}min" if timer_s > 0 else "—")

        lines.append(f"  {day_label}: {' | '.join(parts) if parts else '—'}")

    runs = await queries.get_all_runs(lt["id"])
    if len(runs) > 1:
        lines.append("\nPrevious runs:")
        for run in runs[1:]:
            start_d = parse_iso(run["started_at"]).astimezone(tz).strftime("%b %d")
            if run["ended_at"]:
                end_d = parse_iso(run["ended_at"]).astimezone(tz).strftime("%b %d")
                reason = f" ({run['end_reason']})" if run["end_reason"] else ""
                lines.append(f"  {start_d} – {end_d}{reason}")
            else:
                lines.append(f"  {start_d} – ongoing")

    await callback.message.edit_text("\n".join(lines), reply_markup=history_kb(lt["id"]))
    await callback.answer()


# ── Run management ──

@router.callback_query(LtEndRunCB.filter())
async def lt_end_run(callback: CallbackQuery, callback_data: LtEndRunCB, user_id: int):
    lt = await queries.get_longterm_item(callback_data.lt_id)
    if lt is None:
        await callback.answer("Item not found.", show_alert=True)
        return

    user = await get_user(user_id)
    user_tz = user["timezone"] if user else "UTC"
    run = await queries.get_active_run(callback_data.lt_id)

    if callback_data.confirm == 0:
        if run:
            await callback.message.edit_text(
                f"🌱 {lt['action_name']}\n\nReset the current run and start a new one?",
                reply_markup=confirm_end_run_kb(callback_data.lt_id),
            )
        else:
            await queries.create_run(callback_data.lt_id)
            await callback.answer("Run started!")
            result = await _build_item(callback_data.lt_id, user_id, user_tz)
            if result:
                text, kb = result
                await callback.message.edit_text(text, reply_markup=kb)
            return
        await callback.answer()
        return

    await longterm_service.end_and_reset_run(callback_data.lt_id)
    await callback.answer("Run reset!")
    result = await _build_item(callback_data.lt_id, user_id, user_tz)
    if result:
        text, kb = result
        await callback.message.edit_text(text, reply_markup=kb)


# ── Delete ──

@router.callback_query(LtDeleteCB.filter())
async def lt_delete(callback: CallbackQuery, callback_data: LtDeleteCB, user_id: int):
    lt = await queries.get_longterm_item(callback_data.lt_id)
    if lt is None:
        await callback.answer("Item not found.", show_alert=True)
        return

    if callback_data.confirm == 0:
        await callback.message.edit_text(
            f"Remove '{lt['action_name']}' from Long-term tracking?\n"
            "(Sessions history and action itself are NOT deleted)",
            reply_markup=confirm_delete_lt_kb(callback_data.lt_id),
        )
        await callback.answer()
        return

    name = lt["action_name"]
    await longterm_service.delete_item(callback_data.lt_id)

    user = await get_user(user_id)
    user_tz = user["timezone"] if user else "UTC"
    text, kb = await _build_list(user_id, user_tz)
    await callback.message.edit_text(f"🗑 Removed '{name}'.\n\n{text}", reply_markup=kb)
    await callback.answer("Removed")
