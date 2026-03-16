"""
Unit tests for task manager LLM analysis behavior.

Verifies that the LLM summary is stored by calling update_llm_summary() on the
existing analysis row rather than creating a second record_analysis() entry.
This prevents duplicate project rows in the database.
"""

from __future__ import annotations

import asyncio
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

src_dir = Path(__file__).resolve().parents[2]
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))


SAMPLE_LLM_SUMMARY = "## Architecture\nWell structured.\n## Security\nNo issues found."


@pytest.fixture
def minimal_zip(tmp_path):
    """Create a minimal valid project ZIP."""
    zip_path = tmp_path / "test.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("project/main.py", "print('hi')")
        zf.writestr("project/README.md", "# Test")
    return zip_path


class TestLlmStoredViaUpdateNotRecordAnalysis:
    """
    LLM results must be persisted by calling update_llm_summary() on the existing
    analysis row, NOT by calling record_analysis() a second time.

    Calling record_analysis() a second time was the old approach and caused
    duplicate project rows in the database.
    """

    @patch("backend.database.check_user_consent", return_value=True)
    @patch("backend.analysis.llm_pipeline.run_gemini_analysis")
    @patch("backend.analysis_database.update_llm_summary")
    @patch("backend.analysis_database.get_analysis")
    @patch("backend.analysis_database.record_analysis", return_value=1)
    @patch("backend.cli.analyze_folder")
    def test_llm_summary_stored_via_update_llm_summary(
        self,
        mock_analyze,
        mock_record,
        mock_get_analysis,
        mock_update_llm,
        mock_run_gemini,
        mock_consent,
        minimal_zip,
    ):
        """update_llm_summary is called with the correct UUID and summary text."""
        from backend.task_manager import TaskInfo, TaskManager, TaskStatus, TaskType

        mock_analyze.return_value = {
            "projects": [{"project_name": "Test", "project_path": "project"}],
            "analysis_metadata": {
                "zip_file": str(minimal_zip),
                "analysis_timestamp": "2025-01-01T00:00:00",
            },
            "summary": {},
        }

        fake_row = MagicMock()
        fake_row.__getitem__ = lambda self, k: "uuid-123" if k == "analysis_uuid" else None
        fake_row.__bool__ = lambda self: True
        mock_get_analysis.return_value = fake_row

        mock_run_gemini.return_value = {"llm_summary": SAMPLE_LLM_SUMMARY, "llm_error": None}

        task = TaskInfo(
            task_id="t-llm-1",
            task_type=TaskType.NEW_PORTFOLIO,
            status=TaskStatus.RUNNING,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            username="testuser",
            filename="test.zip",
            file_path=str(minimal_zip),
            file_hash="abc123",
            analysis_type="llm",
        )

        manager = TaskManager()
        result = asyncio.run(manager._process_new_portfolio(task))

        assert result.get("llm_ran") is True
        assert result.get("llm_error") is None
        mock_update_llm.assert_called_once_with("uuid-123", SAMPLE_LLM_SUMMARY, "testuser")

    @patch("backend.database.check_user_consent", return_value=True)
    @patch("backend.analysis.llm_pipeline.run_gemini_analysis")
    @patch("backend.analysis_database.update_llm_summary")
    @patch("backend.analysis_database.get_analysis")
    @patch("backend.analysis_database.record_analysis", return_value=1)
    @patch("backend.cli.analyze_folder")
    def test_record_analysis_called_only_once(
        self,
        mock_analyze,
        mock_record,
        mock_get_analysis,
        mock_update_llm,
        mock_run_gemini,
        mock_consent,
        minimal_zip,
    ):
        """record_analysis must only be called once (for the non-LLM analysis)."""
        from backend.task_manager import TaskInfo, TaskManager, TaskStatus, TaskType

        mock_analyze.return_value = {
            "projects": [{"project_name": "Test", "project_path": "project"}],
            "analysis_metadata": {
                "zip_file": str(minimal_zip),
                "analysis_timestamp": "2025-01-01T00:00:00",
            },
            "summary": {},
        }

        fake_row = MagicMock()
        fake_row.__getitem__ = lambda self, k: "uuid-456" if k == "analysis_uuid" else None
        fake_row.__bool__ = lambda self: True
        mock_get_analysis.return_value = fake_row

        mock_run_gemini.return_value = {"llm_summary": SAMPLE_LLM_SUMMARY, "llm_error": None}

        task = TaskInfo(
            task_id="t-llm-2",
            task_type=TaskType.NEW_PORTFOLIO,
            status=TaskStatus.RUNNING,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            username="testuser",
            filename="test.zip",
            file_path=str(minimal_zip),
            file_hash="abc456",
            analysis_type="llm",
        )

        manager = TaskManager()
        asyncio.run(manager._process_new_portfolio(task))

        assert mock_record.call_count == 1, (
            "record_analysis must only be called once. "
            "A second call would create duplicate project rows in the database."
        )
