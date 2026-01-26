"""High-coverage tests for user-scoped analyses and migrations."""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

# Add src directory (and project root) to path for imports
SRC_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_ROOT = SRC_DIR.parent
for p in (SRC_DIR, PROJECT_ROOT):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from src.backend import analysis_database as adb  # noqa: E402
from src.backend import database as udb  # noqa: E402


@pytest.fixture
def temp_db(tmp_path):
    """Fresh DB with both user and analysis schemas, seeded users for FK checks."""
    db_path = tmp_path / "analysis.db"
    prev_analysis = adb.set_db_path(db_path)
    prev_user = udb.set_db_path(db_path)

    if db_path.exists():
        db_path.unlink()

    # Initialize users first (FK target), then analyses
    udb.init_db()
    udb.create_user("alice", "password123")
    udb.create_user("bob", "password123")
    adb.init_db()

    yield db_path

    adb.set_db_path(prev_analysis)
    udb.set_db_path(prev_user)


def test_username_column_exists_after_init(temp_db):
    """Ensure the username column is present even on fresh init."""
    with adb.get_connection() as conn:
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(analyses)")}
    assert "username" in columns


def test_record_and_list_are_user_scoped(temp_db):
    """Users only see their own analyses."""
    adb.record_analysis(
        "non_llm", _payload("uuid-a"), username="alice", analysis_uuid="uuid-a"
    )
    adb.record_analysis(
        "non_llm", _payload("uuid-b"), username="bob", analysis_uuid="uuid-b"
    )

    alice_list = {a["analysis_uuid"] for a in adb.get_all_analyses_for_user("alice")}
    bob_list = {b["analysis_uuid"] for b in adb.get_all_analyses_for_user("bob")}

    assert alice_list == {"uuid-a"}
    assert bob_list == {"uuid-b"}


def test_get_analysis_by_uuid_requires_owner(temp_db):
    """Fetching by UUID enforces ownership when username is provided."""
    adb.record_analysis(
        "non_llm", _payload("uuid-a"), username="alice", analysis_uuid="uuid-a"
    )
    assert adb.get_analysis_by_uuid("uuid-a", "alice") is not None
    assert adb.get_analysis_by_uuid("uuid-a", "bob") is None


def test_delete_analysis_requires_owner(temp_db):
    """Deletion is blocked for non-owners and succeeds for owners."""
    adb.record_analysis(
        "non_llm", _payload("uuid-a"), username="alice", analysis_uuid="uuid-a"
    )
    assert adb.delete_analysis("uuid-a", "bob") is False
    assert adb.delete_analysis("uuid-a", "alice") is True
    assert adb.get_analysis_by_uuid("uuid-a", "alice") is None


def test_null_username_allowed_for_backward_compat(temp_db):
    """Rows with NULL username still insert (no FK) and can be fetched without user filter."""
    analysis_id = adb.record_analysis(
        "non_llm",
        _payload("uuid-null"),
        username=None,
        analysis_uuid="uuid-null",
    )
    row = adb.get_analysis(analysis_id)
    assert row["username"] is None
    # Unscoped fetch still works
    assert adb.get_analysis_by_uuid("uuid-null") is not None


def test_init_db_backfills_username_column(temp_db):
    """Simulate pre-username schema and ensure init_db migrates without data loss."""
    legacy_db = temp_db

    # Replace schema with legacy (no username column)
    with sqlite3.connect(legacy_db) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("DROP TABLE IF EXISTS analyses;")
        conn.execute(
            """
            CREATE TABLE analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_uuid TEXT NOT NULL UNIQUE,
                analysis_type TEXT NOT NULL,
                zip_file TEXT NOT NULL,
                analysis_timestamp TEXT NOT NULL,
                total_projects INTEGER NOT NULL,
                raw_json TEXT NOT NULL,
                summary_total_files INTEGER,
                summary_total_size_bytes INTEGER,
                summary_total_size_mb REAL,
                summary_languages TEXT,
                summary_frameworks TEXT,
                llm_summary TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        conn.execute(
            """
            INSERT INTO analyses (
                analysis_uuid, analysis_type, zip_file, analysis_timestamp,
                total_projects, raw_json, summary_total_files, summary_total_size_bytes,
                summary_total_size_mb, summary_languages, summary_frameworks, llm_summary
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "legacy-uuid",
                "non_llm",
                "legacy.zip",
                "2024-01-01T00:00:00",
                0,
                "{}",
                None,
                None,
                None,
                None,
                None,
                None,
            ),
        )
        conn.commit()

    # Running init_db should add username column and preserve data
    adb.init_db()

    with adb.get_connection() as conn:
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(analyses)")}
        legacy_row = conn.execute(
            "SELECT analysis_uuid, username FROM analyses WHERE analysis_uuid = ?",
            ("legacy-uuid",),
        ).fetchone()

    assert "username" in columns
    assert legacy_row["analysis_uuid"] == "legacy-uuid"
    # Existing rows remain intact; username is NULL until backfilled or rewritten
    assert legacy_row["username"] is None


def _payload(analysis_uuid: str):
    """Minimal payload helper for brevity."""
    return {
        "analysis_metadata": {
            "zip_file": f"{analysis_uuid}.zip",
            "analysis_timestamp": "2025-11-03T12:34:56",
            "total_projects": 1,
        },
        "projects": [],
        "summary": {},
    }
