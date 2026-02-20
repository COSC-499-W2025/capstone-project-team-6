"""
Unit tests for task manager LLM analysis behavior.

Verifies the fix for duplicate projects when LLM analysis runs:
LLM record_analysis must be called with projects=[] to avoid creating duplicate project rows.
"""

import sys
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

src_dir = Path(__file__).resolve().parent.parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from datetime import datetime

from backend.task_manager import TaskInfo, TaskManager, TaskStatus, TaskType


@pytest.fixture
def minimal_zip(tmp_path):
    """Create a minimal valid project ZIP."""
    zip_path = tmp_path / "test.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("project/main.py", "print('hi')")
        zf.writestr("project/README.md", "# Test")
    return zip_path


@pytest.fixture
def task_with_llm(minimal_zip):
    """Create a TaskInfo for new portfolio with LLM analysis type."""
    return TaskInfo(
        task_id="test-llm-1",
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


@patch("backend.database.check_user_consent")
@patch("backend.task_manager.get_analysis")
@patch("backend.task_manager.record_analysis")
@patch("backend.task_manager.run_gemini_analysis")
@patch("backend.task_manager.analyze_folder")
def test_llm_analysis_passes_empty_projects_to_record_analysis(
    mock_analyze,
    mock_run_gemini,
    mock_record,
    mock_get_analysis,
    mock_consent,
    task_with_llm,
):
    """When LLM analysis runs, record_analysis('llm', payload) must receive projects=[]."""
    mock_consent.return_value = True
    mock_get_analysis.return_value = {"analysis_uuid": "uuid-123"}

    non_llm_result = {
        "projects": [{"project_name": "Test", "project_path": "project"}],
        "analysis_metadata": {"analysis_uuid": "uuid-123"},
    }
    mock_analyze.return_value = non_llm_result

    llm_result = {"skills": [], "architecture": {}}
    mock_run_gemini.return_value = llm_result

    mock_record.return_value = 1

    manager = TaskManager()
    import asyncio

    result = asyncio.get_event_loop().run_until_complete(
        manager._process_new_portfolio(task_with_llm)
    )

    assert result.get("llm_ran") is True

    # Find the LLM call (the one with non_llm_results and projects=[])
    record_calls = mock_record.call_args_list
    llm_call = None
    for call in record_calls:
        payload = call[0][1]
        if "non_llm_results" in payload:
            llm_call = call
            break
    assert llm_call is not None, "Expected record_analysis call with non_llm_results"
    llm_payload = llm_call[0][1]
    assert llm_payload.get("projects") == [], (
        "LLM record_analysis must receive projects=[] to avoid duplicate project rows"
    )
