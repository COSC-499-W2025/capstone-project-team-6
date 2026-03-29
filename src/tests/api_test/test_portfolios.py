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
        assert response.status_code == 403

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
        assert response.status_code == 403

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

    @patch("backend.api_server.get_user_portfolio_settings")
    def test_get_portfolio_settings_success(self, mock_get_settings, auth_token):
        token, _ = auth_token
        mock_get_settings.return_value = {
            "showSkills": True,
            "showProjects": False,
            "showPortfolioItems": True,
        }
        response = client.get(
            "/api/portfolio/settings",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["settings"]["showProjects"] is False
        mock_get_settings.assert_called_once()

    @patch("backend.api_server.upsert_user_portfolio_settings")
    def test_save_portfolio_settings_success(self, mock_save_settings, auth_token):
        token, _ = auth_token
        mock_save_settings.return_value = {
            "showSkills": True,
            "showProjects": True,
            "showPortfolioItems": True,
        }
        response = client.post(
            "/api/portfolio/settings",
            headers={"Authorization": f"Bearer {token}"},
            json={"settings": {"showProjects": True}},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["settings"]["showProjects"] is True
        mock_save_settings.assert_called_once()

    @patch("backend.api_server.list_public_portfolios")
    def test_list_public_portfolios_success(self, mock_list_public, auth_token):
        """Test listing public portfolios with filters."""
        token, _ = auth_token
        mock_list_public.return_value = {
            "items": [
                {
                    "analysis_uuid": str(uuid.uuid4()),
                    "username": "alice",
                    "analysis_type": "llm",
                    "analysis_timestamp": "2026-01-24T10:00:00",
                    "published_at": "2026-01-25T10:00:00",
                    "total_projects": 3,
                    "project_names": ["project-alpha"],
                    "project_types": ["Backend Developer"],
                    "top_languages": ["Python"],
                    "top_skills": ["FastAPI"],
                    "has_tests": True,
                }
            ],
            "total": 1,
            "page": 1,
            "page_size": 12,
        }
        response = client.get(
            "/api/portfolios/public?q=alice&language=Python&sort=newest&page=1&page_size=12",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["total"] == 1
        assert payload["items"][0]["username"] == "alice"
        mock_list_public.assert_called_once()

    def test_list_public_portfolios_unauthorized(self):
        """Test public portfolio listing requires auth."""
        response = client.get("/api/portfolios/public")
        assert response.status_code == 403

    @patch("backend.api_server.set_portfolio_visibility")
    def test_update_portfolio_visibility_success(self, mock_set_visibility, auth_token):
        """Test toggling portfolio visibility."""
        token, _ = auth_token
        portfolio_id = str(uuid.uuid4())
        mock_set_visibility.return_value = True
        response = client.post(
            f"/api/portfolios/{portfolio_id}/visibility",
            headers={"Authorization": f"Bearer {token}"},
            json={"is_public": True},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["analysis_uuid"] == portfolio_id
        assert body["is_public"] is True
        mock_set_visibility.assert_called_once()

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

    @patch("backend.api_server.check_user_consent", return_value=True)
    @patch("backend.api_server.get_task_manager")
    def test_multiple_uploads_return_distinct_task_ids(self, mock_get_task_manager, mock_check_consent, auth_token):
        """Multiple sequential uploads each return a distinct task_id (for multi-upload flow)."""
        token, username = auth_token
        mock_task_manager = mock_get_task_manager.return_value
        mock_task_manager.create_task.side_effect = ["task-uuid-1", "task-uuid-2"]

        file_content_1 = b"fake zip content one"
        file_content_2 = b"fake zip content two"

        r1 = client.post(
            "/api/portfolios/upload",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("project1.zip", file_content_1, "application/zip")},
            data={"analysis_type": "non_llm"},
        )
        assert r1.status_code == 202
        assert r1.json()["details"]["task_id"] == "task-uuid-1"

        r2 = client.post(
            "/api/portfolios/upload",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("project2.zip", file_content_2, "application/zip")},
            data={"analysis_type": "non_llm"},
        )
        assert r2.status_code == 202
        assert r2.json()["details"]["task_id"] == "task-uuid-2"

        assert mock_task_manager.create_task.call_count == 2
        assert r1.json()["details"]["task_id"] != r2.json()["details"]["task_id"]

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
