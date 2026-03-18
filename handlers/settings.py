from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from callbacks.factory import SetCB, TzCB
from services.user_service import get_user, toggle_setting, set_timezone
from keyboards.settings_kb import settings_kb, timezone_picker_kb

router = Router()


@router.message(F.text == "⚙️ Settings")
async def btn_settings(message: Message, user_id: int):
    user = await get_user(user_id)
    if user is None:
        await message.answer("Error: user not found.")
        return

    await message.answer(
        "⚙️ Settings",
        reply_markup=settings_kb(
            user["confirm_finish"], user["confirm_delete"], user["timezone"]
        ),
    )


@router.callback_query(SetCB.filter())
async def toggle(callback: CallbackQuery, callback_data: SetCB, user_id: int):
    key = callback_data.key

    if key == "timezone":
        await callback.message.edit_text(
            "🌍 Select timezone:",
            reply_markup=timezone_picker_kb(),
        )
        await callback.answer()
        return

    if key not in ("confirm_finish", "confirm_delete"):
        await callback.answer("Unknown setting.", show_alert=True)
        return

    await toggle_setting(user_id, key)
    user = await get_user(user_id)
    await callback.message.edit_reply_markup(
        reply_markup=settings_kb(
            user["confirm_finish"], user["confirm_delete"], user["timezone"]
        ),
    )
    await callback.answer("Updated!")


@router.callback_query(TzCB.filter())
async def select_timezone(callback: CallbackQuery, callback_data: TzCB, user_id: int):
    await set_timezone(user_id, callback_data.tz)
    user = await get_user(user_id)
    await callback.message.edit_text(
        "⚙️ Settings",
        reply_markup=settings_kb(
            user["confirm_finish"], user["confirm_delete"], user["timezone"]
        ),
    )
    await callback.answer(f"Timezone set to {callback_data.tz}")
