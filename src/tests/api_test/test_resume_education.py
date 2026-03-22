"""Unit tests for resume education CRUD endpoints."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

# Add src directory to path
src_dir = Path(__file__).resolve().parent.parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

import uuid

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


@pytest.fixture(autouse=False)
def setup_temp_db(tmp_path):
    db_path = tmp_path / "resume_education.db"
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
def auth_token(setup_temp_db):
    """Create authenticated user and return token."""
    test_username = f"testuser_{uuid.uuid4().hex[:8]}"
    response = client.post(
        "/api/auth/signup",
        json={"username": test_username, "password": "password123"},
    )
    return response.json()["access_token"], test_username


@pytest.fixture
def second_auth_token(setup_temp_db):
    """Create a second authenticated user and return token."""
    test_username = f"testuser2_{uuid.uuid4().hex[:8]}"
    response = client.post(
        "/api/auth/signup",
        json={"username": test_username, "password": "password123"},
    )
    return response.json()["access_token"], test_username


@pytest.fixture
def auth_headers(auth_token):
    token, _ = auth_token
    return {"Authorization": f"Bearer {token}"}


class TestResumeEducationEndpoints:
    def test_education_unauthorized(self, setup_temp_db):
        response = client.get("/api/resume/education")
        assert response.status_code == 403

    def test_create_list_update_delete_education(self, auth_token):
        token, _ = auth_token
        headers = {"Authorization": f"Bearer {token}"}

        create_response = client.post(
            "/api/resume/education",
            headers=headers,
            json={
                "university": "MIT",
                "degree": "B.S. Computer Science",
                "location": "Cambridge, MA",
                "start_date": "Aug 2018",
                "end_date": "May 2022",
                "awards": "Dean's List",
                "education_text": "",
            },
        )
        assert create_response.status_code == 200
        created = create_response.json()
        assert "id" in created
        edu_id = created["id"]

        list_response = client.get("/api/resume/education", headers=headers)
        assert list_response.status_code == 200
        entries = list_response.json()
        assert isinstance(entries, list)
        assert len(entries) == 1
        assert entries[0]["id"] == edu_id
        assert entries[0]["university"] == "MIT"

        update_response = client.patch(
            f"/api/resume/education/{edu_id}",
            headers=headers,
            json={
                "university": "Stanford",
                "degree": "B.S. Computer Science",
                "location": "Stanford, CA",
                "start_date": "Aug 2018",
                "end_date": "May 2022",
                "awards": "Honor Roll",
            },
        )
        assert update_response.status_code == 200
        updated = update_response.json()
        assert updated["id"] == edu_id
        assert updated["university"] == "Stanford"
        assert updated["awards"] == "Honor Roll"

        delete_response = client.delete(f"/api/resume/education/{edu_id}", headers=headers)
        assert delete_response.status_code == 200
        assert delete_response.json()["ok"] is True

        list_response_after = client.get("/api/resume/education", headers=headers)
        assert list_response_after.status_code == 200
        assert list_response_after.json() == []

    def test_education_user_scoping(self, auth_token, second_auth_token):
        token1, _ = auth_token
        token2, _ = second_auth_token

        headers1 = {"Authorization": f"Bearer {token1}"}
        headers2 = {"Authorization": f"Bearer {token2}"}

        create_response = client.post(
            "/api/resume/education",
            headers=headers1,
            json={"university": "MIT", "degree": "BSc"},
        )
        assert create_response.status_code == 200

        list_response_1 = client.get("/api/resume/education", headers=headers1)
        list_response_2 = client.get("/api/resume/education", headers=headers2)

        assert list_response_1.status_code == 200
        assert list_response_2.status_code == 200
        assert len(list_response_1.json()) == 1
        assert len(list_response_2.json()) == 0

    def test_education_auto_seed_from_personal_info(self, auth_token):
        token, _ = auth_token
        headers = {"Authorization": f"Bearer {token}"}

        # Legacy fields are saved under personal_info.
        put_personal_info = client.put(
            "/api/resume/personal-info",
            headers=headers,
            json={
                "personal_info": {
                    "education_university": "Georgia Tech",
                    "education_degree": "M.S. Data Science",
                    "education_location": "Atlanta, GA",
                    "education_start_date": "Aug 2020",
                    "education_end_date": "May 2022",
                    "education_awards": "Scholarship A",
                }
            },
        )
        assert put_personal_info.status_code == 200

        # No education entries exist yet; GET should seed from personal_info.
        list_response = client.get("/api/resume/education", headers=headers)
        assert list_response.status_code == 200
        entries = list_response.json()
        assert len(entries) == 1
        assert entries[0]["university"] == "Georgia Tech"
        assert entries[0]["degree"] == "M.S. Data Science"

    @patch("backend.api.resume.get_projects_for_user")
    @patch("backend.api.resume.get_resume_items_for_project_id")
    @patch("backend.api.resume.get_portfolio_item_for_project")
    @patch("backend.analysis.resume_generator.generate_resume")
    def test_generate_resume_includes_education_entries(
        self, mock_generate, mock_portfolio, mock_items, mock_projects, auth_token
    ):
        token, _ = auth_token
        headers = {"Authorization": f"Bearer {token}"}

        # Mock project selection.
        mock_projects.return_value = [{"id": 1, "project_name": "TestProject", "primary_language": "Python"}]
        mock_items.return_value = []
        mock_portfolio.return_value = {}
        mock_generate.return_value = "## Projects\n\n"

        # Create a saved education entry.
        create_response = client.post(
            "/api/resume/education",
            headers=headers,
            json={"university": "MIT", "degree": "B.S. CS", "location": "Cambridge"},
        )
        assert create_response.status_code == 200

        # Generate resume (we don't care about output here; we care about the arguments).
        generate_response = client.post(
            "/api/resume/generate",
            headers=headers,
            json={"project_ids": [1], "format": "markdown"},
        )
        assert generate_response.status_code == 200

        call_kwargs = mock_generate.call_args[1]
        assert "personal_info" in call_kwargs
        personal_info_passed = call_kwargs["personal_info"]
        assert isinstance(personal_info_passed, dict)
        assert "education_entries" in personal_info_passed
        assert isinstance(personal_info_passed["education_entries"], list)
        assert len(personal_info_passed["education_entries"]) == 1
        assert personal_info_passed["education_entries"][0]["university"] == "MIT"

