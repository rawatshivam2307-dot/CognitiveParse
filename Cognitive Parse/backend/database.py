from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sqlite3
import tempfile
from typing import Dict, List

BASE_DIR = Path(__file__).resolve().parents[1]
DB_DIR = BASE_DIR / "data"


def _resolve_db_path() -> Path:
    env_value = __import__("os").environ.get("COGNITIVEPARSE_DB_PATH", "").strip()
    if env_value:
        env_path = Path(env_value).expanduser()
        env_path.parent.mkdir(parents=True, exist_ok=True)
        return env_path

    candidate = DB_DIR / "errors.db"
    try:
        DB_DIR.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(candidate) as probe:
            probe.execute("CREATE TABLE IF NOT EXISTS _probe (x INTEGER)")
            probe.commit()
        return candidate
    except sqlite3.Error:
        fallback_dir = Path(tempfile.gettempdir()) / "cognitiveparse"
        fallback_dir.mkdir(parents=True, exist_ok=True)
        return fallback_dir / "errors.db"


DB_PATH = _resolve_db_path()
FALLBACK_DB_PATH = Path(tempfile.gettempdir()) / "cognitiveparse" / "errors.db"


@dataclass
class ErrorRecord:
    message: str
    category: str
    suggestion: str
    explanation: str
    line_no: int
    token: str


def _connect() -> sqlite3.Connection:
    global DB_PATH
    try:
        DB_DIR.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error:
        FALLBACK_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        DB_PATH = FALLBACK_DB_PATH
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn


def _switch_to_fallback() -> None:
    global DB_PATH
    FALLBACK_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    DB_PATH = FALLBACK_DB_PATH


def _with_retry(action):
    try:
        with _connect() as conn:
            return action(conn)
    except sqlite3.Error:
        _switch_to_fallback()
        with _connect() as conn:
            return action(conn)


def init_db() -> None:
    def _action(conn):
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS errors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message TEXT NOT NULL,
                category TEXT NOT NULL,
                suggestion TEXT NOT NULL,
                explanation TEXT NOT NULL,
                line_no INTEGER NOT NULL DEFAULT 0,
                token TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
    _with_retry(_action)


def log_error(record: ErrorRecord) -> None:
    def _action(conn):
        conn.execute(
            """
            INSERT INTO errors (message, category, suggestion, explanation, line_no, token)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                record.message,
                record.category,
                record.suggestion,
                record.explanation,
                record.line_no,
                record.token,
            ),
        )
        conn.commit()
    _with_retry(_action)


def fetch_recent_errors(limit: int = 20) -> List[Dict[str, str]]:
    def _action(conn):
        rows = conn.execute(
            """
            SELECT id, message, category, suggestion, explanation, line_no, token, created_at
            FROM errors
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]
    return _with_retry(_action)


def fetch_category_counts() -> List[Dict[str, int]]:
    def _action(conn):
        rows = conn.execute(
            """
            SELECT category, COUNT(*) AS count
            FROM errors
            GROUP BY category
            ORDER BY count DESC, category ASC
            """
        ).fetchall()
        return [dict(row) for row in rows]
    return _with_retry(_action)


def fetch_daily_counts() -> List[Dict[str, int]]:
    def _action(conn):
        rows = conn.execute(
            """
            SELECT substr(created_at, 1, 10) AS day, COUNT(*) AS count
            FROM errors
            GROUP BY day
            ORDER BY day ASC
            """
        ).fetchall()
        return [dict(row) for row in rows]
    return _with_retry(_action)


def fetch_top_messages(limit: int = 5) -> List[Dict[str, int]]:
    def _action(conn):
        rows = conn.execute(
            """
            SELECT message, COUNT(*) AS count
            FROM errors
            GROUP BY message
            ORDER BY count DESC, message ASC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]
    return _with_retry(_action)


def fetch_error_total() -> int:
    def _action(conn):
        row = conn.execute("SELECT COUNT(*) AS total FROM errors").fetchone()
        return int(row["total"] if row else 0)
    return _with_retry(_action)


def clear_errors() -> None:
    def _action(conn):
        conn.execute("DELETE FROM errors")
        conn.commit()
    _with_retry(_action)
