"""Unit tests for projects API endpoints."""

import sys
from pathlib import Path

src_dir = Path(__file__).resolve().parent.parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

import uuid
from unittest.mock import MagicMock, patch

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


class TestProjectsEndpoints:
    """Test suite for projects endpoints."""

    @patch("backend.api.projects.get_user_projects")
    def test_list_projects_success(self, mock_get_projects, auth_token):
        """Test listing user projects."""
        token, username = auth_token

        mock_get_projects.return_value = [
            {
                "id": 1,
                "project_name": "test_project",
                "primary_language": "python",
                "total_files": 10,
            }
        ]

        response = client.get(
            "/api/projects",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == username
        assert data["total_projects"] == 1
        assert len(data["projects"]) == 1
        mock_get_projects.assert_called_once_with(username)

    def test_list_projects_unauthorized(self):
        """Test listing projects without auth fails."""
        response = client.get("/api/projects")
        assert response.status_code == 403

    def test_list_projects_invalid_token(self):
        """Test listing projects with invalid token fails."""
        response = client.get(
            "/api/projects",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401

    @patch("backend.api.projects.get_user_projects")
    def test_list_projects_empty(self, mock_get_projects, auth_token):
        """Test listing projects returns empty list for new user."""
        token, username = auth_token
        mock_get_projects.return_value = []

        response = client.get(
            "/api/projects",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_projects"] == 0
        assert data["projects"] == []

    @patch("backend.api.projects.get_analysis_by_uuid")
    def test_get_project_detail_success(self, mock_get_analysis, auth_token):
        """Test getting project details."""
        token, username = auth_token
        portfolio_uuid = str(uuid.uuid4())
        project_path = "test_project"

        mock_get_analysis.return_value = {
            "analysis_uuid": portfolio_uuid,
            "projects": [
                {
                    "name": "Test Project",
                    "path": project_path,
                    "metadata": {"total_files": 10},
                }
            ],
        }

        response = client.get(
            f"/api/projects/{portfolio_uuid}:{project_path}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Project"
        assert data["path"] == project_path

    def test_get_project_detail_invalid_format(self, auth_token):
        """Test getting project with invalid ID format fails."""
        token, _ = auth_token

        response = client.get(
            "/api/projects/invalid-id-format",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 400
        assert "Invalid project_id format" in response.json()["detail"]

    @patch("backend.api.projects.get_analysis_by_uuid")
    def test_get_project_detail_portfolio_not_found(self, mock_get_analysis, auth_token):
        """Test getting project from non-existent portfolio fails."""
        token, _ = auth_token
        mock_get_analysis.return_value = None

        portfolio_uuid = str(uuid.uuid4())
        response = client.get(
            f"/api/projects/{portfolio_uuid}:test_project",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @patch("backend.api.projects.get_analysis_by_uuid")
    def test_get_project_detail_project_not_found(self, mock_get_analysis, auth_token):
        """Test getting non-existent project fails."""
        token, _ = auth_token
        portfolio_uuid = str(uuid.uuid4())

        mock_get_analysis.return_value = {
            "analysis_uuid": portfolio_uuid,
            "projects": [{"name": "Other", "path": "other"}],
        }

        response = client.get(
            f"/api/projects/{portfolio_uuid}:nonexistent",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404

    @patch("backend.analysis_database.get_connection")
    @patch("backend.api.projects.get_user_projects")
    def test_get_aggregated_skills(self, mock_get_projects, mock_get_connection, auth_token):
        """Test getting aggregated skills."""
        token, username = auth_token

        # API queries project_skills table by project id - mock must include id
        mock_get_projects.return_value = [
            {"id": 1, "project_name": "Project1", "name": "Project1"},
            {"id": 2, "project_name": "Project2", "name": "Project2"},
        ]

        # Mock skills from project_skills: Project1 has Python, FastAPI; Project2 has Python, React
        mock_cursor = MagicMock()
        mock_cursor.fetchall.side_effect = [
            [{"skill": "Python"}, {"skill": "FastAPI"}],
            [{"skill": "Python"}, {"skill": "React"}],
        ]
        mock_conn = MagicMock()
        mock_conn.execute.return_value = mock_cursor
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_get_connection.return_value = mock_conn

        response = client.get(
            "/api/skills",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == username
        assert data["total_skills"] == 3
        assert len(data["skills"]) == 3

        # Python should appear in 2 projects
        python_skill = next(s for s in data["skills"] if s["skill"] == "Python")
        assert python_skill["count"] == 2

    @patch("backend.api.projects.get_user_projects")
    def test_get_aggregated_skills_empty(self, mock_get_projects, auth_token):
        """Test getting skills with no projects."""
        token, username = auth_token
        mock_get_projects.return_value = []

        response = client.get(
            "/api/skills",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_skills"] == 0
        assert data["skills"] == []
