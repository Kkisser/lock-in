from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

MAIN_MENU = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="▶️ Now"), KeyboardButton(text="📊 Today")],
        [KeyboardButton(text="📈 Long-term"), KeyboardButton(text="✏️ Event Editor")],
        [KeyboardButton(text="⚙️ Settings"), KeyboardButton(text="❓ Help")],
    ],
    resize_keyboard=True,
)
