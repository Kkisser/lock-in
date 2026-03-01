from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from callbacks.factory import ENavCB, ESelCB, EActCB, ELocCB, CDelCB
from keyboards.common import back_button


def editor_tree_kb(children: list[dict], parent_id: int,
                   can_create_group: bool, can_create_action: bool) -> InlineKeyboardMarkup:
    buttons = []
    for child in children:
        icon = "📁" if child["type"] == "group" else "🎯"
        buttons.append([InlineKeyboardButton(
            text=f"{icon} {child['name']}",
            callback_data=ESelCB(event_id=child["id"]).pack(),
        )])

    create_row = []
    if can_create_group:
        create_row.append(InlineKeyboardButton(
            text="📁+ Group",
            callback_data=ELocCB(parent_id=parent_id, event_type="group").pack(),
        ))
    if can_create_action:
        create_row.append(InlineKeyboardButton(
            text="🎯+ Action",
            callback_data=ELocCB(parent_id=parent_id, event_type="action").pack(),
        ))
    if create_row:
        buttons.append(create_row)

    if parent_id != 0:
        buttons.append([back_button(parent_id, editor=True)])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def event_manage_kb(event: dict) -> InlineKeyboardMarkup:
    event_id = event["id"]
    buttons = []

    if event["type"] == "group":
        buttons.append([InlineKeyboardButton(
            text="📂 Open",
            callback_data=ENavCB(parent_id=event_id).pack(),
        )])

    buttons.append([InlineKeyboardButton(
        text="✏️ Rename",
        callback_data=EActCB(action="rename", event_id=event_id).pack(),
    )])
    buttons.append([InlineKeyboardButton(
        text="🗑 Delete",
        callback_data=EActCB(action="delete", event_id=event_id).pack(),
    )])
    buttons.append([back_button(event["parent_id"], editor=True)])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def confirm_delete_kb(event_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Yes, delete",
                callback_data=CDelCB(action="yes", event_id=event_id).pack(),
            ),
            InlineKeyboardButton(
                text="❌ Cancel",
                callback_data=CDelCB(action="no", event_id=event_id).pack(),
            ),
        ],
    ])
