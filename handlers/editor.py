from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from callbacks.factory import ENavCB, ESelCB, EActCB, ELocCB, CDelCB, EMvNavCB, EMvSelCB
from services.event_service import (
    get_children, get_node, create_node, rename_node,
    delete_node, can_delete, get_path_string, move_node,
    NestingError, DuplicateNameError, MAX_DEPTH,
)
from services.user_service import get_user
from keyboards.editor_kb import (
    editor_tree_kb, event_manage_kb, confirm_delete_kb, editor_move_kb,
)
from states.editor_states import EditorFSM

router = Router()


def _can_create(parent_id: int, parent_depth: int | None,
                parent_type: str | None = None) -> tuple[bool, bool]:
    """Return (can_create_group, can_create_action) based on depth."""
    if parent_id == 0:
        return True, True
    if parent_depth is None or parent_type == "action":
        return False, False
    # groups allowed so children will be at depth ≤ MAX_DEPTH-1
    can_group = parent_depth < MAX_DEPTH - 1
    # actions allowed so children will be at depth ≤ MAX_DEPTH
    can_action = parent_depth < MAX_DEPTH
    return can_group, can_action


@router.message(F.text == "✏️ Event Editor")
async def btn_editor(message: Message, user_id: int, state: FSMContext):
    await state.clear()
    children = await get_children(user_id, 0)
    kb = editor_tree_kb(children, 0, can_create_group=True, can_create_action=True)
    await message.answer("✏️ Event Editor — root level", reply_markup=kb)


@router.callback_query(ENavCB.filter())
async def editor_nav(callback: CallbackQuery, callback_data: ENavCB,
                     user_id: int, state: FSMContext):
    await state.clear()
    parent_id = callback_data.parent_id

    children = await get_children(user_id, parent_id)

    if parent_id == 0:
        title = "✏️ Event Editor — root level"
        can_g, can_a = True, True
    else:
        node = await get_node(parent_id)
        if node is None:
            await callback.answer("Event not found.", show_alert=True)
            return
        path_str = await get_path_string(parent_id)
        title = f"✏️ Event Editor — {path_str}"
        can_g, can_a = _can_create(parent_id, node["depth"], node["node_type"])

    kb = editor_tree_kb(children, parent_id, can_g, can_a)
    await callback.message.edit_text(title, reply_markup=kb)
    await callback.answer()


@router.callback_query(ESelCB.filter())
async def editor_select(callback: CallbackQuery, callback_data: ESelCB):
    node = await get_node(callback_data.node_id)
    if node is None:
        await callback.answer("Event not found.", show_alert=True)
        return

    path_str = await get_path_string(node["id"])
    icon = "📁" if node["node_type"] == "group" else "🎯"
    await callback.message.edit_text(
        f"{icon} {path_str}",
        reply_markup=event_manage_kb(node),
    )
    await callback.answer()


@router.callback_query(ELocCB.filter())
async def editor_create_prompt(callback: CallbackQuery, callback_data: ELocCB,
                               state: FSMContext):
    parent_id = callback_data.parent_id
    event_type = callback_data.event_type
    type_label = "group" if event_type == "group" else "action"

    location = "root level" if parent_id == 0 else await get_path_string(parent_id)

    await state.set_state(EditorFSM.waiting_name)
    await state.update_data(parent_id=parent_id, event_type=event_type)

    await callback.message.edit_text(
        f"Creating {type_label} in: {location}\n\nSend me the name:"
    )
    await callback.answer()


@router.message(EditorFSM.waiting_name)
async def editor_receive_name(message: Message, user_id: int, state: FSMContext):
    data = await state.get_data()
    parent_id = data["parent_id"]
    event_type = data["event_type"]
    name = message.text.strip()

    if not name or len(name) > 64:
        await message.answer("Name must be 1–64 characters. Try again:")
        return

    try:
        await create_node(user_id, parent_id, name, event_type)
    except (NestingError, DuplicateNameError) as e:
        await message.answer(f"Error: {e}")
        await state.clear()
        return

    await state.clear()

    children = await get_children(user_id, parent_id)
    if parent_id == 0:
        title = "✏️ Event Editor — root level"
        can_g, can_a = True, True
    else:
        parent = await get_node(parent_id)
        title = f"✏️ Event Editor — {await get_path_string(parent_id)}"
        can_g, can_a = _can_create(parent_id, parent["depth"], parent["node_type"])

    kb = editor_tree_kb(children, parent_id, can_g, can_a)
    await message.answer(f"✅ Created '{name}'!\n\n{title}", reply_markup=kb)


@router.callback_query(EActCB.filter())
async def editor_action(callback: CallbackQuery, callback_data: EActCB,
                        user_id: int, state: FSMContext):
    action = callback_data.action
    node_id = callback_data.node_id

    node = await get_node(node_id)
    if node is None:
        await callback.answer("Event not found.", show_alert=True)
        return

    if action == "rename":
        await state.set_state(EditorFSM.waiting_rename)
        await state.update_data(node_id=node_id)
        path_str = await get_path_string(node_id)
        await callback.message.edit_text(
            f"Renaming: {path_str}\n\nSend me the new name:"
        )
        await callback.answer()

    elif action == "delete":
        user = await get_user(user_id)
        if user and user["confirm_delete"]:
            path_str = await get_path_string(node_id)
            await callback.message.edit_text(
                f"Delete '{path_str}'?",
                reply_markup=confirm_delete_kb(node_id),
            )
            await callback.answer()
        else:
            await _do_delete(callback, node, user_id)

    elif action == "move":
        children = await get_children(user_id, 0)
        kb = editor_move_kb(children, 0, node_id, back_parent_id=None)
        path_str = await get_path_string(node_id)
        await callback.message.edit_text(
            f"📦 Moving: {path_str}\n\nSelect destination:",
            reply_markup=kb,
        )
        await callback.answer()


@router.message(EditorFSM.waiting_rename)
async def editor_receive_rename(message: Message, state: FSMContext):
    data = await state.get_data()
    node_id = data["node_id"]
    new_name = message.text.strip()

    if not new_name or len(new_name) > 64:
        await message.answer("Name must be 1–64 characters. Try again:")
        return

    try:
        await rename_node(node_id, new_name)
    except DuplicateNameError as e:
        await message.answer(f"Error: {e}")
        await state.clear()
        return

    await state.clear()

    node = await get_node(node_id)
    path_str = await get_path_string(node_id)
    icon = "📁" if node["node_type"] == "group" else "🎯"
    await message.answer(
        f"✅ Renamed to '{new_name}'!\n\n{icon} {path_str}",
        reply_markup=event_manage_kb(node),
    )


@router.callback_query(CDelCB.filter())
async def confirm_delete(callback: CallbackQuery, callback_data: CDelCB,
                         user_id: int):
    if callback_data.action == "no":
        node = await get_node(callback_data.node_id)
        if node:
            path_str = await get_path_string(node["id"])
            icon = "📁" if node["node_type"] == "group" else "🎯"
            await callback.message.edit_text(
                f"{icon} {path_str}",
                reply_markup=event_manage_kb(node),
            )
        await callback.answer("Cancelled")
        return

    node = await get_node(callback_data.node_id)
    if node is None:
        await callback.answer("Event not found.", show_alert=True)
        return

    await _do_delete(callback, node, user_id)


async def _do_delete(callback: CallbackQuery, node: dict, user_id: int):
    ok, reason = await can_delete(node["id"])
    if not ok:
        await callback.answer(reason, show_alert=True)
        return

    parent_id = node["parent_id"]
    name = node["name"]
    await delete_node(node["id"])

    children = await get_children(user_id, parent_id)

    if parent_id == 0:
        title = "✏️ Event Editor — root level"
        can_g, can_a = True, True
    else:
        parent = await get_node(parent_id)
        title = f"✏️ Event Editor — {await get_path_string(parent_id)}"
        can_g, can_a = _can_create(parent_id, parent["depth"], parent["node_type"])

    kb = editor_tree_kb(children, parent_id, can_g, can_a)
    await callback.message.edit_text(f"🗑 Deleted '{name}'.\n\n{title}", reply_markup=kb)
    await callback.answer("Deleted")


# ── Move handlers ──

@router.callback_query(EMvNavCB.filter())
async def editor_move_nav(callback: CallbackQuery, callback_data: EMvNavCB,
                          user_id: int):
    parent_id = callback_data.parent_id
    node_id = callback_data.node_id

    children = await get_children(user_id, parent_id)

    if parent_id == 0:
        title = "📦 Move to: root level"
        back_parent_id = None
    else:
        folder = await get_node(parent_id)
        if folder is None:
            await callback.answer("Folder not found.", show_alert=True)
            return
        path_str = await get_path_string(parent_id)
        title = f"📦 Move to: {path_str}"
        back_parent_id = folder["parent_id"]

    kb = editor_move_kb(children, parent_id, node_id, back_parent_id)
    await callback.message.edit_text(title, reply_markup=kb)
    await callback.answer()


@router.callback_query(EMvSelCB.filter())
async def editor_move_sel(callback: CallbackQuery, callback_data: EMvSelCB,
                          user_id: int):
    target_parent_id = callback_data.target_parent_id
    node_id = callback_data.node_id

    try:
        await move_node(node_id, target_parent_id)
    except NestingError as e:
        await callback.answer(str(e), show_alert=True)
        return

    children = await get_children(user_id, target_parent_id)

    if target_parent_id == 0:
        title = "✅ Moved!\n\n✏️ Event Editor — root level"
        can_g, can_a = True, True
    else:
        parent = await get_node(target_parent_id)
        title = f"✅ Moved!\n\n✏️ Event Editor — {await get_path_string(target_parent_id)}"
        can_g, can_a = _can_create(target_parent_id, parent["depth"], parent["node_type"])

    kb = editor_tree_kb(children, target_parent_id, can_g, can_a)
    await callback.message.edit_text(title, reply_markup=kb)
    await callback.answer("Moved!")
