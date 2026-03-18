from db.connection import get_db
from utils.time_utils import now_iso


# ── Users ──

async def ensure_user(telegram_user_id: int, chat_id: int,
                      display_name: str | None = None) -> int:
    db = await get_db()
    ts = now_iso()
    await db.execute(
        "INSERT OR IGNORE INTO users "
        "(telegram_user_id, chat_id, display_name, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (telegram_user_id, chat_id, display_name, ts, ts),
    )
    await db.commit()
    cur = await db.execute(
        "SELECT id FROM users WHERE telegram_user_id = ?", (telegram_user_id,)
    )
    row = await cur.fetchone()
    user_id = row["id"]

    await db.execute(
        "INSERT OR IGNORE INTO user_settings (user_id, created_at, updated_at) "
        "VALUES (?, ?, ?)",
        (user_id, ts, ts),
    )
    await db.commit()
    return user_id


async def get_user_by_id(user_id: int) -> dict | None:
    db = await get_db()
    cur = await db.execute(
        "SELECT u.id, u.telegram_user_id, u.chat_id, u.display_name, u.timezone, "
        "us.confirm_finish, us.confirm_delete "
        "FROM users u "
        "LEFT JOIN user_settings us ON u.id = us.user_id "
        "WHERE u.id = ?",
        (user_id,),
    )
    row = await cur.fetchone()
    return dict(row) if row else None


async def update_user_setting(user_id: int, key: str, value: int):
    db = await get_db()
    ts = now_iso()
    await db.execute(
        f"UPDATE user_settings SET {key} = ?, updated_at = ? WHERE user_id = ?",
        (value, ts, user_id),
    )
    await db.commit()


async def update_user_timezone(user_id: int, tz: str):
    db = await get_db()
    ts = now_iso()
    await db.execute(
        "UPDATE users SET timezone = ?, updated_at = ? WHERE id = ?",
        (tz, ts, user_id),
    )
    await db.commit()


# ── Nodes ──

async def create_node(user_id: int, parent_id: int, name: str,
                      node_type: str, depth: int) -> int:
    db = await get_db()
    ts = now_iso()
    cur = await db.execute(
        "INSERT INTO nodes (user_id, parent_id, node_type, name, depth, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (user_id, parent_id, node_type, name, depth, ts, ts),
    )
    await db.commit()
    return cur.lastrowid


async def get_node(node_id: int) -> dict | None:
    db = await get_db()
    cur = await db.execute("SELECT * FROM nodes WHERE id = ?", (node_id,))
    row = await cur.fetchone()
    return dict(row) if row else None


async def get_children(user_id: int, parent_id: int) -> list[dict]:
    db = await get_db()
    cur = await db.execute(
        "SELECT * FROM nodes WHERE user_id = ? AND parent_id = ? ORDER BY name",
        (user_id, parent_id),
    )
    rows = await cur.fetchall()
    return [dict(r) for r in rows]


async def rename_node(node_id: int, new_name: str):
    db = await get_db()
    ts = now_iso()
    await db.execute(
        "UPDATE nodes SET name = ?, updated_at = ? WHERE id = ?",
        (new_name, ts, node_id),
    )
    await db.commit()


async def delete_node(node_id: int):
    db = await get_db()
    await db.execute("DELETE FROM nodes WHERE id = ?", (node_id,))
    await db.commit()


async def has_children(node_id: int) -> bool:
    db = await get_db()
    cur = await db.execute(
        "SELECT 1 FROM nodes WHERE parent_id = ? LIMIT 1", (node_id,)
    )
    return await cur.fetchone() is not None


async def get_node_path(node_id: int) -> list[dict]:
    path = []
    current_id = node_id
    while current_id and current_id != 0:
        node = await get_node(current_id)
        if node is None:
            break
        path.append(node)
        current_id = node["parent_id"]
    path.reverse()
    return path


async def get_descendants(node_id: int) -> list[dict]:
    db = await get_db()
    cur = await db.execute(
        """
        WITH RECURSIVE desc_tree AS (
            SELECT id, user_id, parent_id, node_type, name, depth, is_active
            FROM nodes WHERE parent_id = ?
            UNION ALL
            SELECT n.id, n.user_id, n.parent_id, n.node_type, n.name, n.depth, n.is_active
            FROM nodes n JOIN desc_tree d ON n.parent_id = d.id
        )
        SELECT * FROM desc_tree
        """,
        (node_id,),
    )
    rows = await cur.fetchall()
    return [dict(r) for r in rows]


async def move_node(node_id: int, new_parent_id: int, new_depth: int):
    db = await get_db()
    ts = now_iso()
    await db.execute(
        "UPDATE nodes SET parent_id = ?, depth = ?, updated_at = ? WHERE id = ?",
        (new_parent_id, new_depth, ts, node_id),
    )
    await db.commit()


async def update_node_depth(node_id: int, new_depth: int):
    db = await get_db()
    ts = now_iso()
    await db.execute(
        "UPDATE nodes SET depth = ?, updated_at = ? WHERE id = ?",
        (new_depth, ts, node_id),
    )
    await db.commit()


# ── Sessions ──

async def create_session(user_id: int, node_id: int,
                         timer_message_id: int, timer_chat_id: int) -> int:
    db = await get_db()
    ts = now_iso()
    cur = await db.execute(
        "INSERT INTO sessions "
        "(user_id, node_id, status, started_at, timer_message_id, timer_chat_id, "
        "created_at, updated_at) "
        "VALUES (?, ?, 'running', ?, ?, ?, ?, ?)",
        (user_id, node_id, ts, timer_message_id, timer_chat_id, ts, ts),
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
    ts = now_iso()
    await db.execute(
        "UPDATE sessions SET status = ?, updated_at = ? WHERE id = ?",
        (status, ts, session_id),
    )
    await db.commit()


async def finish_session(session_id: int, duration_seconds: int):
    db = await get_db()
    ts = now_iso()
    await db.execute(
        "UPDATE sessions SET status = 'finished', ended_at = ?, "
        "duration_seconds = ?, updated_at = ? WHERE id = ?",
        (ts, duration_seconds, ts, session_id),
    )
    await db.commit()


async def update_session_timer_message(session_id: int,
                                       timer_message_id: int, timer_chat_id: int):
    db = await get_db()
    ts = now_iso()
    await db.execute(
        "UPDATE sessions SET timer_message_id = ?, timer_chat_id = ?, updated_at = ? "
        "WHERE id = ?",
        (timer_message_id, timer_chat_id, ts, session_id),
    )
    await db.commit()


async def has_active_session_for_node(node_id: int) -> bool:
    db = await get_db()
    cur = await db.execute(
        "SELECT 1 FROM sessions WHERE node_id = ? AND status IN ('running', 'paused') LIMIT 1",
        (node_id,),
    )
    return await cur.fetchone() is not None


# ── Session pauses ──

async def create_session_pause(session_id: int):
    db = await get_db()
    ts = now_iso()
    await db.execute(
        "INSERT INTO session_pauses (session_id, started_at, created_at) VALUES (?, ?, ?)",
        (session_id, ts, ts),
    )
    await db.commit()


async def end_session_pause(session_id: int):
    db = await get_db()
    await db.execute(
        "UPDATE session_pauses SET ended_at = ? "
        "WHERE session_id = ? AND ended_at IS NULL",
        (now_iso(), session_id),
    )
    await db.commit()


async def get_session_pauses(session_id: int) -> list[dict]:
    db = await get_db()
    cur = await db.execute(
        "SELECT * FROM session_pauses WHERE session_id = ? ORDER BY id",
        (session_id,),
    )
    rows = await cur.fetchall()
    return [dict(r) for r in rows]


# ── Today queries ──

async def get_finished_sessions_in_range(user_id: int,
                                         start: str, end: str) -> list[dict]:
    db = await get_db()
    cur = await db.execute(
        "SELECT s.*, n.name AS node_name FROM sessions s "
        "JOIN nodes n ON s.node_id = n.id "
        "WHERE s.user_id = ? AND s.status = 'finished' "
        "AND s.started_at >= ? AND s.started_at < ? "
        "ORDER BY s.started_at",
        (user_id, start, end),
    )
    rows = await cur.fetchall()
    return [dict(r) for r in rows]
