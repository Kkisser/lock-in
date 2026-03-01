from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from callbacks.factory import SesCB


def running_kb(session_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="⏸ Pause",
                callback_data=SesCB(action="pause", session_id=session_id).pack(),
            ),
            InlineKeyboardButton(
                text="⏹ Finish",
                callback_data=SesCB(action="finish", session_id=session_id).pack(),
            ),
        ],
    ])


def paused_kb(session_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="▶️ Resume",
                callback_data=SesCB(action="resume", session_id=session_id).pack(),
            ),
            InlineKeyboardButton(
                text="⏹ Finish",
                callback_data=SesCB(action="finish", session_id=session_id).pack(),
            ),
        ],
    ])


def confirm_finish_kb(session_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Yes, finish",
                callback_data=SesCB(action="confirm_finish", session_id=session_id).pack(),
            ),
            InlineKeyboardButton(
                text="❌ Cancel",
                callback_data=SesCB(action="cancel_finish", session_id=session_id).pack(),
            ),
        ],
    ])
