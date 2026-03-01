from aiogram.types import InlineKeyboardButton
from callbacks.factory import NavCB, ENavCB


def back_button(parent_id: int, editor: bool = False) -> InlineKeyboardButton:
    if editor:
        return InlineKeyboardButton(
            text="⬅️ Back", callback_data=ENavCB(parent_id=parent_id).pack()
        )
    return InlineKeyboardButton(
        text="⬅️ Back", callback_data=NavCB(parent_id=parent_id).pack()
    )
