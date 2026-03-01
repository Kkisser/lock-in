from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from callbacks.factory import SetCB


def settings_kb(confirm_finish: int, confirm_delete: int) -> InlineKeyboardMarkup:
    cf_icon = "✅" if confirm_finish else "❌"
    cd_icon = "✅" if confirm_delete else "❌"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"Confirm finish: {cf_icon}",
            callback_data=SetCB(key="confirm_finish").pack(),
        )],
        [InlineKeyboardButton(
            text=f"Confirm delete: {cd_icon}",
            callback_data=SetCB(key="confirm_delete").pack(),
        )],
    ])
