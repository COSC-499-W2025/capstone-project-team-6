"""SQLite helpers for user authentication."""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Optional, Union
from fastapi import HTTPException, status
import bcrypt

DEFAULT_USERS: Dict[str, str] = {
    "testuser": "password123",
    "mithish": "abc123",
}


class UserAlreadyExistsError(Exception):
    """Raised when attempting to create a user that already exists."""


def _default_db_path() -> Path:
    return Path(__file__).resolve().parent.parent / "myapp.db"


def _resolve_db_path() -> Path:
    env_path = os.getenv("MYAPP_DB_PATH")
    if env_path:
        return Path(env_path).expanduser().resolve()
    return _default_db_path()


_DB_PATH = _resolve_db_path()


def get_db_path() -> Path:
    return _DB_PATH


def set_db_path(path: Union[Path, str]) -> Path:
    global _DB_PATH
    previous = _DB_PATH
    _DB_PATH = Path(path).expanduser().resolve()
    return previous


def _ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


@contextmanager
def get_connection() -> sqlite3.Connection:
    """Context manager that yields a SQLite connection with row access by name."""

    db_path = get_db_path()
    _ensure_parent_dir(db_path)
    conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    """Create required tables if they do not already exist."""

    with get_connection() as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_consent (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            llm_allowed BOOLEAN DEFAULT NULL,
            consent_date TEXT,
            FOREIGN KEY (username) REFERENCES users(username)
        );

            """
        )
        # change for consent to be tri state
        cols = conn.execute("PRAGMA table_info(user_consent);").fetchall()
        col_names = {c[1] for c in cols}

        if "has_consented" in col_names and "llm_allowed" not in col_names:
            conn.execute("ALTER TABLE user_consent RENAME TO user_consent_old;")

            conn.execute(
                """
                CREATE TABLE user_consent (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    llm_allowed BOOLEAN DEFAULT NULL,
                    consent_date TEXT,
                    FOREIGN KEY (username) REFERENCES users(username)
                );
                """
            )

            conn.execute(
                """
                INSERT INTO user_consent (id, username, llm_allowed, consent_date)
                SELECT id,
                       username,
                       CASE WHEN has_consented = 1 THEN 1 ELSE 0 END,
                       consent_date
                FROM user_consent_old;
                """
            )

            conn.execute("DROP TABLE user_consent_old;")

        conn.commit()


def reset_db() -> None:
    """Helper for tests: drop the database file and recreate schema."""

    db_path = get_db_path()
    if db_path.exists():
        db_path.unlink()
    init_db()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        # Happens if stored hash is malformed.
        return False


def create_user(username: str, password: str) -> int:
    if not username:
        raise ValueError("Username is required")
    if not password:
        raise ValueError("Password is required")

    hashed = hash_password(password)

    with get_connection() as conn:
        try:
            cursor = conn.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, hashed),
            )
            conn.commit()
        except sqlite3.IntegrityError as exc:
            raise UserAlreadyExistsError("Username already exists") from exc

        return cursor.lastrowid


def get_user(username: str) -> Optional[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            "SELECT id, username, password_hash, created_at FROM users WHERE username = ?",
            (username,),
        ).fetchone()


def authenticate_user(username: str, password: str) -> bool:
    record = get_user(username)
    if record is None:
        return False
    if verify_password(password, record["password_hash"]):
        from .session import save_session

        save_session(username)
        return True
    return False

'''
def check_user_consent(username: str) -> bool:
    """Check if user has given consent.

    Args:
        username: The username to check consent for

    Returns:
        bool: True if user has consented, False otherwise
    """
    with get_connection() as conn:
        result = conn.execute("SELECT has_consented FROM user_consent WHERE username = ?", (username,)).fetchone()
        return bool(result["has_consented"]) if result else False


def save_user_consent(username: str, has_consented: bool) -> None:
    """Save user's consent status.

    Args:
        username: The username to save consent for
        has_consented: Whether user has consented or not
    """
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO user_consent (username, has_consented, consent_date)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(username) DO UPDATE SET
                has_consented = excluded.has_consented,
                consent_date = CURRENT_TIMESTAMP
            """,
            (username, has_consented),
        )
        conn.commit()
'''

# Backwards-compat wrappers
def check_user_consent(username: str) -> bool:
    """
    Backwards compatible wrapper.
    """
    return get_llm_allowed(username) is True


def save_user_consent(username: str, has_consented: bool) -> None:
    """
    Backwards compatible wrapper.
    """
    save_llm_allowed(username, bool(has_consented))



def seed_default_users(default_users: Optional[Dict[str, str]] = None) -> None:
    users = default_users or DEFAULT_USERS
    for username, password in users.items():
        try:
            create_user(username, password)
        except UserAlreadyExistsError:
            continue


def initialize() -> None:
    init_db()
    seed_default_users()

def get_llm_allowed(username: str) -> Optional[bool]:
    """Return the user's LLM permission as a tri-state.

    Returns:
        True  -> user explicitly allowed LLM features
        False -> user explicitly disallowed LLM features
        None  -> user has not answered yet (no row or NULL)
    """
    with get_connection() as conn:
        row = conn.execute("SELECT llm_allowed FROM user_consent WHERE username = ?", (username,)).fetchone()
        if row is None:
            return None
        value = row["llm_allowed"]
        if value is None:
            return None
        return bool(value)


def save_llm_allowed(username: str, llm_allowed: bool) -> None:
    """Persist the user's LLM permission."""
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO user_consent (username, llm_allowed, consent_date)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(username) DO UPDATE SET
                llm_allowed = excluded.llm_allowed,
                consent_date = CURRENT_TIMESTAMP
            """,
            (username, llm_allowed),
        )
        conn.commit()

def require_llm_allowed(username: str) -> None:
    """
    Enforce LLM permission for endpoints that invoke LLM functionality.
    - None or False => block
    - True => allow
    """
    allowed = get_llm_allowed(username)
    if allowed is not True:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="LLM features are disabled for this account.",
        )

if __name__ == "__main__":
    initialize()
    print(f"SQLite setup complete at {get_db_path()}")
