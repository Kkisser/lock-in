from db.connection import get_db
from utils.time_utils import now_iso


# ── Users ──

async def ensure_user(user_id: int):
    db = await get_db()
    await db.execute(
        "INSERT OR IGNORE INTO users (id, created_at) VALUES (?, ?)",
        (user_id, now_iso()),
    )
    await db.commit()


async def get_user(user_id: int) -> dict | None:
    db = await get_db()
    cur = await db.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = await cur.fetchone()
    return dict(row) if row else None


async def update_user_setting(user_id: int, key: str, value: int):
    db = await get_db()
    await db.execute(f"UPDATE users SET {key} = ? WHERE id = ?", (value, user_id))
    await db.commit()


# ── Events ──

async def create_event(user_id: int, parent_id: int, name: str,
                       event_type: str, depth: int) -> int:
    db = await get_db()
    cur = await db.execute(
        "INSERT INTO events (user_id, parent_id, name, type, depth, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, parent_id, name, event_type, depth, now_iso()),
    )
    await db.commit()
    return cur.lastrowid


async def get_event(event_id: int) -> dict | None:
    db = await get_db()
    cur = await db.execute("SELECT * FROM events WHERE id = ?", (event_id,))
    row = await cur.fetchone()
    return dict(row) if row else None


async def get_children(user_id: int, parent_id: int) -> list[dict]:
    db = await get_db()
    cur = await db.execute(
        "SELECT * FROM events WHERE user_id = ? AND parent_id = ? ORDER BY name",
        (user_id, parent_id),
    )
    rows = await cur.fetchall()
    return [dict(r) for r in rows]


async def rename_event(event_id: int, new_name: str):
    db = await get_db()
    await db.execute("UPDATE events SET name = ? WHERE id = ?", (new_name, event_id))
    await db.commit()


async def delete_event(event_id: int):
    db = await get_db()
    await db.execute("DELETE FROM events WHERE id = ?", (event_id,))
    await db.commit()


async def has_children(event_id: int) -> bool:
    db = await get_db()
    cur = await db.execute(
        "SELECT 1 FROM events WHERE parent_id = ? LIMIT 1", (event_id,)
    )
    return await cur.fetchone() is not None


async def get_event_path(event_id: int) -> list[dict]:
    path = []
    current_id = event_id
    while current_id and current_id != 0:
        ev = await get_event(current_id)
        if ev is None:
            break
        path.append(ev)
        current_id = ev["parent_id"]
    path.reverse()
    return path


# ── Sessions ──

async def create_session(user_id: int, event_id: int,
                         message_id: int, chat_id: int) -> int:
    db = await get_db()
    cur = await db.execute(
        "INSERT INTO sessions (user_id, event_id, status, started_at, message_id, chat_id) "
        "VALUES (?, ?, 'running', ?, ?, ?)",
        (user_id, event_id, now_iso(), message_id, chat_id),
    )
    await db.commit()
    return cur.lastrowid


async def get_active_session(user_id: int) -> dict | None:
    db = await get_db()
    cur = await db.execute(
        "SELECT * FROM sessions WHERE user_id = ? AND status IN ('running', 'paused') "
        "ORDER BY id DESC LIMIT 1",
        (user_id,),
    )
    row = await cur.fetchone()
    return dict(row) if row else None


async def get_session(session_id: int) -> dict | None:
    db = await get_db()
    cur = await db.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
    row = await cur.fetchone()
    return dict(row) if row else None


async def update_session_status(session_id: int, status: str):
    db = await get_db()
    if status == "finished":
        await db.execute(
            "UPDATE sessions SET status = ?, ended_at = ? WHERE id = ?",
            (status, now_iso(), session_id),
        )
    else:
        await db.execute(
            "UPDATE sessions SET status = ? WHERE id = ?", (status, session_id)
        )
    await db.commit()


async def update_session_message(session_id: int, message_id: int, chat_id: int):
    db = await get_db()
    await db.execute(
        "UPDATE sessions SET message_id = ?, chat_id = ? WHERE id = ?",
        (message_id, chat_id, session_id),
    )
    await db.commit()


async def has_active_session_for_event(event_id: int) -> bool:
    db = await get_db()
    cur = await db.execute(
        "SELECT 1 FROM sessions WHERE event_id = ? AND status IN ('running', 'paused') LIMIT 1",
        (event_id,),
    )
    return await cur.fetchone() is not None


# ── Pauses ──

async def create_pause(session_id: int):
    db = await get_db()
    await db.execute(
        "INSERT INTO pauses (session_id, started_at) VALUES (?, ?)",
        (session_id, now_iso()),
    )
    await db.commit()


async def end_pause(session_id: int):
    db = await get_db()
    await db.execute(
        "UPDATE pauses SET ended_at = ? WHERE session_id = ? AND ended_at IS NULL",
        (now_iso(), session_id),
    )
    await db.commit()


async def get_pauses(session_id: int) -> list[dict]:
    db = await get_db()
    cur = await db.execute(
        "SELECT * FROM pauses WHERE session_id = ? ORDER BY id", (session_id,)
    )
    rows = await cur.fetchall()
    return [dict(r) for r in rows]


# ── Today queries ──

async def get_finished_sessions_in_range(user_id: int, start: str, end: str) -> list[dict]:
    db = await get_db()
    cur = await db.execute(
        "SELECT s.*, e.name as event_name FROM sessions s "
        "JOIN events e ON s.event_id = e.id "
        "WHERE s.user_id = ? AND s.status = 'finished' "
        "AND s.started_at >= ? AND s.started_at < ? "
        "ORDER BY s.started_at",
        (user_id, start, end),
    )
    rows = await cur.fetchall()
    return [dict(r) for r in rows]
