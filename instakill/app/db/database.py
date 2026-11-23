"""SQLite schema and connection factory for InstaKill."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "instakill.db"
SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS user (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 username TEXT NOT NULL UNIQUE,
 created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
CREATE TABLE IF NOT EXISTS post (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 user_id INTEGER NOT NULL REFERENCES user(id) ON DELETE CASCADE,
 content TEXT NOT NULL,
 created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
CREATE TABLE IF NOT EXISTS follow (
 follower_id INTEGER NOT NULL REFERENCES user(id) ON DELETE CASCADE,
 followed_id INTEGER NOT NULL REFERENCES user(id) ON DELETE CASCADE,
 created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
 PRIMARY KEY (follower_id, followed_id), CHECK(follower_id <> followed_id)
);
CREATE TABLE IF NOT EXISTS like (
 user_id INTEGER NOT NULL REFERENCES user(id) ON DELETE CASCADE,
 post_id INTEGER NOT NULL REFERENCES post(id) ON DELETE CASCADE,
 created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
 PRIMARY KEY (user_id, post_id)
);
CREATE INDEX IF NOT EXISTS idx_post_created ON post(created_at);
CREATE INDEX IF NOT EXISTS idx_post_user ON post(user_id);
CREATE INDEX IF NOT EXISTS idx_like_post ON like(post_id);
"""

def get_connection(db_path: str | Path | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path or DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db(db_path: str | Path | None = None) -> None:
    with get_connection(db_path) as conn:
        conn.executescript(SCHEMA)
