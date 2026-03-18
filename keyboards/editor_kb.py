from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from callbacks.factory import ENavCB, ESelCB, EActCB, ELocCB, CDelCB, EMvNavCB, EMvSelCB
from keyboards.common import back_button


def editor_tree_kb(children: list[dict], parent_id: int,
                   can_create_group: bool, can_create_action: bool) -> InlineKeyboardMarkup:
    buttons = []
    for child in children:
        icon = "📁" if child["node_type"] == "group" else "🎯"
        buttons.append([InlineKeyboardButton(
            text=f"{icon} {child['name']}",
            callback_data=ESelCB(node_id=child["id"]).pack(),
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


def event_manage_kb(node: dict) -> InlineKeyboardMarkup:
    node_id = node["id"]
    buttons = []

    if node["node_type"] == "group":
        buttons.append([InlineKeyboardButton(
            text="📂 Open",
            callback_data=ENavCB(parent_id=node_id).pack(),
        )])

    buttons.append([InlineKeyboardButton(
        text="✏️ Rename",
        callback_data=EActCB(action="rename", node_id=node_id).pack(),
    )])
    buttons.append([InlineKeyboardButton(
        text="📦 Move",
        callback_data=EActCB(action="move", node_id=node_id).pack(),
    )])
    buttons.append([InlineKeyboardButton(
        text="🗑 Delete",
        callback_data=EActCB(action="delete", node_id=node_id).pack(),
    )])
    buttons.append([back_button(node["parent_id"], editor=True)])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def confirm_delete_kb(node_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Yes, delete",
                callback_data=CDelCB(action="yes", node_id=node_id).pack(),
            ),
            InlineKeyboardButton(
                text="❌ Cancel",
                callback_data=CDelCB(action="no", node_id=node_id).pack(),
            ),
        ],
    ])


def editor_move_kb(children: list[dict], current_parent_id: int,
                   node_id: int, back_parent_id: int | None) -> InlineKeyboardMarkup:
    buttons = []

    buttons.append([InlineKeyboardButton(
        text="📌 Move here",
        callback_data=EMvSelCB(target_parent_id=current_parent_id, node_id=node_id).pack(),
    )])

    for child in children:
        if child["node_type"] == "group" and child["id"] != node_id:
            buttons.append([InlineKeyboardButton(
                text=f"📁 {child['name']}",
                callback_data=EMvNavCB(parent_id=child["id"], node_id=node_id).pack(),
            )])

    if back_parent_id is not None:
        buttons.append([InlineKeyboardButton(
            text="⬅️ Back",
            callback_data=EMvNavCB(parent_id=back_parent_id, node_id=node_id).pack(),
        )])

    return InlineKeyboardMarkup(inline_keyboard=buttons)
