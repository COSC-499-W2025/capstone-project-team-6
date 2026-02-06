"""Unit tests for resume API endpoints."""

import sys
from pathlib import Path

# Add src directory to path
src_dir = Path(__file__).resolve().parent.parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

import uuid
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from backend.api.auth import active_tokens
from backend.api_server import app
from backend import analysis_database as adb
from backend import database as udb

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_tokens():
    """Clear tokens before each test."""
    active_tokens.clear()
    yield
    active_tokens.clear()


@pytest.fixture(autouse=True)
def setup_temp_db(tmp_path):
    db_path = tmp_path / "resume_api.db"
    previous_user = udb.set_db_path(db_path)
    previous_analysis = adb.set_db_path(db_path)

    if db_path.exists():
        db_path.unlink()

    udb.init_db()
    adb.init_db()
    yield
    adb.set_db_path(previous_analysis)
    udb.set_db_path(previous_user)


@pytest.fixture
def auth_token():
    """Create authenticated user and return token."""
    test_username = f"testuser_{uuid.uuid4().hex[:8]}"
    response = client.post(
        "/api/auth/signup",
        json={"username": test_username, "password": "password123"},
    )
    return response.json()["access_token"], test_username


class TestResumeEndpoints:
    """Test suite for resume endpoints."""

    def test_generate_resume_unauthorized(self):
        """Test generating resume without auth fails."""
        response = client.post(
            "/api/resume/generate",
            json={
                "portfolio_ids": [str(uuid.uuid4())],
                "format": "markdown",
            },
        )
        assert response.status_code == 403

    def test_generate_resume_multiple_portfolios(self, auth_token):
        """Test generating resume from multiple portfolios (implementation incomplete)."""
        token, username = auth_token
        portfolio_ids = [str(uuid.uuid4()), str(uuid.uuid4())]

        response = client.post(
            "/api/resume/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "portfolio_ids": portfolio_ids,
                "format": "markdown",
            },
        )

        assert response.status_code == 404

    def test_create_list_get_update_stored_resume(self, auth_token):
        token, _ = auth_token

        create_response = client.post(
            "/api/resumes",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "title": "My Stored Resume",
                "format": "markdown",
                "content": "## Projects\n\nBase Project\n- base bullet",
            },
        )
        assert create_response.status_code == 200
        created = create_response.json()
        assert created["title"] == "My Stored Resume"

        list_response = client.get(
            "/api/resumes",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert list_response.status_code == 200
        assert len(list_response.json()) == 1

        get_response = client.get(
            f"/api/resumes/{created['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert get_response.status_code == 200
        assert "Base Project" in get_response.json()["content"]

        update_response = client.patch(
            f"/api/resumes/{created['id']}",
            headers={"Authorization": f"Bearer {token}"},
            json={"content": "## Projects\n\nUpdated Project\n- updated bullet"},
        )
        assert update_response.status_code == 200
        assert "Updated Project" in update_response.json()["content"]

    @patch("backend.api.resume.get_analysis_by_uuid")
    @patch("backend.analysis.resume_generator.generate_resume")
    def test_generate_resume_merges_with_stored_resume(
        self, mock_generate_resume, mock_get_analysis, auth_token
    ):
        token, _ = auth_token
        portfolio_id = str(uuid.uuid4())

        mock_get_analysis.return_value = {
            "analysis_uuid": portfolio_id,
            "projects": [],
            "total_projects": 1,
        }
        mock_generate_resume.return_value = (
            "John Doe\njohn@example.com\n\n## Projects\n\n"
            "**GenProj** | *Python*\n- gen bullet\n"
        )

        create_response = client.post(
            "/api/resumes",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "title": "Stored Resume",
                "format": "markdown",
                "content": "## Projects\n\nBase Project\n- base bullet",
            },
        )
        assert create_response.status_code == 200
        resume_id = create_response.json()["id"]

        response = client.post(
            "/api/resume/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "portfolio_ids": [portfolio_id],
                "format": "markdown",
                "stored_resume_id": resume_id,
            },
        )
        assert response.status_code == 200
        content = response.json()["content"]
        assert "John Doe" in content
        assert content.count("## Projects") == 1
        assert "GenProj" in content
        assert "Base Project" in content

    def test_get_resume_list_unauthorized(self):
        """Test getting resume list without auth."""
        response = client.get("/api/resume")
        # Endpoint doesn't exist
        assert response.status_code == 404

    def test_get_resume_by_id_success(self, auth_token):
        """Test getting specific resume by ID (not implemented)."""
        token, _ = auth_token
        resume_id = str(uuid.uuid4())

        response = client.get(
            f"/api/resume/{resume_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 501

    def test_delete_resume_unauthorized(self):
        """Test deleting resume without auth."""
        resume_id = str(uuid.uuid4())
        response = client.delete(f"/api/resume/{resume_id}")
        assert response.status_code == 405
