"""SQLite helpers for storing uploaded document metadata."""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Optional

CATEGORY_COLUMNS = ("code_files", "doc_files", "test_files", "config_files", "other_files")
CATEGORY_ALIASES = {
    "code": "code_files",
    "docs": "doc_files",
    "tests": "test_files",
    "configs": "config_files",
    "other": "other_files",
}


def _default_db_path() -> Path:
    return Path(__file__).resolve().parent.parent / "documents.db"


def _resolve_db_path() -> Path:
    env_path = os.getenv("DOCUMENTS_DB_PATH")
    if env_path:
        return Path(env_path).expanduser().resolve()
    return _default_db_path()


_DB_PATH = _resolve_db_path()


def get_db_path() -> Path:
    return _DB_PATH


def set_db_path(path: Path | str) -> Path:
    global _DB_PATH
    previous = _DB_PATH
    _DB_PATH = Path(path).expanduser().resolve()
    return previous


def _ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


@contextmanager
def get_connection() -> sqlite3.Connection:
    db_path = get_db_path()
    _ensure_parent_dir(db_path)
    conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS Documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT NOT NULL,
                extracted_text TEXT,
                code_files INTEGER NOT NULL DEFAULT 0,
                doc_files INTEGER NOT NULL DEFAULT 0,
                test_files INTEGER NOT NULL DEFAULT 0,
                config_files INTEGER NOT NULL DEFAULT 0,
                other_files INTEGER NOT NULL DEFAULT 0,
                uploaded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        conn.commit()


def reset_db() -> None:
    db_path = get_db_path()
    if db_path.exists():
        db_path.unlink()
    init_db()


def initialize() -> None:
    init_db()


def save_document(
    file_name: str,
    extracted_text: str,
    *,
    category_counts: Optional[Dict[str, int]] = None,
    uploaded_at: Optional[str] = None,
) -> int:
    """Persist an uploaded document record with optional category counts."""

    counts = {column: 0 for column in CATEGORY_COLUMNS}
    if category_counts:
        for key, value in category_counts.items():
            if key in CATEGORY_COLUMNS:
                counts[key] = int(value)
            elif key in CATEGORY_ALIASES:
                counts[CATEGORY_ALIASES[key]] = int(value)

    with get_connection() as conn:
        if uploaded_at:
            cursor = conn.execute(
                """
                INSERT INTO Documents (
                    file_name,
                    extracted_text,
                    code_files,
                    doc_files,
                    test_files,
                    config_files,
                    other_files,
                    uploaded_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    file_name,
                    extracted_text,
                    counts["code_files"],
                    counts["doc_files"],
                    counts["test_files"],
                    counts["config_files"],
                    counts["other_files"],
                    uploaded_at,
                ),
            )
        else:
            cursor = conn.execute(
                """
                INSERT INTO Documents (
                    file_name,
                    extracted_text,
                    code_files,
                    doc_files,
                    test_files,
                    config_files,
                    other_files,
                    uploaded_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (
                    file_name,
                    extracted_text,
                    counts["code_files"],
                    counts["doc_files"],
                    counts["test_files"],
                    counts["config_files"],
                    counts["other_files"],
                ),
            )
        conn.commit()
        return cursor.lastrowid
