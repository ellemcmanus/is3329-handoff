"""SQLite connection and table set-up (prototype stand-in for a managed cloud database)."""
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS guests (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    room TEXT NOT NULL,
    stay_start TEXT NOT NULL,
    stay_end TEXT NOT NULL,
    allergies TEXT NOT NULL DEFAULT '[]'
);
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY,
    guest_id INTEGER NOT NULL REFERENCES guests(id),
    note_text TEXT NOT NULL,
    created_at TEXT NOT NULL,
    ai_failed INTEGER NOT NULL DEFAULT 0,
    flags TEXT NOT NULL DEFAULT '[]'
);
CREATE TABLE IF NOT EXISTS handoff_items (
    id INTEGER PRIMARY KEY,
    note_id INTEGER NOT NULL REFERENCES notes(id),
    guest_id INTEGER NOT NULL REFERENCES guests(id),
    request_type TEXT NOT NULL,
    details TEXT NOT NULL,
    source_text TEXT NOT NULL,
    flags TEXT NOT NULL DEFAULT '[]',
    confirmed_by TEXT,
    confirmed_at TEXT
);
"""


def connect(path: str = ":memory:") -> sqlite3.Connection:
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn