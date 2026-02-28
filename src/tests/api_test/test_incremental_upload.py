#!/usr/bin/env python3
"""
Unit tests for incremental portfolio upload feature.
"""

import json
import sys
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add src directory to path so backend imports work
src_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_dir))

from fastapi.testclient import TestClient

from backend.api_server import app
from backend.task_manager import TaskInfo, TaskManager, TaskStatus, TaskType


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def test_user():
    """Test user credentials."""
    return {"username": "testuser_incremental", "password": "testpass123"}


@pytest.fixture
def auth_token(client, test_user):
    """Get authentication token."""
    # Try signup first
    response = client.post("/api/auth/signup", json=test_user)
    if response.status_code == 409:
        # User exists, just login
        response = client.post("/api/auth/login", json=test_user)

    assert response.status_code in [200, 201]
    return response.json()["access_token"]


@pytest.fixture
def test_zip_file():
    tmp = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
    tmp_path = Path(tmp.name)
    tmp.close()  # <- critical for Windows

    with zipfile.ZipFile(tmp_path, "w") as zipf:
        zipf.writestr("test_project/main.py", "print('Hello World')")
        zipf.writestr("test_project/README.md", "# Test Project")

    yield tmp_path

    tmp_path.unlink(missing_ok=True)


@pytest.fixture
def additional_zip_file():
    """Create another test ZIP file with additional projects."""
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
        with zipfile.ZipFile(tmp.name, "w") as zipf:
            # Add different project
            zipf.writestr("another_project/app.py", "print('Another project')")
            zipf.writestr("another_project/README.md", "# Another Project")

        yield Path(tmp.name)

        # Cleanup
        Path(tmp.name).unlink(missing_ok=True)


class TestIncrementalUploadAPI:
    """Test incremental upload API endpoint."""

    def test_incremental_upload_endpoint_exists(self, client, auth_token):
        """Test that the incremental upload endpoint exists."""
        # Try to add to a non-existent portfolio (should return 404)
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.post(
            "/api/portfolios/fake-uuid/add",
            headers=headers,
            files={"file": ("test.zip", b"fake content", "application/zip")},
        )

        # Should fail with 404 (portfolio not found) not 405 (method not allowed)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_incremental_upload_requires_auth(self, client, test_zip_file):
        """Test that incremental upload requires authentication."""
        with open(test_zip_file, "rb") as f:
            response = client.post(
                "/api/portfolios/some-uuid/add",
                files={"file": ("test.zip", f, "application/zip")},
            )

        assert response.status_code == 403  # No auth token

    def test_incremental_upload_validates_file_type(self, client, auth_token):
        """Test that endpoint validates file type."""
        headers = {"Authorization": f"Bearer {auth_token}"}

        # Try to upload non-ZIP file
        response = client.post(
            "/api/portfolios/fake-uuid/add",
            headers=headers,
            files={"file": ("test.txt", b"not a zip", "text/plain")},
        )

        # Should fail validation before checking if portfolio exists
        assert response.status_code in [400, 404]


class TestTaskManagerIncrementalUpload:
    """Test task manager incremental upload processing."""

    @pytest.mark.asyncio
    async def test_process_incremental_upload_deduplicates_projects(self):
        """Test that incremental upload deduplicates projects by path."""
        from datetime import datetime

        # Create mock task
        task = TaskInfo(
            task_id="test-task-1",
            task_type=TaskType.INCREMENTAL_UPLOAD,
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            username="testuser",
            filename="additional.zip",
            file_path="/tmp/test.zip",
            portfolio_id="portfolio-123",
        )

        # Mock existing portfolio with one project
        existing_portfolio = {
            "projects": [
                {"project_name": "Project1", "project_path": "project1"},
            ],
            "analysis_metadata": {"total_projects": 1},
        }

        # Mock new analysis with overlapping and new projects
        new_analysis = {
            "projects": [
                {"project_name": "Project1", "project_path": "project1"},  # Duplicate
                {"project_name": "Project2", "project_path": "project2"},  # New
            ],
            "analysis_metadata": {"total_projects": 2},
        }

        task_manager = TaskManager()

        with patch(
            "backend.analysis_database.get_analysis_by_uuid",
            return_value=existing_portfolio,
        ), patch(
            "backend.cli.analyze_folder", return_value=new_analysis
        ), patch("backend.analysis_database.get_connection") as mock_conn:

            # Mock database connection with proper execute().fetchone() chain
            mock_cursor = MagicMock()
            # FIX: added "id" key so row["id"] doesn't raise KeyError
            mock_cursor.fetchone.return_value = {"id": 1, "raw_json": json.dumps(existing_portfolio)}

            mock_conn_obj = MagicMock()
            mock_conn_obj.__enter__ = MagicMock(return_value=mock_conn_obj)
            mock_conn_obj.__exit__ = MagicMock(return_value=False)
            mock_conn_obj.execute.return_value = mock_cursor
            mock_conn_obj.commit = MagicMock()

            mock_conn.return_value = mock_conn_obj

            result = await task_manager._process_incremental_upload(task)

            # Should only add 1 new project (Project2)
            assert result["added_projects"] == 1
            assert result["total_projects"] == 2
            assert result["analysis_uuid"] == "portfolio-123"

            # Verify database was updated
            assert mock_conn_obj.commit.called

    @pytest.mark.asyncio
    async def test_process_incremental_upload_handles_missing_portfolio(self):
        """Test that incremental upload fails gracefully when portfolio not found."""
        task = TaskInfo(
            task_id="test-task-2",
            task_type=TaskType.INCREMENTAL_UPLOAD,
            status=TaskStatus.PENDING,
            created_at=MagicMock(),
            updated_at=MagicMock(),
            username="testuser",
            filename="additional.zip",
            file_path="/tmp/test.zip",
            portfolio_id="nonexistent-portfolio",
        )

        task_manager = TaskManager()

        with patch("backend.analysis_database.get_analysis_by_uuid", return_value=None):
            with pytest.raises(ValueError, match="not found"):
                await task_manager._process_incremental_upload(task)

    @pytest.mark.asyncio
    async def test_process_incremental_upload_updates_database(self):
        """Test that incremental upload updates the database correctly."""
        task = TaskInfo(
            task_id="test-task-3",
            task_type=TaskType.INCREMENTAL_UPLOAD,
            status=TaskStatus.PENDING,
            created_at=MagicMock(),
            updated_at=MagicMock(),
            username="testuser",
            filename="additional.zip",
            file_path="/tmp/test.zip",
            portfolio_id="portfolio-789",
        )

        existing_portfolio = {
            "projects": [{"project_name": "Old", "project_path": "old"}],
            "analysis_metadata": {"total_projects": 1},
        }

        new_analysis = {
            "projects": [{"project_name": "New", "project_path": "new"}],
            "analysis_metadata": {"total_projects": 1},
        }

        task_manager = TaskManager()

        with patch(
            "backend.analysis_database.get_analysis_by_uuid",
            return_value=existing_portfolio,
        ), patch(
            "backend.cli.analyze_folder", return_value=new_analysis
        ), patch("backend.analysis_database.get_connection") as mock_conn:

            mock_conn_obj = MagicMock()
            mock_conn_obj.__enter__ = MagicMock(return_value=mock_conn_obj)
            mock_conn_obj.__exit__ = MagicMock(return_value=False)
            mock_row = {"id": 1, "raw_json": json.dumps(existing_portfolio)}
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = mock_row
            mock_conn_obj.execute.return_value = mock_cursor
            mock_conn_obj.commit = MagicMock()

            mock_conn.return_value = mock_conn_obj

            result = await task_manager._process_incremental_upload(task)

            # Verify database was updated
            assert mock_conn_obj.commit.called

            # Verify UPDATE query was executed
            update_calls = [call for call in mock_conn_obj.execute.call_args_list if "UPDATE" in str(call)]
            assert len(update_calls) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])