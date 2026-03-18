from db import queries

MAX_DEPTH = 4  # actions can be at depth 0..4 (5 levels total)


class NestingError(Exception):
    pass


class DuplicateNameError(Exception):
    pass


async def get_children(user_id: int, parent_id: int) -> list[dict]:
    return await queries.get_children(user_id, parent_id)


async def get_node(node_id: int) -> dict | None:
    return await queries.get_node(node_id)


async def get_path(node_id: int) -> list[dict]:
    return await queries.get_node_path(node_id)


async def get_path_string(node_id: int) -> str:
    path = await get_path(node_id)
    return " → ".join(n["name"] for n in path)


async def create_node(user_id: int, parent_id: int, name: str,
                      node_type: str) -> int:
    if parent_id == 0:
        depth = 0
    else:
        parent = await queries.get_node(parent_id)
        if parent is None:
            raise NestingError("Parent node not found.")
        if parent["node_type"] != "group":
            raise NestingError("Cannot create nodes inside an action.")
        child_depth = parent["depth"] + 1
        if node_type == "group" and child_depth > MAX_DEPTH - 1:
            raise NestingError("Maximum group nesting depth reached.")
        if node_type == "action" and child_depth > MAX_DEPTH:
            raise NestingError("Maximum nesting depth reached.")
        depth = child_depth

    try:
        return await queries.create_node(user_id, parent_id, name, node_type, depth)
    except Exception as e:
        if "UNIQUE constraint" in str(e):
            raise DuplicateNameError(
                f"A node named '{name}' already exists in this location."
            )
        raise


async def rename_node(node_id: int, new_name: str):
    try:
        await queries.rename_node(node_id, new_name)
    except Exception as e:
        if "UNIQUE constraint" in str(e):
            raise DuplicateNameError(
                f"A node named '{new_name}' already exists in this location."
            )
        raise


async def can_delete(node_id: int) -> tuple[bool, str]:
    if await queries.has_children(node_id):
        return False, "Cannot delete: group is not empty. Delete children first."
    if await queries.has_active_session_for_node(node_id):
        return False, "Cannot delete: action has an active session. Finish it first."
    return True, ""


async def delete_node(node_id: int):
    await queries.delete_node(node_id)


async def move_node(node_id: int, target_parent_id: int):
    node = await queries.get_node(node_id)
    if node is None:
        raise NestingError("Node not found.")

    # Cannot move into itself
    if target_parent_id == node_id:
        raise NestingError("Cannot move a node into itself.")

    # Calculate new depth
    if target_parent_id == 0:
        new_depth = 0
    else:
        target = await queries.get_node(target_parent_id)
        if target is None:
            raise NestingError("Target location not found.")
        if target["node_type"] != "group":
            raise NestingError("Cannot move into an action node.")
        new_depth = target["depth"] + 1

    old_depth = node["depth"]
    depth_diff = new_depth - old_depth

    # Get all descendants
    descendants = await queries.get_descendants(node_id)
    descendant_ids = {d["id"] for d in descendants}

    # Cannot move into own descendant
    if target_parent_id in descendant_ids:
        raise NestingError("Cannot move a node into one of its descendants.")

    # Validate resulting depth
    if descendants:
        max_relative_depth = max(d["depth"] - old_depth for d in descendants)
        if new_depth + max_relative_depth > MAX_DEPTH:
            raise NestingError(
                f"Move would exceed maximum depth of {MAX_DEPTH}. "
                "Move subtree to a shallower location."
            )

    # Execute move
    await queries.move_node(node_id, target_parent_id, new_depth)

    # Update depths of all descendants
    for d in descendants:
        await queries.update_node_depth(d["id"], d["depth"] + depth_diff)
