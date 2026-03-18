from db.connection import get_db

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_user_id INTEGER NOT NULL UNIQUE,
    chat_id          INTEGER NOT NULL,
    display_name     TEXT,
    timezone         TEXT NOT NULL DEFAULT 'UTC',
    created_at       TEXT NOT NULL,
    updated_at       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS user_settings (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id        INTEGER NOT NULL UNIQUE REFERENCES users(id),
    confirm_finish INTEGER NOT NULL DEFAULT 0,
    confirm_delete INTEGER NOT NULL DEFAULT 1,
    created_at     TEXT NOT NULL,
    updated_at     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS actions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id),
    name        TEXT NOT NULL,
    description TEXT,
    is_active   INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS nodes (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(id),
    parent_id  INTEGER NOT NULL DEFAULT 0,
    node_type  TEXT NOT NULL CHECK(node_type IN ('group', 'action_ref')),
    name       TEXT NOT NULL,
    action_id  INTEGER REFERENCES actions(id),
    depth      INTEGER NOT NULL DEFAULT 0,
    is_active  INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(user_id, parent_id, name)
);

CREATE TABLE IF NOT EXISTS action_sessions (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id          INTEGER NOT NULL REFERENCES users(id),
    action_id        INTEGER NOT NULL REFERENCES actions(id) ON DELETE CASCADE,
    status           TEXT NOT NULL CHECK(status IN ('running','paused','finished')),
    started_at       TEXT NOT NULL,
    ended_at         TEXT,
    duration_seconds INTEGER,
    timer_chat_id    INTEGER,
    timer_message_id INTEGER,
    created_at       TEXT NOT NULL,
    updated_at       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS action_session_pauses (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL REFERENCES action_sessions(id) ON DELETE CASCADE,
    started_at TEXT NOT NULL,
    ended_at   TEXT,
    created_at TEXT NOT NULL
);
"""


async def init_db():
    db = await get_db()
    await db.executescript(SCHEMA)
    await db.commit()
