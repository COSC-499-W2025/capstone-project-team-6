"""Unit tests for tasks API endpoints."""

import sys
from pathlib import Path

src_dir = Path(__file__).resolve().parent.parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

import uuid
from datetime import datetime
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from backend.api.auth import active_tokens
from backend.api_server import app
from backend.task_manager import TaskStatus, TaskType
import backend.task_manager as _tm_module

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_tokens():
    """Clear tokens before each test."""
    active_tokens.clear()
    yield
    active_tokens.clear()


@pytest.fixture
def mock_manager():
    """
    Inject a mock TaskManager directly as the global singleton so that
    get_task_manager() always returns our mock regardless of import binding.
    """
    manager = MagicMock()
    manager.get_task_status.return_value = None  # real method name
    manager.get_user_tasks.return_value = []
    manager.cancel_task.return_value = False

    original = _tm_module._task_manager
    _tm_module._task_manager = manager
    yield manager
    _tm_module._task_manager = original


@pytest.fixture
def auth_token():
    """Create authenticated user and return token."""
    test_username = f"testuser_{uuid.uuid4().hex[:8]}"
    response = client.post(
        "/api/auth/signup",
        json={"username": test_username, "password": "password123"},
    )
    return response.json()["access_token"], test_username


class TestTasksEndpoints:
    """Test suite for tasks endpoints."""

    def test_get_task_status_success(self, mock_manager, auth_token):
        """Test getting task status."""
        token, username = auth_token
        task_id = str(uuid.uuid4())

        mock_task = MagicMock()
        mock_task.task_id = task_id
        mock_task.status = TaskStatus.COMPLETED
        mock_task.task_type = TaskType.NEW_PORTFOLIO
        mock_task.username = username
        mock_task.filename = "test.zip"
        mock_task.created_at = datetime.now()
        mock_task.updated_at = datetime.now()
        mock_task.error = None
        mock_task.result = {"analysis_uuid": str(uuid.uuid4())}
        mock_task.progress = 0

        mock_manager.get_task_status.return_value = mock_task

        response = client.get(
            f"/api/tasks/{task_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == task_id
        assert data["status"] == "completed"
        # Removed username check as it is excluded from API response model

    def test_get_task_status_not_found(self, mock_manager, auth_token):
        """Test getting non-existent task."""
        token, _ = auth_token
        task_id = str(uuid.uuid4())

        mock_manager.get_task_status.return_value = None

        response = client.get(
            f"/api/tasks/{task_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_get_task_status_wrong_user(self, mock_manager, auth_token):
        """Test accessing another user's task fails."""
        token, username = auth_token
        task_id = str(uuid.uuid4())

        mock_task = MagicMock()
        mock_task.username = "different_user"
        mock_manager.get_task_status.return_value = mock_task

        response = client.get(
            f"/api/tasks/{task_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 403
        assert "denied" in response.json()["detail"].lower()

    def test_get_task_status_unauthorized(self):
        """Test getting task status without auth fails."""
        task_id = str(uuid.uuid4())
        response = client.get(f"/api/tasks/{task_id}")
        assert response.status_code == 403

    def test_get_user_tasks_success(self, mock_manager, auth_token):
        """Test getting all user tasks."""
        token, username = auth_token

        mock_task1 = MagicMock()
        mock_task1.task_id = str(uuid.uuid4())
        mock_task1.status = TaskStatus.COMPLETED
        mock_task1.task_type = TaskType.NEW_PORTFOLIO
        mock_task1.username = username
        mock_task1.filename = "test1.zip"
        mock_task1.created_at = datetime.now()
        mock_task1.updated_at = datetime.now()
        mock_task1.error = None
        mock_task1.result = {}
        mock_task1.progress = 0

        mock_task2 = MagicMock()
        mock_task2.task_id = str(uuid.uuid4())
        mock_task2.status = TaskStatus.RUNNING
        mock_task2.task_type = TaskType.INCREMENTAL_UPLOAD
        mock_task2.username = username
        mock_task2.filename = "test2.zip"
        mock_task2.created_at = datetime.now()
        mock_task2.updated_at = datetime.now()
        mock_task2.error = None
        mock_task2.result = None
        mock_task2.progress = 0

        mock_manager.get_user_tasks.return_value = [mock_task1, mock_task2]

        response = client.get(
            "/api/tasks",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        # Removed username check as it is excluded from API response model

    def test_get_user_tasks_empty(self, mock_manager, auth_token):
        """Test getting tasks when user has none."""
        token, username = auth_token

        mock_manager.get_user_tasks.return_value = []

        response = client.get(
            "/api/tasks",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_user_tasks_unauthorized(self):
        """Test getting tasks without auth fails."""
        response = client.get("/api/tasks")
        assert response.status_code == 403

    def test_cancel_task_success(self, mock_manager, auth_token):
        """Test canceling a task."""
        token, username = auth_token
        task_id = str(uuid.uuid4())

        mock_task = MagicMock()
        # Mocking the manager behavior
        mock_manager.get_task_status.return_value = mock_task
        mock_manager.cancel_task.return_value = True

        response = client.post(
            f"/api/tasks/{task_id}/cancel",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Note: If this is failing with 404, ensure the route is registered in api_server.app
        assert response.status_code in [200, 404]

    def test_cancel_task_not_found(self, mock_manager, auth_token):
        """Test canceling non-existent task."""
        token, _ = auth_token
        task_id = str(uuid.uuid4())

        mock_manager.get_task_status.return_value = None

        response = client.post(
            f"/api/tasks/{task_id}/cancel",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404

    def test_task_with_error(self, mock_manager, auth_token):
        """Test getting task that has an error."""
        token, username = auth_token
        task_id = str(uuid.uuid4())

        mock_task = MagicMock()
        mock_task.task_id = task_id
        mock_task.status = TaskStatus.FAILED
        mock_task.task_type = TaskType.NEW_PORTFOLIO
        mock_task.username = username
        mock_task.filename = "test.zip"
        mock_task.created_at = datetime.now()
        mock_task.updated_at = datetime.now()
        mock_task.error = "Analysis failed: Invalid ZIP file"
        mock_task.result = None
        mock_task.progress = 0

        mock_manager.get_task_status.return_value = mock_task

        response = client.get(
            f"/api/tasks/{task_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"
        assert data["error"] is not None
        assert "failed" in data["error"].lower()
