from aiogram import Router, F
from aiogram.types import Message

router = Router()


@router.message(F.text == "📈 Long-term")
async def btn_longterm(message: Message):
    await message.answer("📈 Long-term stats — coming soon!")
