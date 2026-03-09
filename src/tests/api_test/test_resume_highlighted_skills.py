"""
Tests for the highlighted_skills field in the resume API endpoint.

Validates that the POST /api/resume/generate endpoint correctly accepts and
forwards highlighted_skills to the resume generator.
"""

import sys
import uuid
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

# Add src directory to path
src_dir = Path(__file__).resolve().parent.parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

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
    db_path = tmp_path / "test_resume_highlighted.db"
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


class TestResumeHighlightedSkills:
    """Tests for the highlighted_skills field in ResumeRequest."""

    @patch("backend.api.resume.get_analysis_by_uuid")
    @patch("backend.analysis.resume_generator.generate_resume")
    def test_highlighted_skills_passed_to_generator(
        self, mock_generate_resume, mock_get_analysis_by_uuid, auth_token
    ):
        """Test that highlighted_skills from the request body are forwarded to the generator."""
        token, username = auth_token

        mock_get_analysis_by_uuid.return_value = {"projects": [{"project_name": "Test"}], "total_projects": 1}
        mock_generate_resume.return_value = "Resume with curated skills"

        curated_skills = ["Python", "React", "FastAPI"]

        response = client.post(
            "/api/resume/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "portfolio_ids": ["portfolio-1"],
                "format": "markdown",
                "highlighted_skills": curated_skills,
            },
        )

        assert response.status_code == 200
        # Verify the generator was called with highlighted_skills
        mock_generate_resume.assert_called_once()
        call_kwargs = mock_generate_resume.call_args[1]
        assert call_kwargs["highlighted_skills"] == curated_skills

    @patch("backend.api.resume.get_analysis_by_uuid")
    @patch("backend.analysis.resume_generator.generate_resume")
    def test_highlighted_skills_none_when_not_provided(
        self, mock_generate_resume, mock_get_analysis_by_uuid, auth_token
    ):
        """Test that highlighted_skills defaults to None when not in the request."""
        token, username = auth_token

        mock_get_analysis_by_uuid.return_value = {"projects": [{"project_name": "Test"}], "total_projects": 1}
        mock_generate_resume.return_value = "Resume without curated skills"

        response = client.post(
            "/api/resume/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "portfolio_ids": ["portfolio-1"],
                "format": "markdown",
            },
        )

        assert response.status_code == 200
        call_kwargs = mock_generate_resume.call_args[1]
        assert call_kwargs["highlighted_skills"] is None

    @patch("backend.api.resume.get_analysis_by_uuid")
    @patch("backend.analysis.resume_generator.generate_resume")
    def test_highlighted_skills_empty_list(
        self, mock_generate_resume, mock_get_analysis_by_uuid, auth_token
    ):
        """Test that empty list is passed through correctly."""
        token, username = auth_token

        mock_get_analysis_by_uuid.return_value = {"projects": [{"project_name": "Test"}], "total_projects": 1}
        mock_generate_resume.return_value = "Resume content"

        response = client.post(
            "/api/resume/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "portfolio_ids": ["portfolio-1"],
                "format": "markdown",
                "highlighted_skills": [],
            },
        )

        assert response.status_code == 200
        call_kwargs = mock_generate_resume.call_args[1]
        assert call_kwargs["highlighted_skills"] == []

    @patch("backend.api.resume.get_analysis_by_uuid")
    @patch("backend.analysis.resume_generator.generate_resume")
    def test_highlighted_skills_with_personal_info_and_options(
        self, mock_generate_resume, mock_get_analysis_by_uuid, auth_token
    ):
        """Test highlighted_skills alongside other request fields."""
        token, username = auth_token

        mock_get_analysis_by_uuid.return_value = {"projects": [{"project_name": "Test"}], "total_projects": 1}
        mock_generate_resume.return_value = "Full resume"

        personal = {"name": "Jane Doe", "email": "jane@example.com"}
        skills = ["Kubernetes", "Docker", "Terraform"]

        response = client.post(
            "/api/resume/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "portfolio_ids": ["portfolio-1"],
                "format": "markdown",
                "include_skills": True,
                "include_projects": True,
                "max_projects": 3,
                "personal_info": personal,
                "highlighted_skills": skills,
            },
        )

        assert response.status_code == 200
        call_kwargs = mock_generate_resume.call_args[1]
        assert call_kwargs["highlighted_skills"] == skills
        assert call_kwargs["personal_info"] == personal
        assert call_kwargs["include_skills"] is True
        assert call_kwargs["max_projects"] == 3

    def test_resume_request_model_accepts_highlighted_skills(self):
        """Test that the ResumeRequest Pydantic model accepts highlighted_skills."""
        from backend.api.resume import ResumeRequest

        req = ResumeRequest(
            portfolio_ids=["portfolio-1", "portfolio-2"],
            format="markdown",
            highlighted_skills=["Python", "React"],
        )
        assert req.highlighted_skills == ["Python", "React"]

    def test_resume_request_model_highlighted_skills_optional(self):
        """Test that highlighted_skills defaults to None."""
        from backend.api.resume import ResumeRequest

        req = ResumeRequest(portfolio_ids=["portfolio-1"])
        assert req.highlighted_skills is None

    def test_resume_request_model_highlighted_skills_empty(self):
        """Test that highlighted_skills can be an empty list."""
        from backend.api.resume import ResumeRequest

        req = ResumeRequest(portfolio_ids=["portfolio-1"], highlighted_skills=[])
        assert req.highlighted_skills == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
