from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from callbacks.factory import SetCB, TzCB

TIMEZONES = [
    "UTC",
    "Europe/Moscow",
    "Europe/Kiev",
    "Europe/London",
    "Europe/Berlin",
    "Asia/Yekaterinburg",
    "Asia/Novosibirsk",
    "America/New_York",
    "Asia/Tokyo",
    "Asia/Shanghai",
]


def settings_kb(confirm_finish: int, confirm_delete: int,
                timezone: str = "UTC") -> InlineKeyboardMarkup:
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
        [InlineKeyboardButton(
            text=f"🌍 Timezone: {timezone}",
            callback_data=SetCB(key="timezone").pack(),
        )],
    ])


def timezone_picker_kb() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=tz, callback_data=TzCB(tz=tz).pack())]
        for tz in TIMEZONES
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
