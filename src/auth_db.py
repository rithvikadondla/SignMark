"""Tiny SQLite user store (standard library only). Passwords are stored as hashes, never as text."""
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = """CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL, last_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE, date_of_birth TEXT NOT NULL,
    password_hash TEXT NOT NULL, created_at TEXT NOT NULL)"""


def _connect(path):
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with closing(_connect(path)) as conn, conn:
        conn.execute(SCHEMA)


def create_user(path, first_name, last_name, email, dob, password_hash):
    """Returns the new user id, or None if the email is already registered."""
    try:
        with closing(_connect(path)) as conn, conn:
            cur = conn.execute(
                "INSERT INTO users (first_name, last_name, email, date_of_birth, password_hash, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (first_name, last_name, email, dob, password_hash, datetime.now(timezone.utc).isoformat()))
            return cur.lastrowid
    except sqlite3.IntegrityError:
        return None


def user_by_email(path, email):
    with closing(_connect(path)) as conn:
        return conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()


def user_by_id(path, user_id):
    with closing(_connect(path)) as conn:
        return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
