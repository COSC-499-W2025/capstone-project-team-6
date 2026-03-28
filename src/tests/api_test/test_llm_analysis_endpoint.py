"""
Tests for GET /api/projects/{project_id}/llm-analysis endpoint.

Covers:
- Returns llm_summary when analysis exists with one
- Returns null llm_summary when analysis exists but LLM hasn't run
- Returns 404 for non-existent project
- Returns 404 when project belongs to a different user
- Response shape is always correct
"""

from __future__ import annotations

import sys
import uuid
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

SRC_DIR = Path(__file__).resolve().parents[2]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from backend import analysis_database as adb
from backend import database as udb
from backend.api.auth import active_tokens
from backend.api_server import app

client = TestClient(app)

SAMPLE_LLM_SUMMARY = (
    "## General Validation\nThe project follows clean architecture principles.\n\n"
    "### Security\nNo critical vulnerabilities found.\n"
)

SAMPLE_PAYLOAD = {
    "analysis_metadata": {
        "zip_file": "project.zip",
        "analysis_timestamp": "2025-01-01T00:00:00",
        "total_projects": 1,
    },
    "projects": [
        {
            "project_name": "test_project",
            "project_path": "",
            "primary_language": "python",
            "languages": {"python": 5},
            "total_files": 5,
            "total_size": 512,
            "code_files": 4,
            "test_files": 1,
            "doc_files": 0,
            "config_files": 0,
            "frameworks": [],
            "dependencies": {},
            "has_tests": True,
            "has_readme": False,
            "has_ci_cd": False,
            "has_docker": False,
            "is_git_repo": False,
        }
    ],
    "summary": {
        "total_files": 5,
        "total_size_bytes": 512,
        "total_size_mb": 0.0,
        "languages_used": ["python"],
        "frameworks_used": [],
    },
}


@pytest.fixture(autouse=True)
def clear_tokens():
    active_tokens.clear()
    yield
    active_tokens.clear()


@pytest.fixture
def isolated_db(tmp_path):
    """Isolated DB + restore original paths after each test."""
    db_path = tmp_path / "api_test.db"
    prev_adb = adb.set_db_path(db_path)
    prev_udb = udb.set_db_path(db_path)
    udb.init_db()
    adb.init_db()
    yield db_path
    adb.set_db_path(prev_adb)
    udb.set_db_path(prev_udb)


@pytest.fixture
def auth_token(isolated_db):
    username = f"user_{uuid.uuid4().hex[:8]}"
    resp = client.post(
        "/api/auth/signup",
        json={"username": username, "password": "password123"},
    )
    assert resp.status_code in (200, 201), resp.text
    return resp.json()["access_token"], username


@pytest.fixture
def project_with_llm(isolated_db, auth_token):
    """Create a real analysis+project row with LLM summary in the DB."""
    _, username = auth_token
    analysis_id = adb.record_analysis("non_llm", SAMPLE_PAYLOAD, username=username, analysis_uuid="test-uuid-llm")
    adb.update_llm_summary("test-uuid-llm", SAMPLE_LLM_SUMMARY, username)
    # Get the project integer ID
    projects = adb.get_projects_for_analysis(analysis_id)
    return projects[0]["id"]


@pytest.fixture
def project_without_llm(isolated_db, auth_token):
    """Create a real analysis+project row WITHOUT an LLM summary."""
    _, username = auth_token
    analysis_id = adb.record_analysis("non_llm", SAMPLE_PAYLOAD, username=username, analysis_uuid="test-uuid-no-llm")
    projects = adb.get_projects_for_analysis(analysis_id)
    return projects[0]["id"]


class TestLlmAnalysisEndpoint:

    def test_returns_llm_summary_when_present(self, auth_token, project_with_llm):
        token, _ = auth_token
        resp = client.get(
            f"/api/projects/{project_with_llm}/llm-analysis",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["project_id"] == project_with_llm
        assert data["llm_summary"] == SAMPLE_LLM_SUMMARY
        assert data.get("llm_error") is None

    def test_returns_llm_error_when_stored(self, auth_token, isolated_db):
        """When LLM failed, llm_error is persisted and returned alongside null summary."""
        token, username = auth_token
        analysis_id = adb.record_analysis(
            "llm", SAMPLE_PAYLOAD, username=username, analysis_uuid="test-uuid-err"
        )
        msg = "This project is too large for LLM analysis. Blume employees are working on a fix."
        adb.update_llm_error("test-uuid-err", msg, username)
        projects = adb.get_projects_for_analysis(analysis_id)
        project_id = projects[0]["id"]

        resp = client.get(
            f"/api/projects/{project_id}/llm-analysis",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["llm_summary"] is None
        assert data["llm_error"] == msg

    def test_returns_null_summary_when_llm_not_run(self, auth_token, project_without_llm):
        token, _ = auth_token
        resp = client.get(
            f"/api/projects/{project_without_llm}/llm-analysis",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["project_id"] == project_without_llm
        assert data["llm_summary"] is None
        assert data.get("llm_error") is None

    def test_returns_404_for_nonexistent_project(self, auth_token, isolated_db):
        token, _ = auth_token
        resp = client.get(
            "/api/projects/99999/llm-analysis",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404

    def test_returns_404_for_other_users_project(self, isolated_db):
        """User B cannot access User A's project."""
        # Create user A with a project
        user_a = f"user_a_{uuid.uuid4().hex[:6]}"
        udb.create_user(user_a, "password123")
        analysis_id = adb.record_analysis("non_llm", SAMPLE_PAYLOAD, username=user_a, analysis_uuid="owner-a-uuid")
        projects = adb.get_projects_for_analysis(analysis_id)
        project_id = projects[0]["id"]

        # Create user B and authenticate
        user_b = f"user_b_{uuid.uuid4().hex[:6]}"
        signup = client.post(
            "/api/auth/signup",
            json={"username": user_b, "password": "password123"},
        )
        token_b = signup.json()["access_token"]

        resp = client.get(
            f"/api/projects/{project_id}/llm-analysis",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert resp.status_code == 404

    def test_requires_authentication(self, isolated_db):
        resp = client.get("/api/projects/1/llm-analysis")
        assert resp.status_code in (401, 403)

    def test_response_always_has_project_id_and_llm_summary_keys(self, auth_token, project_with_llm):
        """Response shape must always include both keys."""
        token, _ = auth_token
        resp = client.get(
            f"/api/projects/{project_with_llm}/llm-analysis",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "project_id" in data
        assert "llm_summary" in data
        assert "llm_error" in data
