"""
Tests for LLM summary storage and retrieval pipeline.

Covers:
- update_llm_summary / get_llm_summary_for_analysis in analysis_database
- record_analysis correctly persists project rows (regression: total_projects=0 bug)
- sqlite3.Row 'in' operator bug (analysis_uuid always None)
- task_manager correctly saves LLM summary using analysis_uuid from DB row
"""

from __future__ import annotations

import asyncio
import sqlite3
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

SRC_DIR = Path(__file__).resolve().parents[2]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from backend import analysis_database as adb
from backend import database as udb

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

SAMPLE_PAYLOAD = {
    "analysis_metadata": {
        "zip_file": "project.zip",
        "analysis_timestamp": "2025-01-01T00:00:00",
        "total_projects": 1,
    },
    "projects": [
        {
            "project_name": "demo_project",
            "project_path": "demo",
            "primary_language": "python",
            "languages": {"python": 10},
            "total_files": 10,
            "total_size": 1024,
            "code_files": 8,
            "test_files": 2,
            "doc_files": 1,
            "config_files": 1,
            "frameworks": ["FastAPI"],
            "dependencies": {},
            "has_tests": True,
            "has_readme": True,
            "has_ci_cd": False,
            "has_docker": False,
            "is_git_repo": False,
        }
    ],
    "summary": {
        "total_files": 10,
        "total_size_bytes": 1024,
        "total_size_mb": 0.001,
        "languages_used": ["python"],
        "frameworks_used": ["FastAPI"],
    },
}

SAMPLE_LLM_SUMMARY = (
    "## General Validation\nThe codebase is well-structured with clear separation of concerns.\n\n"
    "### Architecture\nUses a layered architecture with FastAPI for REST endpoints.\n\n"
    "### Security\nNo obvious SQL injection vulnerabilities detected.\n"
)


@pytest.fixture
def db(tmp_path):
    """Isolated SQLite DB for each test."""
    db_path = tmp_path / "test_llm.db"
    prev_adb = adb.set_db_path(db_path)
    prev_udb = udb.set_db_path(db_path)
    udb.init_db()
    udb.create_user("alice", "password123")
    adb.init_db()
    yield
    adb.set_db_path(prev_adb)
    udb.set_db_path(prev_udb)


# ---------------------------------------------------------------------------
# 1. update_llm_summary and get_llm_summary_for_analysis
# ---------------------------------------------------------------------------


class TestUpdateAndGetLlmSummary:
    def test_update_saves_summary_and_get_retrieves_it(self, db):
        analysis_id = adb.record_analysis("non_llm", SAMPLE_PAYLOAD, username="alice", analysis_uuid="uuid-aaa")
        assert analysis_id is not None

        saved = adb.update_llm_summary("uuid-aaa", SAMPLE_LLM_SUMMARY, "alice")
        assert saved is True

        retrieved = adb.get_llm_summary_for_analysis("uuid-aaa", "alice")
        assert retrieved == SAMPLE_LLM_SUMMARY

    def test_update_returns_false_for_nonexistent_uuid(self, db):
        result = adb.update_llm_summary("does-not-exist", "some text", "alice")
        assert result is False

    def test_get_returns_none_for_nonexistent_uuid(self, db):
        result = adb.get_llm_summary_for_analysis("does-not-exist", "alice")
        assert result is None

    def test_get_returns_none_when_summary_not_set(self, db):
        adb.record_analysis("non_llm", SAMPLE_PAYLOAD, username="alice", analysis_uuid="uuid-bbb")
        result = adb.get_llm_summary_for_analysis("uuid-bbb", "alice")
        assert result is None

    def test_get_returns_none_for_wrong_user(self, db):
        udb.create_user("bob", "password123")
        adb.record_analysis("non_llm", SAMPLE_PAYLOAD, username="alice", analysis_uuid="uuid-ccc")
        adb.update_llm_summary("uuid-ccc", SAMPLE_LLM_SUMMARY, "alice")

        result = adb.get_llm_summary_for_analysis("uuid-ccc", "bob")
        assert result is None

    def test_update_overwrites_existing_summary(self, db):
        adb.record_analysis("non_llm", SAMPLE_PAYLOAD, username="alice", analysis_uuid="uuid-ddd")
        adb.update_llm_summary("uuid-ddd", "first summary", "alice")
        adb.update_llm_summary("uuid-ddd", "updated summary", "alice")

        result = adb.get_llm_summary_for_analysis("uuid-ddd", "alice")
        assert result == "updated summary"

    def test_summary_persists_large_text(self, db):
        large_summary = "# Analysis\n" + ("X" * 50_000)
        adb.record_analysis("non_llm", SAMPLE_PAYLOAD, username="alice", analysis_uuid="uuid-eee")
        adb.update_llm_summary("uuid-eee", large_summary, "alice")

        result = adb.get_llm_summary_for_analysis("uuid-eee", "alice")
        assert result == large_summary
        assert len(result) == len(large_summary)


# ---------------------------------------------------------------------------
# 2. record_analysis project persistence (regression: total_projects=0 bug)
# ---------------------------------------------------------------------------


class TestRecordAnalysisProjectPersistence:
    def test_projects_created_in_db_after_record_analysis(self, db):
        analysis_id = adb.record_analysis("non_llm", SAMPLE_PAYLOAD, username="alice")
        projects = adb.get_projects_for_analysis(analysis_id)
        assert len(projects) == 1
        assert projects[0]["project_name"] == "demo_project"

    def test_total_projects_column_matches_actual_count(self, db):
        analysis_id = adb.record_analysis("non_llm", SAMPLE_PAYLOAD, username="alice")
        row = adb.get_analysis(analysis_id)
        assert row["total_projects"] == 1

    def test_analysis_uuid_stored_correctly(self, db):
        analysis_id = adb.record_analysis("non_llm", SAMPLE_PAYLOAD, username="alice", analysis_uuid="my-fixed-uuid")
        row = adb.get_analysis(analysis_id)
        assert row["analysis_uuid"] == "my-fixed-uuid"

    def test_analysis_uuid_auto_generated_when_not_provided(self, db):
        analysis_id = adb.record_analysis("non_llm", SAMPLE_PAYLOAD, username="alice")
        row = adb.get_analysis(analysis_id)
        assert row["analysis_uuid"] is not None
        assert len(row["analysis_uuid"]) == 36  # standard UUID4 length

    def test_zip_file_hash_stored(self, db):
        analysis_id = adb.record_analysis("non_llm", SAMPLE_PAYLOAD, username="alice", zip_file_hash="abc123hash")
        row = adb.get_analysis(analysis_id)
        assert row["zip_file_hash"] == "abc123hash"


# ---------------------------------------------------------------------------
# 3. sqlite3.Row 'in' operator bug — analysis_uuid always None
# ---------------------------------------------------------------------------


class TestSqlite3RowUuidExtraction:
    """
    Regression tests for the bug where `"analysis_uuid" in row` returned False
    for sqlite3.Row objects even when the column existed and had a value.
    This caused analysis_uuid to be set to None in task_manager, preventing
    the LLM summary from ever being saved to the database.
    """

    def test_in_operator_returns_false_for_sqlite3_row(self, db):
        """Demonstrates the original broken pattern."""
        analysis_id = adb.record_analysis("non_llm", SAMPLE_PAYLOAD, username="alice", analysis_uuid="bug-test-uuid")
        row = adb.get_analysis(analysis_id)

        # sqlite3.Row does NOT support 'in' for column name checks
        assert ("analysis_uuid" in row) is False  # this was the bug
        # but direct access still works
        assert row["analysis_uuid"] == "bug-test-uuid"

    def test_correct_uuid_extraction_without_in_check(self, db):
        """Demonstrates the fixed pattern used in task_manager."""
        analysis_id = adb.record_analysis("non_llm", SAMPLE_PAYLOAD, username="alice", analysis_uuid="fixed-uuid")
        row = adb.get_analysis(analysis_id)

        # Correct pattern: just check row is not None
        analysis_uuid = row["analysis_uuid"] if row else None
        assert analysis_uuid == "fixed-uuid"

    def test_none_row_gives_none_uuid(self, db):
        """When get_analysis returns None (bad ID), uuid should be None."""
        row = adb.get_analysis(99999)
        analysis_uuid = row["analysis_uuid"] if row else None
        assert analysis_uuid is None

    def test_llm_summary_saved_when_uuid_extracted_correctly(self, db):
        """End-to-end: correct uuid extraction allows LLM summary to be saved."""
        analysis_id = adb.record_analysis("non_llm", SAMPLE_PAYLOAD, username="alice", analysis_uuid="e2e-uuid")
        row = adb.get_analysis(analysis_id)

        # The fixed extraction
        analysis_uuid = row["analysis_uuid"] if row else None
        assert analysis_uuid == "e2e-uuid"

        # Save LLM summary using the correctly extracted UUID
        adb.update_llm_summary(analysis_uuid, SAMPLE_LLM_SUMMARY, "alice")

        # Verify it was actually persisted
        result = adb.get_llm_summary_for_analysis("e2e-uuid", "alice")
        assert result == SAMPLE_LLM_SUMMARY


# ---------------------------------------------------------------------------
# 4. task_manager LLM save flow
# ---------------------------------------------------------------------------


@pytest.fixture
def minimal_zip(tmp_path):
    zip_path = tmp_path / "test_project.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("main.py", "print('hello')")
        zf.writestr("README.md", "# Test Project")
    return zip_path


class TestTaskManagerLlmSave:
    """Tests that _process_new_portfolio saves the LLM summary to the correct analysis row."""

    @patch("backend.database.check_user_consent", return_value=True)
    @patch("backend.analysis.llm_pipeline.run_gemini_analysis")
    @patch("backend.analysis_database.update_llm_summary")
    @patch("backend.analysis_database.get_analysis")
    @patch("backend.analysis_database.record_analysis", return_value=42)
    @patch("backend.cli.analyze_folder")
    def test_llm_summary_saved_when_uuid_available(
        self,
        mock_analyze,
        mock_record,
        mock_get_analysis,
        mock_update_llm,
        mock_run_gemini,
        mock_consent,
        minimal_zip,
    ):
        """When get_analysis returns a row with analysis_uuid, update_llm_summary is called."""
        from backend.task_manager import (TaskInfo, TaskManager, TaskStatus,
                                          TaskType)

        mock_analyze.return_value = {
            "projects": [{"project_name": "Test", "project_path": ""}],
            "analysis_metadata": {"zip_file": str(minimal_zip), "analysis_timestamp": "2025-01-01T00:00:00"},
            "summary": {},
        }
        # Simulate a proper sqlite3.Row-like object that returns uuid correctly
        fake_row = MagicMock()
        fake_row.__getitem__ = lambda self, k: "real-uuid-456" if k == "analysis_uuid" else None
        fake_row.__bool__ = lambda self: True
        mock_get_analysis.return_value = fake_row

        mock_run_gemini.return_value = {"llm_summary": SAMPLE_LLM_SUMMARY, "llm_error": None}

        task = TaskInfo(
            task_id="t1",
            task_type=TaskType.NEW_PORTFOLIO,
            status=TaskStatus.RUNNING,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            username="alice",
            filename="test_project.zip",
            file_path=str(minimal_zip),
            file_hash="somehash",
            analysis_type="non_llm",
        )

        manager = TaskManager()
        result = asyncio.run(manager._process_new_portfolio(task))

        assert result["llm_ran"] is True
        assert result["llm_error"] is None
        mock_update_llm.assert_called_once_with("real-uuid-456", SAMPLE_LLM_SUMMARY, "alice")

    @patch("backend.database.check_user_consent", return_value=True)
    @patch("backend.analysis.llm_pipeline.run_gemini_analysis")
    @patch("backend.analysis_database.update_llm_summary")
    @patch("backend.analysis_database.get_analysis", return_value=None)
    @patch("backend.analysis_database.record_analysis", return_value=99)
    @patch("backend.cli.analyze_folder")
    def test_llm_summary_not_saved_when_uuid_is_none(
        self,
        mock_analyze,
        mock_record,
        mock_get_analysis,
        mock_update_llm,
        mock_run_gemini,
        mock_consent,
        minimal_zip,
    ):
        """When get_analysis returns None (uuid=None), update_llm_summary is NOT called."""
        from backend.task_manager import (TaskInfo, TaskManager, TaskStatus,
                                          TaskType)

        mock_analyze.return_value = {
            "projects": [{"project_name": "Test", "project_path": ""}],
            "analysis_metadata": {"zip_file": str(minimal_zip), "analysis_timestamp": "2025-01-01T00:00:00"},
            "summary": {},
        }
        mock_run_gemini.return_value = {"llm_summary": SAMPLE_LLM_SUMMARY, "llm_error": None}

        task = TaskInfo(
            task_id="t2",
            task_type=TaskType.NEW_PORTFOLIO,
            status=TaskStatus.RUNNING,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            username="alice",
            filename="test_project.zip",
            file_path=str(minimal_zip),
            file_hash="somehash2",
            analysis_type="non_llm",
        )

        manager = TaskManager()
        asyncio.run(manager._process_new_portfolio(task))

        # Should NOT call update_llm_summary because uuid is None
        mock_update_llm.assert_not_called()

    @patch("backend.database.check_user_consent", return_value=False)
    @patch("backend.analysis.llm_pipeline.run_gemini_analysis")
    @patch("backend.analysis_database.get_analysis")
    @patch("backend.analysis_database.record_analysis", return_value=10)
    @patch("backend.cli.analyze_folder")
    def test_llm_not_run_when_no_consent(
        self,
        mock_analyze,
        mock_record,
        mock_get_analysis,
        mock_run_gemini,
        mock_consent,
        minimal_zip,
    ):
        """LLM pipeline is skipped entirely when user has not consented."""
        from backend.task_manager import (TaskInfo, TaskManager, TaskStatus,
                                          TaskType)

        mock_analyze.return_value = {
            "projects": [{"project_name": "Test", "project_path": ""}],
            "analysis_metadata": {"zip_file": str(minimal_zip), "analysis_timestamp": "2025-01-01T00:00:00"},
            "summary": {},
        }
        fake_row = MagicMock()
        fake_row.__getitem__ = lambda self, k: "some-uuid"
        fake_row.__bool__ = lambda self: True
        mock_get_analysis.return_value = fake_row

        task = TaskInfo(
            task_id="t3",
            task_type=TaskType.NEW_PORTFOLIO,
            status=TaskStatus.RUNNING,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            username="alice",
            filename="test_project.zip",
            file_path=str(minimal_zip),
            file_hash="somehash3",
            analysis_type="non_llm",
        )

        manager = TaskManager()
        result = asyncio.run(manager._process_new_portfolio(task))

        assert result["llm_ran"] is False
        mock_run_gemini.assert_not_called()

    @patch("backend.database.check_user_consent", return_value=True)
    @patch("backend.analysis.llm_pipeline.run_gemini_analysis")
    @patch("backend.analysis_database.update_llm_summary")
    @patch("backend.analysis_database.get_analysis")
    @patch("backend.analysis_database.record_analysis", return_value=5)
    @patch("backend.cli.analyze_folder")
    def test_llm_error_does_not_crash_task(
        self,
        mock_analyze,
        mock_record,
        mock_get_analysis,
        mock_update_llm,
        mock_run_gemini,
        mock_consent,
        minimal_zip,
    ):
        """If LLM pipeline raises an exception, the task still completes (llm_ran=False)."""
        from backend.task_manager import (TaskInfo, TaskManager, TaskStatus,
                                          TaskType)

        mock_analyze.return_value = {
            "projects": [{"project_name": "Test", "project_path": ""}],
            "analysis_metadata": {"zip_file": str(minimal_zip), "analysis_timestamp": "2025-01-01T00:00:00"},
            "summary": {},
        }
        fake_row = MagicMock()
        fake_row.__getitem__ = lambda self, k: "some-uuid"
        fake_row.__bool__ = lambda self: True
        mock_get_analysis.return_value = fake_row

        mock_run_gemini.side_effect = RuntimeError("Gemini API quota exceeded")

        task = TaskInfo(
            task_id="t4",
            task_type=TaskType.NEW_PORTFOLIO,
            status=TaskStatus.RUNNING,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            username="alice",
            filename="test_project.zip",
            file_path=str(minimal_zip),
            file_hash="somehash4",
            analysis_type="non_llm",
        )

        manager = TaskManager()
        result = asyncio.run(manager._process_new_portfolio(task))

        assert result["llm_ran"] is False
        assert "Gemini API quota exceeded" in result["llm_error"]
        mock_update_llm.assert_not_called()
