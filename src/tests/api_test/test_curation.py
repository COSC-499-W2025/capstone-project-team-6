"""Unit tests for curation API endpoints (basic coverage)."""

import sys
from pathlib import Path
import uuid
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

src_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_dir))

from backend.api.auth import active_tokens
from backend.api_server import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_tokens():
    active_tokens.clear()
    yield
    active_tokens.clear()


@pytest.fixture
def auth_token():
    test_username = f"testuser_{uuid.uuid4().hex[:8]}"
    response = client.post(
        "/api/auth/signup",
        json={"username": test_username, "password": "password123"},
    )
    return response.json()["access_token"], test_username


class TestCurationEndpoints:
    @patch("backend.api.curation.save_showcase_projects")
    def test_post_curation_showcase_success(self, mock_save, auth_token):
        token, _ = auth_token
        mock_save.return_value = True
        response = client.post(
            "/api/curation/showcase",
            headers={"Authorization": f"Bearer {token}"},
            json={"project_ids": [1]},
        )
        assert response.status_code in (200, 201, 202)



    def test_get_curation_skills_unauthorized(self):
        response = client.get("/api/curation/skills")
        assert response.status_code in (401, 403)

    @patch("backend.api.curation.get_available_skills_alphabetical")
    def test_get_curation_skills_success(self, mock_get_skills, auth_token):
        token, _ = auth_token
        mock_get_skills.return_value = ["Python", "JavaScript"]
        response = client.get(
            "/api/curation/skills",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_post_curation_skills_unauthorized(self):
        response = client.post("/api/curation/skills", json={"skills": ["Python"]})
        assert response.status_code in (401, 403)

    @patch("backend.api.curation.save_highlighted_skills")
    def test_post_curation_skills_success(self, mock_save, auth_token):
        token, _ = auth_token
        mock_save.return_value = True
        response = client.post(
            "/api/curation/skills",
            headers={"Authorization": f"Bearer {token}"},
            json={"skills": ["Python"]},
        )
        assert response.status_code in (200, 201, 202)

    def test_post_curation_attributes_unauthorized(self):
        response = client.post("/api/curation/attributes", json={"attributes": ["language"]})
        assert response.status_code in (401, 403)

    @patch("backend.api.curation.save_comparison_attributes")
    def test_post_curation_attributes_success(self, mock_save, auth_token):
        token, _ = auth_token
        mock_save.return_value = True
        response = client.post(
            "/api/curation/attributes",
            headers={"Authorization": f"Bearer {token}"},
            json={"attributes": ["language", "frameworks"]},
        )
        assert response.status_code in (200, 201, 202)

    def test_post_curation_chronology_unauthorized(self):
        response = client.post("/api/curation/chronology", json={"project_id": 1})
        assert response.status_code in (401, 403)

    @patch("backend.api.curation.save_chronology_correction")
    def test_post_curation_chronology_success(self, mock_save, auth_token):
        token, _ = auth_token
        mock_save.return_value = True
        response = client.post(
            "/api/curation/chronology",
            headers={"Authorization": f"Bearer {token}"},
            json={"project_id": 1, "last_commit_date": "2024-01-01"},
        )
        assert response.status_code in (200, 201, 202)

    def test_post_curation_order_unauthorized(self):
        response = client.post("/api/curation/order", json={"project_ids": [1]})
        assert response.status_code in (401, 403)

    @patch("backend.api.curation.save_project_order")
    def test_post_curation_order_success(self, mock_save, auth_token):
        token, _ = auth_token
        mock_save.return_value = True
        response = client.post(
            "/api/curation/order",
            headers={"Authorization": f"Bearer {token}"},
            json={"project_ids": [1]},
        )
        assert response.status_code in (200, 201, 202)

    def test_get_curation_attributes_unauthorized(self):
        response = client.get("/api/curation/attributes")
        assert response.status_code in (401, 403)

    @patch("backend.api.curation.get_user_curation_settings")
    def test_get_curation_settings_success(self, mock_settings, auth_token):
        token, username = auth_token
        from unittest.mock import MagicMock
        mock_obj = MagicMock()
        mock_obj.user_id = username
        mock_obj.comparison_attributes = []
        mock_obj.showcase_project_ids = []
        mock_obj.custom_project_order = []
        mock_obj.highlighted_skills = []
        mock_settings.return_value = mock_obj
        response = client.get(
            "/api/curation/settings",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "comparison_attributes" in data
        assert "showcase_project_ids" in data

    def test_get_curation_settings_unauthorized(self):
        response = client.get("/api/curation/settings")
        assert response.status_code in (401, 403)
