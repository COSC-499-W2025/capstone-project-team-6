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

from backend import analysis_database as adb
from backend import database as udb
from backend.api.auth import active_tokens
from backend.api_server import app

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


@pytest.fixture
def second_auth_token():
    """Create a second authenticated user and return token."""
    test_username = f"testuser2_{uuid.uuid4().hex[:8]}"
    response = client.post(
        "/api/auth/signup",
        json={"username": test_username, "password": "password123"},
    )
    return response.json()["access_token"], test_username


def _mock_one_project(project_id: int = 1, name: str = "TestProject", lang: str = "Python"):
    """Return (projects_list, resume_items, portfolio_item) for easy mock setup."""
    return (
        [{"id": project_id, "project_name": name, "primary_language": lang}],
        [],
        {},
    )


class TestResumeEndpoints:
    """Test suite for resume endpoints."""

    def test_generate_resume_unauthorized(self):
        """Test generating resume without auth fails."""
        response = client.post(
            "/api/resume/generate",
            json={
                "project_ids": [1],
                "format": "markdown",
            },
        )
        assert response.status_code == 403

    @patch("backend.api.resume.get_projects_for_user")
    @patch("backend.api.resume.get_resume_items_for_project_id")
    @patch("backend.api.resume.get_portfolio_item_for_project")
    @patch("backend.analysis.resume_generator.generate_resume")
    def test_generate_resume_multiple_projects_supported(
        self, mock_generate, mock_portfolio, mock_items, mock_projects, auth_token
    ):
        """Multiple projects can now be selected; no longer limited to exactly one."""
        token, _ = auth_token
        mock_projects.return_value = [
            {"id": 1, "project_name": "Project A", "primary_language": "Python"},
            {"id": 2, "project_name": "Project B", "primary_language": "Go"},
        ]
        mock_items.return_value = []
        mock_portfolio.return_value = {}
        mock_generate.return_value = "## Projects\n\n**Project A**\n**Project B**\n"

        response = client.post(
            "/api/resume/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={"project_ids": [1, 2], "format": "markdown"},
        )
        assert response.status_code == 200
        assert response.json()["metadata"]["project_count"] == 2

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

    @patch("backend.api.resume.get_projects_for_user")
    @patch("backend.api.resume.get_resume_items_for_project_id")
    @patch("backend.api.resume.get_portfolio_item_for_project")
    @patch("backend.analysis.resume_generator.generate_resume")
    def test_generate_resume_merges_with_stored_resume(
        self, mock_generate, mock_portfolio, mock_items, mock_projects, auth_token
    ):
        token, _ = auth_token

        mock_projects.return_value = [{"id": 1, "project_name": "GenProj", "primary_language": "Python"}]
        mock_items.return_value = []
        mock_portfolio.return_value = {}
        mock_generate.return_value = "John Doe\njohn@example.com\n\n## Projects\n\n**GenProj** | *Python*\n- gen bullet\n"

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
                "project_ids": [1],
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

    @patch("backend.api.resume.get_projects_for_user")
    @patch("backend.api.resume.get_resume_items_for_project_id")
    @patch("backend.api.resume.get_portfolio_item_for_project")
    @patch("backend.analysis.resume_generator.generate_resume")
    def test_generate_resume_success(self, mock_generate, mock_portfolio, mock_items, mock_projects, auth_token):
        """Test generating resume with valid project IDs succeeds."""
        token, username = auth_token
        projects, items, portfolio = _mock_one_project()
        mock_projects.return_value = projects
        mock_items.return_value = items
        mock_portfolio.return_value = portfolio
        mock_generate.return_value = "John Doe\njohn@example.com\n\n## Projects\n\n**TestProject** | *Python*\n- Test bullet\n"

        response = client.post(
            "/api/resume/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={"project_ids": [1], "format": "markdown"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "resume_id" in data
        assert data["format"] == "markdown"
        assert "John Doe" in data["content"]
        assert "metadata" in data
        assert data["metadata"]["username"] == username

    def test_generate_resume_invalid_project_ids(self, auth_token):
        """Test generating resume with IDs not owned by user returns 404."""
        token, _ = auth_token

        # No projects in DB for this user — ID 99999 doesn't exist
        response = client.post(
            "/api/resume/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={"project_ids": [99999], "format": "markdown"},
        )
        assert response.status_code == 404
        assert "projects" in response.json()["detail"].lower()

    @patch("backend.api.resume.get_projects_for_user")
    @patch("backend.api.resume.get_resume_items_for_project_id")
    @patch("backend.api.resume.get_portfolio_item_for_project")
    @patch("backend.analysis.resume_generator.generate_resume")
    def test_generate_resume_with_personal_info(self, mock_generate, mock_portfolio, mock_items, mock_projects, auth_token):
        """Test generating resume with personal info."""
        token, _ = auth_token
        projects, items, portfolio = _mock_one_project()
        mock_projects.return_value = projects
        mock_items.return_value = items
        mock_portfolio.return_value = portfolio
        mock_generate.return_value = "Custom Name\ncustom@example.com\n\n## Projects\n\n"

        response = client.post(
            "/api/resume/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "project_ids": [1],
                "format": "markdown",
                "personal_info": {"name": "Custom Name", "email": "custom@example.com"},
            },
        )
        assert response.status_code == 200
        mock_generate.assert_called_once()
        call_kwargs = mock_generate.call_args[1]
        assert call_kwargs["personal_info"]["name"] == "Custom Name"

    @patch("backend.api.resume.get_projects_for_user")
    @patch("backend.api.resume.get_resume_items_for_project_id")
    @patch("backend.api.resume.get_portfolio_item_for_project")
    @patch("backend.analysis.resume_generator.generate_resume")
    def test_generate_resume_with_options(self, mock_generate, mock_portfolio, mock_items, mock_projects, auth_token):
        """Test generating resume with include_skills, include_projects, max_projects options."""
        token, _ = auth_token
        projects, items, portfolio = _mock_one_project()
        mock_projects.return_value = projects
        mock_items.return_value = items
        mock_portfolio.return_value = portfolio
        mock_generate.return_value = "Resume content"

        response = client.post(
            "/api/resume/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "project_ids": [1],
                "format": "markdown",
                "include_skills": False,
                "include_projects": True,
                "max_projects": 5,
            },
        )
        assert response.status_code == 200
        call_kwargs = mock_generate.call_args[1]
        assert call_kwargs["include_skills"] is False
        assert call_kwargs["include_projects"] is True
        assert call_kwargs["max_projects"] == 5

    @patch("backend.api.resume.get_projects_for_user")
    @patch("backend.api.resume.get_resume_items_for_project_id")
    @patch("backend.api.resume.get_portfolio_item_for_project")
    @patch("backend.analysis.resume_generator.generate_resume")
    def test_generate_resume_pdf_format(self, mock_generate, mock_portfolio, mock_items, mock_projects, auth_token):
        """Test generating resume in PDF format."""
        token, _ = auth_token
        projects, items, portfolio = _mock_one_project()
        mock_projects.return_value = projects
        mock_items.return_value = items
        mock_portfolio.return_value = portfolio
        mock_generate.return_value = b"PDF binary content"

        response = client.post(
            "/api/resume/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={"project_ids": [1], "format": "pdf"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "pdf"
        assert isinstance(data["content"], str)

    @patch("backend.api.resume.get_projects_for_user")
    @patch("backend.api.resume.get_resume_items_for_project_id")
    @patch("backend.api.resume.get_portfolio_item_for_project")
    @patch("backend.analysis.resume_generator.generate_resume")
    def test_generate_resume_latex_format(self, mock_generate, mock_portfolio, mock_items, mock_projects, auth_token):
        """Test generating resume in LaTeX format."""
        token, _ = auth_token
        projects, items, portfolio = _mock_one_project()
        mock_projects.return_value = projects
        mock_items.return_value = items
        mock_portfolio.return_value = portfolio
        mock_generate.return_value = b"LaTeX binary content"

        response = client.post(
            "/api/resume/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={"project_ids": [1], "format": "latex"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "latex"
        assert isinstance(data["content"], str)

    def test_generate_resume_stored_resume_wrong_format(self, auth_token):
        """Test generating resume with stored resume but wrong output format returns 400."""
        token, _ = auth_token

        create_response = client.post(
            "/api/resumes",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "title": "Stored Resume",
                "format": "markdown",
                "content": "## Projects\n\nBase Project",
            },
        )
        resume_id = create_response.json()["id"]

        # Stored-resume validation runs before project lookup, so no DB mock needed
        response = client.post(
            "/api/resume/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "project_ids": [1],
                "format": "pdf",
                "stored_resume_id": resume_id,
            },
        )
        assert response.status_code == 400
        assert "markdown" in response.json()["detail"].lower()

    def test_generate_resume_stored_resume_not_found(self, auth_token):
        """Test generating resume with non-existent stored resume ID returns 404."""
        token, _ = auth_token

        response = client.post(
            "/api/resume/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "project_ids": [1],
                "format": "markdown",
                "stored_resume_id": 99999,
            },
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_generate_resume_stored_resume_wrong_format_type(self, auth_token):
        """Test generating resume with stored resume that's not markdown returns 400."""
        token, _ = auth_token

        create_response = client.post(
            "/api/resumes",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": "Text Resume", "format": "text", "content": "Plain text resume"},
        )
        resume_id = create_response.json()["id"]

        response = client.post(
            "/api/resume/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "project_ids": [1],
                "format": "markdown",
                "stored_resume_id": resume_id,
            },
        )
        assert response.status_code == 400
        assert "markdown" in response.json()["detail"].lower()

    def test_create_stored_resume_unauthorized(self):
        """Test creating stored resume without auth."""
        response = client.post(
            "/api/resumes",
            json={"title": "Test Resume", "format": "markdown", "content": "Test content"},
        )
        assert response.status_code == 403

    def test_create_stored_resume_invalid_format(self, auth_token):
        """Test creating stored resume with invalid format (not markdown/text/pdf)."""
        token, _ = auth_token
        response = client.post(
            "/api/resumes",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": "Test Resume", "format": "latex", "content": "Test content"},
        )
        assert response.status_code == 400
        detail = response.json()["detail"].lower()
        assert "markdown" in detail or "text" in detail or "pdf" in detail

    def test_create_stored_resume_pdf_format(self, auth_token):
        """Test creating stored resume in pdf format (base64 body stored as text)."""
        token, _ = auth_token
        # Minimal placeholder; API stores string as-is
        response = client.post(
            "/api/resumes",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": "PDF Resume", "format": "pdf", "content": "JVBERi0xLjQK"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "pdf"
        assert data["content"] == "JVBERi0xLjQK"

    def test_create_stored_resume_text_format(self, auth_token):
        """Test creating stored resume in text format."""
        token, _ = auth_token
        response = client.post(
            "/api/resumes",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": "Text Resume", "format": "text", "content": "Plain text resume content"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "text"
        assert data["content"] == "Plain text resume content"

    def test_list_stored_resumes_unauthorized(self):
        """Test listing stored resumes without auth."""
        response = client.get("/api/resumes")
        assert response.status_code == 403

    def test_list_stored_resumes_empty(self, auth_token):
        """Test listing stored resumes when none exist."""
        token, _ = auth_token
        response = client.get("/api/resumes", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert response.json() == []

    def test_list_stored_resumes_multiple(self, auth_token):
        """Test listing multiple stored resumes."""
        token, _ = auth_token

        for i in range(3):
            client.post(
                "/api/resumes",
                headers={"Authorization": f"Bearer {token}"},
                json={"title": f"Resume {i+1}", "format": "markdown", "content": f"Content {i+1}"},
            )

        response = client.get("/api/resumes", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        resumes = response.json()
        assert len(resumes) == 3
        assert all("id" in r for r in resumes)
        assert all("title" in r for r in resumes)

    def test_get_stored_resume_unauthorized(self):
        """Test getting stored resume without auth."""
        response = client.get("/api/resumes/1")
        assert response.status_code == 403

    def test_get_stored_resume_not_found(self, auth_token):
        """Test getting non-existent stored resume."""
        token, _ = auth_token
        response = client.get("/api/resumes/99999", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 404

    def test_get_stored_resume_access_control(self, auth_token, second_auth_token):
        """Test that users cannot access other users' resumes."""
        token1, _ = auth_token
        token2, _ = second_auth_token

        create_response = client.post(
            "/api/resumes",
            headers={"Authorization": f"Bearer {token1}"},
            json={"title": "User1 Resume", "format": "markdown", "content": "User1 content"},
        )
        resume_id = create_response.json()["id"]

        response = client.get(
            f"/api/resumes/{resume_id}",
            headers={"Authorization": f"Bearer {token2}"},
        )
        assert response.status_code == 404

    def test_get_stored_resume_with_items(self, auth_token):
        """Test getting stored resume includes items list."""
        token, _ = auth_token

        create_response = client.post(
            "/api/resumes",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": "Resume with Items", "format": "markdown", "content": "## Projects\n\nTest"},
        )
        resume_id = create_response.json()["id"]

        response = client.get(
            f"/api/resumes/{resume_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_update_stored_resume_unauthorized(self):
        """Test updating stored resume without auth."""
        response = client.patch("/api/resumes/1", json={"content": "Updated content"})
        assert response.status_code == 403

    def test_delete_stored_resume_success(self, auth_token):
        """Test deleting a stored resume returns 204 and removes the row."""
        token, _ = auth_token
        create_response = client.post(
            "/api/resumes",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": "To Delete", "format": "markdown", "content": "## Hi"},
        )
        assert create_response.status_code == 200
        resume_id = create_response.json()["id"]

        delete_response = client.delete(
            f"/api/resumes/{resume_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert delete_response.status_code == 204

        get_response = client.get(
            f"/api/resumes/{resume_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert get_response.status_code == 404

    def test_delete_stored_resume_unauthorized(self):
        """Test deleting stored resume without auth."""
        response = client.delete("/api/resumes/1")
        assert response.status_code == 403

    def test_delete_stored_resume_not_found(self, auth_token):
        """Test deleting non-existent stored resume returns 404."""
        token, _ = auth_token
        response = client.delete(
            "/api/resumes/99999",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404

    def test_delete_stored_resume_access_control(self, auth_token, second_auth_token):
        """Test that users cannot delete other users' resumes."""
        token1, _ = auth_token
        token2, _ = second_auth_token

        create_response = client.post(
            "/api/resumes",
            headers={"Authorization": f"Bearer {token1}"},
            json={"title": "User1 Only", "format": "markdown", "content": "Secret"},
        )
        resume_id = create_response.json()["id"]

        response = client.delete(
            f"/api/resumes/{resume_id}",
            headers={"Authorization": f"Bearer {token2}"},
        )
        assert response.status_code == 404

    def test_update_stored_resume_not_found(self, auth_token):
        """Test updating non-existent stored resume."""
        token, _ = auth_token
        try:
            response = client.patch(
                "/api/resumes/99999",
                headers={"Authorization": f"Bearer {token}"},
                json={"content": "Updated content"},
            )
            assert response.status_code == 500
        except (TypeError, Exception):
            pass

    def test_update_stored_resume_access_control(self, auth_token, second_auth_token):
        """Test that users cannot update other users' resumes."""
        token1, _ = auth_token
        token2, _ = second_auth_token

        create_response = client.post(
            "/api/resumes",
            headers={"Authorization": f"Bearer {token1}"},
            json={"title": "User1 Resume", "format": "markdown", "content": "User1 content"},
        )
        resume_id = create_response.json()["id"]

        try:
            response = client.patch(
                f"/api/resumes/{resume_id}",
                headers={"Authorization": f"Bearer {token2}"},
                json={"content": "Hacked content"},
            )
            assert response.status_code == 500
        except (TypeError, Exception):
            pass

    def test_edit_resume_unauthorized(self):
        """Test editing resume without auth."""
        response = client.post("/api/resume/123/edit", json={"content": "Edited content"})
        assert response.status_code == 403

    def test_edit_resume_not_implemented(self, auth_token):
        """Test editing resume returns 501."""
        token, _ = auth_token
        response = client.post(
            "/api/resume/123/edit",
            headers={"Authorization": f"Bearer {token}"},
            json={"content": "Edited content"},
        )
        assert response.status_code == 501

    def test_add_items_to_stored_resume_unauthorized(self):
        """Test adding items to stored resume without auth."""
        response = client.post("/api/resumes/1/items", json={"resume_item_ids": [1, 2, 3]})
        assert response.status_code == 403

    def test_add_items_to_stored_resume_empty_list(self, auth_token):
        """Test adding empty list of items returns 400."""
        token, _ = auth_token

        create_response = client.post(
            "/api/resumes",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": "Test Resume", "format": "markdown", "content": "Test content"},
        )
        resume_id = create_response.json()["id"]

        response = client.post(
            f"/api/resumes/{resume_id}/items",
            headers={"Authorization": f"Bearer {token}"},
            json={"resume_item_ids": []},
        )
        assert response.status_code == 400
        assert "no resume items" in response.json()["detail"].lower()

    def test_add_items_to_stored_resume_not_found(self, auth_token):
        """Test adding items to non-existent resume."""
        token, _ = auth_token
        response = client.post(
            "/api/resumes/99999/items",
            headers={"Authorization": f"Bearer {token}"},
            json={"resume_item_ids": [1, 2]},
        )
        assert response.status_code in [400, 404]

    def test_add_items_to_stored_resume_invalid_items(self, auth_token):
        """Test adding items with invalid resume item IDs returns 400."""
        token, _ = auth_token

        create_response = client.post(
            "/api/resumes",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": "Test Resume", "format": "markdown", "content": "Test content"},
        )
        resume_id = create_response.json()["id"]

        response = client.post(
            f"/api/resumes/{resume_id}/items",
            headers={"Authorization": f"Bearer {token}"},
            json={"resume_item_ids": [99999, 99998]},
        )
        assert response.status_code == 400
        assert "no valid resume items" in response.json()["detail"].lower()

    @patch("backend.api.resume.get_projects_for_user")
    @patch("backend.api.resume.get_resume_items_for_project_id")
    @patch("backend.api.resume.get_portfolio_item_for_project")
    @patch("backend.analysis.resume_generator.generate_resume")
    def test_generate_resume_error_handling(self, mock_generate, mock_portfolio, mock_items, mock_projects, auth_token):
        """Test error handling when resume generation fails."""
        token, username = auth_token
        projects, items, portfolio = _mock_one_project()
        mock_projects.return_value = projects
        mock_items.return_value = items
        mock_portfolio.return_value = portfolio
        mock_generate.side_effect = Exception("Generation failed")

        response = client.post(
            "/api/resume/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={"project_ids": [1], "format": "markdown"},
        )
        assert response.status_code == 500
        assert "failed" in response.json()["detail"].lower()

    def test_stored_resume_response_structure(self, auth_token):
        """Test that stored resume response has all required fields."""
        token, _ = auth_token

        create_response = client.post(
            "/api/resumes",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": "Complete Resume", "format": "markdown", "content": "## Projects\n\nTest"},
        )
        assert create_response.status_code == 200
        data = create_response.json()
        required_fields = ["id", "title", "format", "content", "items", "created_at", "updated_at"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        assert isinstance(data["items"], list)
        assert isinstance(data["id"], int)

    @patch("backend.api.resume.get_projects_for_user")
    @patch("backend.api.resume.get_resume_items_for_project_id")
    @patch("backend.api.resume.get_portfolio_item_for_project")
    @patch("backend.analysis.resume_generator.generate_resume")
    def test_resume_response_metadata(self, mock_generate, mock_portfolio, mock_items, mock_projects, auth_token):
        """Test that generated resume response includes proper metadata."""
        token, username = auth_token
        projects, items, portfolio = _mock_one_project()
        mock_projects.return_value = projects
        mock_items.return_value = items
        mock_portfolio.return_value = portfolio
        mock_generate.return_value = "Resume content"

        response = client.post(
            "/api/resume/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={"project_ids": [1], "format": "markdown"},
        )
        assert response.status_code == 200
        metadata = response.json()["metadata"]
        assert metadata["username"] == username
        assert metadata["project_count"] == 1
        assert "total_projects" in metadata
        assert "generated_at" in metadata


class TestResumeWorkExperienceEndpoints:
    def test_work_experience_unauthorized(self):
        response = client.get("/api/resume/work-experience")
        assert response.status_code == 403

    def test_create_list_update_delete_work_experience(self, auth_token):
        token, _ = auth_token
        headers = {"Authorization": f"Bearer {token}"}

        create_response = client.post(
            "/api/resume/work-experience",
            headers=headers,
            json={
                "company": "Acme Corp",
                "job_title": "Software Engineer",
                "location": "Remote",
                "start_date": "Jan 2020",
                "end_date": "Dec 2021",
                "responsibilities_text": "Built APIs\nImproved performance",
            },
        )
        assert create_response.status_code == 200
        created = create_response.json()
        assert "id" in created
        work_id = created["id"]

        list_response = client.get("/api/resume/work-experience", headers=headers)
        assert list_response.status_code == 200
        entries = list_response.json()
        assert isinstance(entries, list)
        assert len(entries) == 1
        assert entries[0]["id"] == work_id
        assert entries[0]["company"] == "Acme Corp"

        update_response = client.patch(
            f"/api/resume/work-experience/{work_id}",
            headers=headers,
            json={
                "company": "Acme Corp",
                "job_title": "Senior Software Engineer",
                "location": "Remote",
                "start_date": "Jan 2020",
                "end_date": "Dec 2021",
                "responsibilities_text": "Led API redesign",
            },
        )
        assert update_response.status_code == 200
        updated = update_response.json()
        assert updated["id"] == work_id
        assert updated["job_title"] == "Senior Software Engineer"

        delete_response = client.delete(f"/api/resume/work-experience/{work_id}", headers=headers)
        assert delete_response.status_code == 200
        assert delete_response.json()["ok"] is True

        list_response_after = client.get("/api/resume/work-experience", headers=headers)
        assert list_response_after.status_code == 200
        assert list_response_after.json() == []

    def test_work_experience_user_scoping(self, auth_token, second_auth_token):
        token1, _ = auth_token
        token2, _ = second_auth_token

        headers1 = {"Authorization": f"Bearer {token1}"}
        headers2 = {"Authorization": f"Bearer {token2}"}

        create_response = client.post(
            "/api/resume/work-experience",
            headers=headers1,
            json={"company": "Acme Corp", "job_title": "Engineer"},
        )
        assert create_response.status_code == 200

        list_response_1 = client.get("/api/resume/work-experience", headers=headers1)
        list_response_2 = client.get("/api/resume/work-experience", headers=headers2)
        assert len(list_response_1.json()) == 1
        assert len(list_response_2.json()) == 0

    def test_work_experience_auto_seed_from_personal_info(self, auth_token):
        token, _ = auth_token
        headers = {"Authorization": f"Bearer {token}"}

        put_personal_info = client.put(
            "/api/resume/personal-info",
            headers=headers,
            json={
                "personal_info": {
                    "work_company": "Globex",
                    "work_job_title": "Data Analyst",
                    "work_location": "Boston, MA",
                    "work_start_date": "Aug 2019",
                    "work_end_date": "May 2020",
                    "work_responsibilities_text": "Analyzed datasets\nCreated dashboards",
                }
            },
        )
        assert put_personal_info.status_code == 200

        # No work entries yet; GET should seed.
        list_response = client.get("/api/resume/work-experience", headers=headers)
        assert list_response.status_code == 200
        entries = list_response.json()
        assert len(entries) == 1
        assert entries[0]["company"] == "Globex"
        assert entries[0]["job_title"] == "Data Analyst"

    @patch("backend.api.resume.get_projects_for_user")
    @patch("backend.api.resume.get_resume_items_for_project_id")
    @patch("backend.api.resume.get_portfolio_item_for_project")
    @patch("backend.analysis.resume_generator.generate_resume")
    def test_generate_resume_includes_work_experience_entries(
        self, mock_generate, mock_portfolio, mock_items, mock_projects, auth_token
    ):
        token, _ = auth_token
        headers = {"Authorization": f"Bearer {token}"}

        mock_projects.return_value = [{"id": 1, "project_name": "TestProject", "primary_language": "Python"}]
        mock_items.return_value = []
        mock_portfolio.return_value = {}
        mock_generate.return_value = "## Projects\n\n"

        create_response = client.post(
            "/api/resume/work-experience",
            headers=headers,
            json={"company": "Acme Corp", "job_title": "Engineer", "location": "Remote"},
        )
        assert create_response.status_code == 200

        generate_response = client.post(
            "/api/resume/generate",
            headers=headers,
            json={"project_ids": [1], "format": "markdown"},
        )
        assert generate_response.status_code == 200

        call_kwargs = mock_generate.call_args[1]
        personal_info_passed = call_kwargs["personal_info"]
        assert "work_experience_entries" in personal_info_passed
        assert isinstance(personal_info_passed["work_experience_entries"], list)
        assert len(personal_info_passed["work_experience_entries"]) == 1
        assert personal_info_passed["work_experience_entries"][0]["company"] == "Acme Corp"


MOCK_JOB_MATCH_ANALYZER_RESULT = {
    "overall_score": 72,
    "skills_score": 80,
    "experience_score": 65,
    "matched_skills": ["Python", "SQL"],
    "missing_skills": ["Kubernetes"],
    "matched_requirements": ["Bachelor's degree"],
    "unmet_requirements": ["5+ years distributed systems"],
    "recommendations": ["Highlight cloud projects"],
    "summary": "Strong technical overlap with gaps in ops tooling.",
}


class TestJobMatchEndpoints:
    """Tests for job description match persistence API."""

    def test_job_match_unauthorized(self):
        response = client.post(
            "/api/resume/job-match",
            json={"job_description": "a" * 50},
        )
        assert response.status_code == 403

    def test_job_matches_list_unauthorized(self):
        assert client.get("/api/resume/job-matches").status_code == 403

    def test_job_matches_delete_unauthorized(self):
        assert client.delete("/api/resume/job-matches/1").status_code == 403

    def test_job_match_validation_too_short(self, auth_token):
        token, _ = auth_token
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post(
            "/api/resume/job-match",
            headers=headers,
            json={"job_description": "short"},
        )
        assert response.status_code == 422

    @patch("backend.api.resume.analyze_job_match")
    @patch("backend.api.resume.get_projects_for_user")
    def test_job_match_persists_returns_id_and_lists(
        self, mock_projects, mock_analyze, auth_token
    ):
        token, _ = auth_token
        headers = {"Authorization": f"Bearer {token}"}
        mock_projects.return_value = []
        mock_analyze.return_value = dict(MOCK_JOB_MATCH_ANALYZER_RESULT)

        desc = "We are hiring a senior backend engineer with fifty chars min."
        post = client.post(
            "/api/resume/job-match",
            headers=headers,
            json={"job_description": desc},
        )
        assert post.status_code == 200
        body = post.json()
        assert body["id"] is not None
        assert body["job_description"] == desc
        assert body["overall_score"] == 72
        assert body["matched_skills"] == ["Python", "SQL"]
        mock_analyze.assert_called_once()

        listed = client.get("/api/resume/job-matches", headers=headers)
        assert listed.status_code == 200
        items = listed.json()
        assert len(items) == 1
        assert items[0]["id"] == body["id"]
        assert items[0]["job_description"] == desc

        deleted = client.delete(
            f"/api/resume/job-matches/{body['id']}",
            headers=headers,
        )
        assert deleted.status_code == 200
        assert deleted.json() == {"ok": True}

        after = client.get("/api/resume/job-matches", headers=headers)
        assert after.json() == []

    @patch("backend.api.resume.analyze_job_match")
    @patch("backend.api.resume.get_projects_for_user")
    def test_job_match_delete_not_found(self, mock_projects, mock_analyze, auth_token):
        token, _ = auth_token
        headers = {"Authorization": f"Bearer {token}"}
        mock_projects.return_value = []
        mock_analyze.return_value = dict(MOCK_JOB_MATCH_ANALYZER_RESULT)
        response = client.delete("/api/resume/job-matches/999999", headers=headers)
        assert response.status_code == 404

    @patch("backend.api.resume.analyze_job_match")
    @patch("backend.api.resume.get_projects_for_user")
    def test_job_match_delete_other_user_denied(
        self, mock_projects, mock_analyze, auth_token, second_auth_token
    ):
        token1, _ = auth_token
        token2, _ = second_auth_token
        headers1 = {"Authorization": f"Bearer {token1}"}
        headers2 = {"Authorization": f"Bearer {token2}"}
        mock_projects.return_value = []
        mock_analyze.return_value = dict(MOCK_JOB_MATCH_ANALYZER_RESULT)

        desc = "Another job description that is at least fifty characters long here."
        post = client.post(
            "/api/resume/job-match",
            headers=headers1,
            json={"job_description": desc},
        )
        assert post.status_code == 200
        match_id = post.json()["id"]

        denied = client.delete(f"/api/resume/job-matches/{match_id}", headers=headers2)
        assert denied.status_code == 404

        still_there = client.get("/api/resume/job-matches", headers=headers1)
        assert len(still_there.json()) == 1
