"""Unit tests for portfolios API endpoints."""

import sys
from pathlib import Path

src_dir = Path(__file__).resolve().parent.parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

import uuid
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from backend.api.auth import active_tokens
from backend.api_server import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_tokens():
    """Clear tokens before each test."""
    active_tokens.clear()
    yield
    active_tokens.clear()


@pytest.fixture
def auth_token():
    """Create authenticated user and return token."""
    test_username = f"testuser_{uuid.uuid4().hex[:8]}"
    response = client.post(
        "/api/auth/signup",
        json={"username": test_username, "password": "password123"},
    )
    return response.json()["access_token"], test_username


class TestPortfoliosEndpoints:
    """Test suite for portfolios endpoints."""

    @patch("backend.api_server.get_all_analyses_for_user")
    def test_list_portfolios_success(self, mock_get_analyses, auth_token):
        """Test listing user portfolios."""
        token, username = auth_token

        mock_get_analyses.return_value = [
            {
                "analysis_uuid": str(uuid.uuid4()),
                "zip_file": "test.zip",
                "analysis_timestamp": "2026-01-24T10:00:00",
                "total_projects": 5,
                "analysis_type": "llm",
            }
        ]

        response = client.get(
            "/api/portfolios",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["total_projects"] == 5
        assert data[0]["analysis_type"] == "llm"
        mock_get_analyses.assert_called_once_with(username)

    def test_list_portfolios_unauthorized(self):
        """Test listing portfolios without auth fails."""
        response = client.get("/api/portfolios")
        assert response.status_code in (401, 403)  # 401 Unauthorized or 403 Forbidden (platform-dependent)

    @patch("backend.api_server.get_all_analyses_for_user")
    def test_list_portfolios_empty(self, mock_get_analyses, auth_token):
        """Test listing portfolios returns empty list for new user."""
        token, username = auth_token
        mock_get_analyses.return_value = []

        response = client.get(
            "/api/portfolios",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert response.json() == []

    @patch("backend.api_server.get_analysis_by_uuid")
    def test_get_portfolio_success(self, mock_get_analysis, auth_token):
        """Test getting portfolio details."""
        token, username = auth_token
        portfolio_id = str(uuid.uuid4())

        mock_get_analysis.return_value = {
            "analysis_uuid": portfolio_id,
            "analysis_type": "llm",
            "zip_file": "test.zip",
            "analysis_timestamp": "2026-01-24T10:00:00",
            "total_projects": 3,
            "projects": [],
            "skills": [],
            "summary": {},
        }

        response = client.get(
            f"/api/portfolios/{portfolio_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["analysis_uuid"] == portfolio_id
        assert data["total_projects"] == 3
        mock_get_analysis.assert_called_once_with(portfolio_id, username)

    @patch("backend.api_server.get_analysis_by_uuid")
    def test_get_portfolio_not_found(self, mock_get_analysis, auth_token):
        """Test getting non-existent portfolio fails."""
        token, _ = auth_token
        mock_get_analysis.return_value = None

        portfolio_id = str(uuid.uuid4())
        response = client.get(
            f"/api/portfolios/{portfolio_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @patch("backend.api.portfolios.get_analysis_by_uuid")
    def test_get_portfolio_alias(self, mock_get_analysis, auth_token):
        """Test portfolio alias endpoint works."""
        token, username = auth_token
        portfolio_id = str(uuid.uuid4())

        mock_get_analysis.return_value = {
            "analysis_uuid": portfolio_id,
            "analysis_type": "llm",
            "zip_file": "test.zip",
            "analysis_timestamp": "2026-01-24T10:00:00",
            "total_projects": 1,
            "projects": [],
            "skills": [],
        }

        response = client.get(
            f"/api/portfolio/{portfolio_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200

    def test_delete_portfolio_unauthorized(self):
        """Test deleting portfolio without auth fails."""
        portfolio_id = str(uuid.uuid4())
        response = client.delete(f"/api/portfolios/{portfolio_id}")
        assert response.status_code in (401, 403)  # 401 Unauthorized or 403 Forbidden (platform-dependent)

    @patch("backend.api_server.check_user_consent")
    def test_save_consent_success(self, mock_check_consent, auth_token):
        """Test saving user consent."""
        token, username = auth_token

        response = client.post(
            "/api/user/consent",
            headers={"Authorization": f"Bearer {token}"},
            json={"has_consented": True},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["has_consented"] is True
        assert "saved" in data["message"].lower()

    @patch("backend.api_server.check_user_consent")
    def test_get_consent_success(self, mock_check_consent, auth_token):
        """Test getting user consent status."""
        token, username = auth_token
        mock_check_consent.return_value = True

        response = client.get(
            "/api/user/consent",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["has_consented"] is True
        mock_check_consent.assert_called_once()

    def test_get_consent_unauthorized(self):
        """Test getting consent without auth fails."""
        response = client.get("/api/user/consent")
        assert response.status_code == 403

    @patch("backend.api_server.check_user_consent", return_value=True)
    @patch("backend.api_server.get_task_manager")
    def test_upload_new_portfolio_success(self, mock_get_task_manager, mock_check_consent, auth_token):
        """Test uploading a new portfolio (happy path)."""
        token, username = auth_token
        mock_task_manager = mock_get_task_manager.return_value
        mock_task_manager.create_task.return_value = "task-uuid"

        file_content = b"fake zip content"
        response = client.post(
            "/api/portfolios/upload",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("test.zip", file_content, "application/zip")},
            data={"analysis_type": "llm"},
        )
        assert response.status_code == 202
        data = response.json()
        assert data["details"]["task_id"] == "task-uuid"
        assert data["details"]["status"] == "processing"

    @patch("backend.api_server.get_analysis_by_uuid")
    @patch("backend.api_server.check_user_consent", return_value=True)
    @patch("backend.api_server.get_task_manager")
    def test_add_to_existing_portfolio_success(self, mock_get_task_manager, mock_check_consent, mock_get_analysis, auth_token):
        """Test adding to an existing portfolio (happy path)."""
        token, username = auth_token
        portfolio_id = str(uuid.uuid4())
        mock_get_analysis.return_value = {"analysis_uuid": portfolio_id}
        mock_task_manager = mock_get_task_manager.return_value
        mock_task_manager.create_task.return_value = "task-uuid"

        file_content = b"more zip content"
        response = client.post(
            f"/api/portfolios/{portfolio_id}/add",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("add.zip", file_content, "application/zip")},
        )
        assert response.status_code == 202
        data = response.json()
        assert data["details"]["task_id"] == "task-uuid"
        assert data["details"]["portfolio_id"] == portfolio_id
        assert data["details"]["status"] == "processing"

    @patch("backend.api_server.get_analysis_by_uuid")
    @patch("backend.api_server.delete_analysis")
    def test_delete_portfolio_success(self, mock_delete_analysis, mock_get_analysis, auth_token):
        """Test deleting a portfolio (happy path)."""
        token, username = auth_token
        portfolio_id = str(uuid.uuid4())
        mock_get_analysis.return_value = {"analysis_uuid": portfolio_id}
        mock_delete_analysis.return_value = True

        response = client.delete(
            f"/api/portfolios/{portfolio_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "deleted successfully" in data["message"].lower()
        mock_get_analysis.assert_called_once_with(portfolio_id, username)
        mock_delete_analysis.assert_called_once_with(portfolio_id, username)
