from db import queries
from utils.time_utils import parse_iso, now_utc


async def get_active_session(user_id: int) -> dict | None:
    return await queries.get_active_session(user_id)


async def start_session(user_id: int, node_id: int,
                        timer_message_id: int, timer_chat_id: int) -> int | None:
    active = await queries.get_active_session(user_id)
    if active:
        return None
    return await queries.create_session(user_id, node_id, timer_message_id, timer_chat_id)


async def pause_session(session_id: int):
    await queries.update_session_status(session_id, "paused")
    await queries.create_session_pause(session_id)


async def resume_session(session_id: int):
    await queries.end_session_pause(session_id)
    await queries.update_session_status(session_id, "running")


async def finish_session(session_id: int):
    session = await queries.get_session(session_id)
    if session and session["status"] == "paused":
        await queries.end_session_pause(session_id)
    elapsed = await calc_elapsed(session_id)
    await queries.finish_session(session_id, elapsed)


async def calc_elapsed(session_id: int) -> int:
    session = await queries.get_session(session_id)
    if session is None:
        return 0

    start = parse_iso(session["started_at"])
    end = parse_iso(session["ended_at"]) if session["ended_at"] else now_utc()
    total_seconds = int((end - start).total_seconds())

    pauses = await queries.get_session_pauses(session_id)
    pause_seconds = 0
    for p in pauses:
        p_start = parse_iso(p["started_at"])
        p_end = parse_iso(p["ended_at"]) if p["ended_at"] else now_utc()
        pause_seconds += int((p_end - p_start).total_seconds())

    return max(0, total_seconds - pause_seconds)


async def get_session(session_id: int) -> dict | None:
    return await queries.get_session(session_id)


async def update_session_message(session_id: int,
                                  timer_message_id: int, timer_chat_id: int):
    await queries.update_session_timer_message(session_id, timer_message_id, timer_chat_id)
