from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from callbacks.factory import ENavCB, ESelCB, EActCB, ELocCB, CDelCB
from services.event_service import (
    get_children, get_event, create_event, rename_event,
    delete_event, can_delete, get_path_string,
    NestingError, DuplicateNameError,
)
from services.user_service import get_user
from keyboards.editor_kb import editor_tree_kb, event_manage_kb, confirm_delete_kb
from states.editor_states import EditorFSM

router = Router()


def _can_create(parent_id: int, parent_depth: int | None) -> tuple[bool, bool]:
    """Return (can_create_group, can_create_action) based on depth."""
    if parent_id == 0:
        return True, True
    if parent_depth is None:
        return False, False
    if parent_depth == 0:
        return True, True  # depth-0 group can have subgroups and actions
    if parent_depth == 1:
        return False, True  # depth-1 subgroup can only have actions
    return False, False


@router.message(F.text == "✏️ Event Editor")
async def btn_editor(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    children = await get_children(user_id, 0)
    kb = editor_tree_kb(children, 0, can_create_group=True, can_create_action=True)
    await message.answer("✏️ Event Editor — root level", reply_markup=kb)


@router.callback_query(ENavCB.filter())
async def editor_nav(callback: CallbackQuery, callback_data: ENavCB, state: FSMContext):
    await state.clear()
    user_id = callback.from_user.id
    parent_id = callback_data.parent_id

    children = await get_children(user_id, parent_id)

    if parent_id == 0:
        title = "✏️ Event Editor — root level"
        can_g, can_a = True, True
    else:
        event = await get_event(parent_id)
        if event is None:
            await callback.answer("Event not found.", show_alert=True)
            return
        path_str = await get_path_string(parent_id)
        title = f"✏️ Event Editor — {path_str}"
        can_g, can_a = _can_create(parent_id, event["depth"])

    kb = editor_tree_kb(children, parent_id, can_g, can_a)
    await callback.message.edit_text(title, reply_markup=kb)
    await callback.answer()


@router.callback_query(ESelCB.filter())
async def editor_select(callback: CallbackQuery, callback_data: ESelCB):
    event = await get_event(callback_data.event_id)
    if event is None:
        await callback.answer("Event not found.", show_alert=True)
        return

    path_str = await get_path_string(event["id"])
    icon = "📁" if event["type"] == "group" else "🎯"
    await callback.message.edit_text(
        f"{icon} {path_str}",
        reply_markup=event_manage_kb(event),
    )
    await callback.answer()


@router.callback_query(ELocCB.filter())
async def editor_create_prompt(callback: CallbackQuery, callback_data: ELocCB, state: FSMContext):
    parent_id = callback_data.parent_id
    event_type = callback_data.event_type
    type_label = "group" if event_type == "group" else "action"

    if parent_id == 0:
        location = "root level"
    else:
        location = await get_path_string(parent_id)

    await state.set_state(EditorFSM.waiting_name)
    await state.update_data(parent_id=parent_id, event_type=event_type,
                            editor_message_id=callback.message.message_id)

    await callback.message.edit_text(
        f"Creating {type_label} in: {location}\n\nSend me the name:"
    )
    await callback.answer()


@router.message(EditorFSM.waiting_name)
async def editor_receive_name(message: Message, state: FSMContext):
    data = await state.get_data()
    parent_id = data["parent_id"]
    event_type = data["event_type"]
    name = message.text.strip()

    if not name or len(name) > 64:
        await message.answer("Name must be 1–64 characters. Try again:")
        return

    user_id = message.from_user.id
    try:
        await create_event(user_id, parent_id, name, event_type)
    except NestingError as e:
        await message.answer(f"Error: {e}")
        await state.clear()
        return
    except DuplicateNameError as e:
        await message.answer(f"Error: {e}")
        await state.clear()
        return

    await state.clear()

    children = await get_children(user_id, parent_id)
    if parent_id == 0:
        title = "✏️ Event Editor — root level"
        can_g, can_a = True, True
    else:
        parent = await get_event(parent_id)
        title = f"✏️ Event Editor — {await get_path_string(parent_id)}"
        can_g, can_a = _can_create(parent_id, parent["depth"])

    kb = editor_tree_kb(children, parent_id, can_g, can_a)
    await message.answer(f"✅ Created '{name}'!\n\n{title}", reply_markup=kb)


@router.callback_query(EActCB.filter())
async def editor_action(callback: CallbackQuery, callback_data: EActCB, state: FSMContext):
    action = callback_data.action
    event_id = callback_data.event_id

    event = await get_event(event_id)
    if event is None:
        await callback.answer("Event not found.", show_alert=True)
        return

    if action == "rename":
        await state.set_state(EditorFSM.waiting_rename)
        await state.update_data(event_id=event_id)
        path_str = await get_path_string(event_id)
        await callback.message.edit_text(
            f"Renaming: {path_str}\n\nSend me the new name:"
        )
        await callback.answer()

    elif action == "delete":
        user = await get_user(callback.from_user.id)
        if user and user["confirm_delete"]:
            path_str = await get_path_string(event_id)
            await callback.message.edit_text(
                f"Delete '{path_str}'?",
                reply_markup=confirm_delete_kb(event_id),
            )
            await callback.answer()
        else:
            await _do_delete(callback, event)


@router.message(EditorFSM.waiting_rename)
async def editor_receive_rename(message: Message, state: FSMContext):
    data = await state.get_data()
    event_id = data["event_id"]
    new_name = message.text.strip()

    if not new_name or len(new_name) > 64:
        await message.answer("Name must be 1–64 characters. Try again:")
        return

    try:
        await rename_event(event_id, new_name)
    except DuplicateNameError as e:
        await message.answer(f"Error: {e}")
        await state.clear()
        return

    await state.clear()

    event = await get_event(event_id)
    path_str = await get_path_string(event_id)
    icon = "📁" if event["type"] == "group" else "🎯"
    await message.answer(
        f"✅ Renamed to '{new_name}'!\n\n{icon} {path_str}",
        reply_markup=event_manage_kb(event),
    )


@router.callback_query(CDelCB.filter())
async def confirm_delete(callback: CallbackQuery, callback_data: CDelCB):
    if callback_data.action == "no":
        event = await get_event(callback_data.event_id)
        if event:
            path_str = await get_path_string(event["id"])
            icon = "📁" if event["type"] == "group" else "🎯"
            await callback.message.edit_text(
                f"{icon} {path_str}",
                reply_markup=event_manage_kb(event),
            )
        await callback.answer("Cancelled")
        return

    event = await get_event(callback_data.event_id)
    if event is None:
        await callback.answer("Event not found.", show_alert=True)
        return

    await _do_delete(callback, event)


async def _do_delete(callback: CallbackQuery, event: dict):
    ok, reason = await can_delete(event["id"])
    if not ok:
        await callback.answer(reason, show_alert=True)
        return

    parent_id = event["parent_id"]
    name = event["name"]
    await delete_event(event["id"])

    user_id = callback.from_user.id
    children = await get_children(user_id, parent_id)

    if parent_id == 0:
        title = "✏️ Event Editor — root level"
        can_g, can_a = True, True
    else:
        parent = await get_event(parent_id)
        title = f"✏️ Event Editor — {await get_path_string(parent_id)}"
        can_g, can_a = _can_create(parent_id, parent["depth"])

    kb = editor_tree_kb(children, parent_id, can_g, can_a)
    await callback.message.edit_text(f"🗑 Deleted '{name}'.\n\n{title}", reply_markup=kb)
    await callback.answer("Deleted")
