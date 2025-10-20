"""Модуль работы с SQLite.
Простой синхронный доступ через sqlite3 — достаточно для MVP.
"""
import sqlite3
from contextlib import contextmanager
from pathlib import Path
import config

DB_PATH = Path(config.DB_PATH)
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


# Инициализация схемы при импорте
def init_db():
    sql_file = Path(__file__).parent / "migrations" / "init.sql"
    with sqlite3.connect(DB_PATH) as conn:
        with open(sql_file, "r", encoding="utf-8") as f:
            conn.executescript(f.read())
        conn.commit()


init_db()


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


# User helpers
def ensure_user(user_id: int):
    with get_conn() as conn:
        conn.execute("INSERT OR IGNORE INTO users(user_id) VALUES(?)", (user_id,))
        conn.commit()


# Busy helpers
def add_busy(user_id: int, label: str, start_ts: int, end_ts: int):
    ensure_user(user_id)
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO busy(user_id, label, start_ts, end_ts) VALUES(?,?,?,?)",
            (user_id, label, start_ts, end_ts),
        )
        conn.commit()


def get_busy(user_id: int):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM busy WHERE user_id = ? ORDER BY start_ts", (user_id,)
        ).fetchall()
        return [dict(r) for r in rows]


# Tasks helpers
def add_task(user_id: int, label: str, duration_hours: float, preferred_days: str | None = None):
    ensure_user(user_id)
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO tasks(user_id, label, duration_hours, preferred_days) VALUES(?,?,?,?)",
            (user_id, label, duration_hours, preferred_days),
        )
        conn.commit()


def get_tasks(user_id: int):
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM tasks WHERE user_id = ?", (user_id,)).fetchall()
        return [dict(r) for r in rows]


# Settings helpers
def set_user_hours(user_id: int, start_hour: int, end_hour: int):
    ensure_user(user_id)
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO settings(user_id, start_hour, end_hour) VALUES(?,?,?) "
            "ON CONFLICT(user_id) DO UPDATE SET start_hour=excluded.start_hour, "
            "end_hour=excluded.end_hour",
            (user_id, start_hour, end_hour),
        )
        conn.commit()


def get_user_hours(user_id: int):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT start_hour, end_hour FROM settings WHERE user_id = ?", (user_id,)
        ).fetchone()
        if row:
            return int(row["start_hour"]), int(row["end_hour"])
        return config.DEFAULT_START_HOUR, config.DEFAULT_END_HOUR
