from db.connection import get_db

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY,
    timezone    TEXT    NOT NULL DEFAULT 'UTC',
    confirm_finish INTEGER NOT NULL DEFAULT 0,
    confirm_delete INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id),
    parent_id   INTEGER NOT NULL DEFAULT 0,
    name        TEXT    NOT NULL,
    type        TEXT    NOT NULL CHECK(type IN ('group', 'action')),
    depth       INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT    NOT NULL,
    UNIQUE(user_id, parent_id, name)
);

CREATE TABLE IF NOT EXISTS sessions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id),
    event_id    INTEGER NOT NULL REFERENCES events(id),
    status      TEXT    NOT NULL CHECK(status IN ('running', 'paused', 'finished')),
    started_at  TEXT    NOT NULL,
    ended_at    TEXT,
    message_id  INTEGER,
    chat_id     INTEGER
);

CREATE TABLE IF NOT EXISTS pauses (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  INTEGER NOT NULL REFERENCES sessions(id),
    started_at  TEXT    NOT NULL,
    ended_at    TEXT
);
"""


async def init_db():
    db = await get_db()
    await db.executescript(SCHEMA)
    await db.commit()
