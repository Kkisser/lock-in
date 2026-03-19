from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from callbacks.factory import (
    LtItemCB, LtCounterAddCB, LtStartTimerCB, LtHistoryCB,
    LtEndRunCB, LtDeleteCB, LtNavCB, LtSelCB, LtTypeCB, LtSkipCB, LtNoTargetCB,
)


def longterm_list_kb(items: list[dict], progresses: list[str]) -> InlineKeyboardMarkup:
    buttons = []
    for lt, prog in zip(items, progresses):
        label = f"🌱 {lt['action_name']}"
        if prog:
            label += f"  {prog}"
        buttons.append([InlineKeyboardButton(
            text=label,
            callback_data=LtItemCB(lt_id=lt["id"]).pack(),
        )])
    buttons.append([InlineKeyboardButton(
        text="➕ Add",
        callback_data=LtNavCB(parent_id=0).pack(),
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def longterm_item_kb(lt: dict, has_active_run: bool) -> InlineKeyboardMarkup:
    buttons = []
    tt = lt["tracking_type"]

    action_row = []
    if tt in ("counter", "both"):
        action_row.append(InlineKeyboardButton(
            text="+1",
            callback_data=LtCounterAddCB(lt_id=lt["id"], amount=1).pack(),
        ))
        action_row.append(InlineKeyboardButton(
            text="+ Custom",
            callback_data=LtCounterAddCB(lt_id=lt["id"], amount=0).pack(),
        ))
    if tt in ("timer", "both"):
        action_row.append(InlineKeyboardButton(
            text="▶️ Start Now",
            callback_data=LtStartTimerCB(lt_id=lt["id"]).pack(),
        ))
    if action_row:
        buttons.append(action_row)

    buttons.append([InlineKeyboardButton(
        text="📜 History",
        callback_data=LtHistoryCB(lt_id=lt["id"]).pack(),
    )])

    run_label = "🔄 Reset run" if has_active_run else "▶️ Start run"
    buttons.append([InlineKeyboardButton(
        text=run_label,
        callback_data=LtEndRunCB(lt_id=lt["id"], confirm=0).pack(),
    )])
    buttons.append([InlineKeyboardButton(
        text="🗑 Remove",
        callback_data=LtDeleteCB(lt_id=lt["id"], confirm=0).pack(),
    )])
    buttons.append([InlineKeyboardButton(
        text="⬅️ Back",
        callback_data="lt_back",
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def confirm_end_run_kb(lt_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="✅ Yes, reset",
            callback_data=LtEndRunCB(lt_id=lt_id, confirm=1).pack(),
        ),
        InlineKeyboardButton(
            text="❌ Cancel",
            callback_data=LtItemCB(lt_id=lt_id).pack(),
        ),
    ]])


def confirm_delete_lt_kb(lt_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="✅ Yes, delete",
            callback_data=LtDeleteCB(lt_id=lt_id, confirm=1).pack(),
        ),
        InlineKeyboardButton(
            text="❌ Cancel",
            callback_data=LtItemCB(lt_id=lt_id).pack(),
        ),
    ]])


def history_kb(lt_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="⬅️ Back",
            callback_data=LtItemCB(lt_id=lt_id).pack(),
        ),
    ]])


def lt_tree_kb(children: list[dict], parent_id: int,
               back_parent_id: int | None) -> InlineKeyboardMarkup:
    buttons = []
    for child in children:
        if child["node_type"] == "group":
            count = child.get("child_count", 0)
            count_str = f" ({count})" if count > 0 else ""
            buttons.append([InlineKeyboardButton(
                text=f"📁 {child['name']}{count_str}",
                callback_data=LtNavCB(parent_id=child["id"]).pack(),
            )])
        else:
            buttons.append([InlineKeyboardButton(
                text=f"🎯 {child['name']}",
                callback_data=LtSelCB(node_id=child["id"]).pack(),
            )])
    if back_parent_id is not None:
        buttons.append([InlineKeyboardButton(
            text="⬅️ Back",
            callback_data=LtNavCB(parent_id=back_parent_id).pack(),
        )])
    buttons.append([InlineKeyboardButton(
        text="✖️ Cancel",
        callback_data="lt_back",
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def type_choice_kb(node_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🔢 Counter",
            callback_data=LtTypeCB(node_id=node_id, tracking_type="counter").pack(),
        )],
        [InlineKeyboardButton(
            text="⏱ Timer",
            callback_data=LtTypeCB(node_id=node_id, tracking_type="timer").pack(),
        )],
        [InlineKeyboardButton(
            text="🔢+⏱ Both",
            callback_data=LtTypeCB(node_id=node_id, tracking_type="both").pack(),
        )],
        [InlineKeyboardButton(text="✖️ Cancel", callback_data="lt_back")],
    ])


def skip_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="Skip", callback_data=LtSkipCB().pack()),
    ]])


def no_target_kb(step: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="⏭ No target",
            callback_data=LtNoTargetCB(step=step).pack(),
        ),
    ]])
