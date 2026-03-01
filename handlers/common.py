from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from keyboards.menu import MAIN_MENU

router = Router()

HELP_TEXT = (
    "🕐 Lock-in — Time Tracking Bot\n\n"
    "▶️ Now — start/manage a session\n"
    "📊 Today — today's summary\n"
    "📈 Long-term — coming soon\n"
    "✏️ Event Editor — create/edit events\n"
    "⚙️ Settings — bot preferences\n"
    "❓ Help — this message"
)


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "Welcome to Lock-in! Track your time effectively.\n\n"
        "Use the menu below to get started.",
        reply_markup=MAIN_MENU,
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(HELP_TEXT, reply_markup=MAIN_MENU)


@router.message(F.text == "❓ Help")
async def btn_help(message: Message):
    await message.answer(HELP_TEXT, reply_markup=MAIN_MENU)
