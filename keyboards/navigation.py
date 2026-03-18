from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from callbacks.factory import NavCB, SelCB, StartCB, ENavCB  # noqa: F401 — ENavCB used in empty_*_kb
from keyboards.common import back_button


def build_tree_kb(children: list[dict], parent_id: int) -> InlineKeyboardMarkup:
    buttons = []
    for child in children:
        if child["node_type"] == "group":
            count = child.get("child_count", 0)
            count_str = f" ({count})" if count > 0 else ""
            buttons.append([InlineKeyboardButton(
                text=f"📁 {child['name']}{count_str}",
                callback_data=NavCB(parent_id=child["id"]).pack(),
            )])
        else:
            buttons.append([InlineKeyboardButton(
                text=f"🎯 {child['name']}",
                callback_data=SelCB(node_id=child["id"]).pack(),
            )])

    if parent_id != 0:
        buttons.append([back_button(parent_id, editor=False)])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def build_tree_kb_with_back(children: list[dict], current_event_parent_id: int) -> InlineKeyboardMarkup:
    buttons = []
    for child in children:
        if child["node_type"] == "group":
            count = child.get("child_count", 0)
            count_str = f" ({count})" if count > 0 else ""
            buttons.append([InlineKeyboardButton(
                text=f"📁 {child['name']}{count_str}",
                callback_data=NavCB(parent_id=child["id"]).pack(),
            )])
        else:
            buttons.append([InlineKeyboardButton(
                text=f"🎯 {child['name']}",
                callback_data=SelCB(node_id=child["id"]).pack(),
            )])

    buttons.append([back_button(current_event_parent_id, editor=False)])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def action_confirm_kb(event_id: int, parent_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="▶️ Start",
            callback_data=StartCB(node_id=event_id).pack(),
        )],
        [back_button(parent_id, editor=False)],
    ])


def empty_root_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="✏️ Open Event Editor",
            callback_data=ENavCB(parent_id=0).pack(),
        )],
    ])


def empty_group_kb(parent_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="✏️ Open Event Editor",
            callback_data=ENavCB(parent_id=0).pack(),
        )],
        [back_button(parent_id, editor=False)],
    ])
