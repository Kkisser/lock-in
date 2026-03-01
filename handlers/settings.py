from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from callbacks.factory import SetCB
from services.user_service import get_user, toggle_setting
from keyboards.settings_kb import settings_kb

router = Router()


@router.message(F.text == "⚙️ Settings")
async def btn_settings(message: Message):
    user_id = message.from_user.id
    user = await get_user(user_id)
    if user is None:
        await message.answer("Error: user not found.")
        return

    await message.answer(
        "⚙️ Settings",
        reply_markup=settings_kb(user["confirm_finish"], user["confirm_delete"]),
    )


@router.callback_query(SetCB.filter())
async def toggle(callback: CallbackQuery, callback_data: SetCB):
    user_id = callback.from_user.id
    key = callback_data.key

    if key not in ("confirm_finish", "confirm_delete"):
        await callback.answer("Unknown setting.", show_alert=True)
        return

    await toggle_setting(user_id, key)
    user = await get_user(user_id)
    await callback.message.edit_reply_markup(
        reply_markup=settings_kb(user["confirm_finish"], user["confirm_delete"]),
    )
    await callback.answer("Updated!")
