"""SQLite database access: connection helper, schema and user lookups."""
import re
import sqlite3
from contextlib import contextmanager

from config import ADMIN_EMAIL, DB_PATH


@contextmanager
def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def name_from_email(email: str) -> str:
    local = email.split("@")[0]
    return re.sub(r"[._\-]+", " ", local).strip().title()


def init_db() -> None:
    with db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                email      TEXT NOT NULL UNIQUE COLLATE NOCASE,
                name       TEXT NOT NULL DEFAULT '',
                phone      TEXT NOT NULL DEFAULT '',
                city       TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS sessions (
                token      TEXT PRIMARY KEY,
                email      TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        # The single admin, so someone can log in on a brand-new database.
        conn.execute(
            "INSERT OR IGNORE INTO users (email, name) VALUES (?, ?)",
            (ADMIN_EMAIL, name_from_email(ADMIN_EMAIL)),
        )


def row_to_dict(row: sqlite3.Row) -> dict:
    return {k: row[k] for k in ("id", "email", "name", "phone", "city")}


def find_users(conn: sqlite3.Connection, identifier: str) -> list[sqlite3.Row]:
    """Find users by email or by (partial) name. Tries the strictest match first."""
    ident = identifier.strip().strip("\"'").lower()
    ident = re.sub(r"['\u2019]s$", "", ident)  # samantha's -> samantha
    candidates = [ident]
    if ident.endswith("s") and "@" not in ident:
        candidates.append(ident[:-1])  # samanthas -> samantha

    for cand in candidates:
        rows = conn.execute("SELECT * FROM users WHERE lower(email) = ?", (cand,)).fetchall()
        if rows:
            return rows
        rows = conn.execute("SELECT * FROM users WHERE lower(name) = ?", (cand,)).fetchall()
        if rows:
            return rows
        like = f"%{cand}%"
        rows = conn.execute(
            "SELECT * FROM users WHERE lower(name) LIKE ? OR lower(email) LIKE ?", (like, like)
        ).fetchall()
        if rows:
            return rows
    return []