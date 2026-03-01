from db import queries


async def ensure_user(user_id: int):
    await queries.ensure_user(user_id)


async def get_user(user_id: int) -> dict | None:
    return await queries.get_user(user_id)


async def toggle_setting(user_id: int, key: str) -> int:
    user = await queries.get_user(user_id)
    if user is None:
        return 0
    current = user[key]
    new_value = 0 if current else 1
    await queries.update_user_setting(user_id, key, new_value)
    return new_value
