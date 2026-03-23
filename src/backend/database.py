"""SQLite helpers for user authentication."""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Optional, Union

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
                has_consented BOOLEAN NOT NULL DEFAULT 0,
                consent_date TEXT,
                FOREIGN KEY (username) REFERENCES users(username)
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tokens (
                token TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL
            );
            """
        )
        _migrate_user_consent(conn)
        conn.commit()


def _migrate_user_consent(conn: sqlite3.Connection) -> None:
    """Add has_consented/consent_date columns if missing (backward compatibility)."""
    try:
        cursor = conn.execute("PRAGMA table_info(user_consent)")
    except sqlite3.OperationalError:
        return  # Table doesn't exist yet, CREATE TABLE will create it
    columns = [row[1] for row in cursor.fetchall()]
    if "has_consented" not in columns:
        conn.execute("ALTER TABLE user_consent ADD COLUMN has_consented BOOLEAN NOT NULL DEFAULT 0")
    if "consent_date" not in columns:
        conn.execute("ALTER TABLE user_consent ADD COLUMN consent_date TEXT")


def reset_db() -> None:
    """Helper for tests: drop the database file and recreate schema."""

    db_path = get_db_path()
    if db_path.exists():
        db_path.unlink()
    init_db()



def save_token_to_db(token: str, username: str, created_at: str, expires_at: str) -> None:
    """Upsert a token record into the tokens table."""
    with get_connection() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO tokens (token, username, created_at, expires_at)
            VALUES (?, ?, ?, ?)
            """,
            (token, username, created_at, expires_at),
        )
        conn.commit()


def delete_token_from_db(token: str) -> None:
    """Remove a single token from the tokens table."""
    with get_connection() as conn:
        conn.execute("DELETE FROM tokens WHERE token = ?", (token,))
        conn.commit()


def clear_tokens_from_db() -> None:
    """Remove all tokens from the tokens table."""
    with get_connection() as conn:
        conn.execute("DELETE FROM tokens")
        conn.commit()


def load_active_tokens_from_db() -> dict:
    """Load all non-expired tokens from the DB into a plain dict."""
    from datetime import datetime

    result = {}
    with get_connection() as conn:
        rows = conn.execute("SELECT token, username, created_at, expires_at FROM tokens").fetchall()
    for row in rows:
        try:
            expires_at = datetime.fromisoformat(row["expires_at"])
            created_at = datetime.fromisoformat(row["created_at"])
        except (ValueError, TypeError):
            continue
        if datetime.now() < expires_at:
            result[row["token"]] = {
                "username": row["username"],
                "created_at": created_at,
                "expires_at": expires_at,
            }
    return result


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


def delete_user_account(username: str) -> bool:
    """
    Permanently delete a user and all associated data.

    Uses ONE SQLite connection/transaction only, because both auth data and
    analysis data live in the same myapp.db file. Opening two write connections
    to the same SQLite file can cause 'database is locked'.
    """
    if not username:
        raise ValueError("username is required")

    with get_connection() as conn:
        conn.execute("PRAGMA foreign_keys = ON;")

        try:
            conn.execute("BEGIN;")

            # Delete analysis-side rows first (these reference users.username and
            # some do not use ON DELETE CASCADE)
            conn.execute(
                """
                DELETE FROM analyses
                WHERE username = ?
                """,
                (username,),
            )

            conn.execute(
                """
                DELETE FROM uploads
                WHERE username = ?
                """,
                (username,),
            )

            conn.execute(
                """
                DELETE FROM user_profile
                WHERE username = ?
                """,
                (username,),
            )

            conn.execute(
                """
                DELETE FROM user_resumes
                WHERE username = ?
                """,
                (username,),
            )

            # Delete auth-side dependent rows
            conn.execute(
                """
                DELETE FROM user_consent
                WHERE username = ?
                """,
                (username,),
            )

            # Finally delete the user row
            cur = conn.execute(
                """
                DELETE FROM users
                WHERE username = ?
                """,
                (username,),
            )

            conn.commit()
            return (cur.rowcount or 0) > 0

        except Exception:
            conn.rollback()
            raise


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


def update_user_password(username: str, new_password: str) -> None:
    if not username:
        raise ValueError("Username is required")
    if not new_password:
        raise ValueError("New password is required")

    if get_user(username) is None:
        raise ValueError("User does not exist")

    hashed = hash_password(new_password)

    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET password_hash = ? WHERE username = ?",
            (hashed, username),
        )
        conn.commit()


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


if __name__ == "__main__":
    initialize()
    print(f"SQLite setup complete at {get_db_path()}")
