from aiogram import Router, F
from aiogram.types import Message

from services.today_service import get_today_summary
from services.user_service import get_user

router = Router()


@router.message(F.text == "📊 Today")
async def btn_today(message: Message):
    user_id = message.from_user.id
    user = await get_user(user_id)
    tz = user["timezone"] if user else "UTC"
    summary = await get_today_summary(user_id, tz)
    await message.answer(summary)
