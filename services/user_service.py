from db import queries


async def ensure_user(telegram_user_id: int, chat_id: int,
                      display_name: str | None = None) -> int:
    """Ensure user exists and return internal user_id."""
    return await queries.ensure_user(telegram_user_id, chat_id, display_name)


async def get_user(user_id: int) -> dict | None:
    return await queries.get_user_by_id(user_id)


async def toggle_setting(user_id: int, key: str) -> int:
    user = await queries.get_user_by_id(user_id)
    if user is None:
        return 0
    current = user[key]
    new_value = 0 if current else 1
    await queries.update_user_setting(user_id, key, new_value)
    return new_value


async def set_timezone(user_id: int, tz: str):
    await queries.update_user_timezone(user_id, tz)
