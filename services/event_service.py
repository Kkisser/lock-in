from db import queries


class NestingError(Exception):
    pass


class DuplicateNameError(Exception):
    pass


async def get_children(user_id: int, parent_id: int) -> list[dict]:
    return await queries.get_children(user_id, parent_id)


async def get_event(event_id: int) -> dict | None:
    return await queries.get_event(event_id)


async def get_path(event_id: int) -> list[dict]:
    return await queries.get_event_path(event_id)


async def get_path_string(event_id: int) -> str:
    path = await get_path(event_id)
    return " → ".join(e["name"] for e in path)


async def create_event(user_id: int, parent_id: int, name: str,
                       event_type: str) -> int:
    if parent_id == 0:
        depth = 0
    else:
        parent = await queries.get_event(parent_id)
        if parent is None:
            raise NestingError("Parent event not found.")
        if parent["type"] != "group":
            raise NestingError("Cannot create events inside an action.")
        if parent["depth"] >= 2:
            raise NestingError("Maximum nesting depth reached (group → subgroup → action).")
        if parent["depth"] == 1 and event_type == "group":
            raise NestingError("Cannot create a subgroup inside a subgroup.")
        depth = parent["depth"] + 1

    try:
        return await queries.create_event(user_id, parent_id, name, event_type, depth)
    except Exception as e:
        if "UNIQUE constraint" in str(e):
            raise DuplicateNameError(
                f"An event named '{name}' already exists in this location."
            )
        raise


async def rename_event(event_id: int, new_name: str):
    try:
        await queries.rename_event(event_id, new_name)
    except Exception as e:
        if "UNIQUE constraint" in str(e):
            raise DuplicateNameError(
                f"An event named '{new_name}' already exists in this location."
            )
        raise


async def can_delete(event_id: int) -> tuple[bool, str]:
    if await queries.has_children(event_id):
        return False, "Cannot delete: group is not empty. Delete children first."
    if await queries.has_active_session_for_event(event_id):
        return False, "Cannot delete: action has an active session. Finish it first."
    return True, ""


async def delete_event(event_id: int):
    await queries.delete_event(event_id)
