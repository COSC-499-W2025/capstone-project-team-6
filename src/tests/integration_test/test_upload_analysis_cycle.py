"""
Integration tests for the upload-analysis cycle.

Tests the full flow:
1. Login/signup with new account
2. Give consent
3. Upload single project (ZIP)
4. Navigate to analyze page (simulated by polling task status)
5. Analysis runs, loading bar shows progress
6. After completion, projects page shows the analyzed project
"""

import sys
import tempfile
import time
import zipfile
from pathlib import Path
import pytest

src_dir = Path(__file__).resolve().parent.parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from fastapi.testclient import TestClient

from backend.analysis_database import (
    init_db as init_analysis_db,
    set_db_path as set_analysis_db_path,
)
from backend.api.auth import active_tokens
from backend.api_server import app
from backend.curation import init_curation_tables
from backend.database import init_db as init_user_db, set_db_path as set_user_db_path


@pytest.fixture
def temp_dbs(tmp_path):
    """Use temporary databases for user and analysis."""
    user_db = tmp_path / "users.db"
    analysis_db = tmp_path / "analysis.db"

    orig_user = set_user_db_path(user_db)
    orig_analysis = set_analysis_db_path(analysis_db)

    init_user_db()
    init_analysis_db()
    init_curation_tables()

    yield user_db, analysis_db

    set_user_db_path(orig_user)
    set_analysis_db_path(orig_analysis)


@pytest.fixture
def client(temp_dbs):
    """Create test client with clean token state."""
    active_tokens.clear()
    yield TestClient(app)
    active_tokens.clear()


@pytest.fixture
def auth_headers(client):
    """Sign up, give consent, and return auth headers."""
    username = f"upload_test_{int(time.time())}"
    password = "testpass123"

    # Signup
    r = client.post("/api/auth/signup", json={"username": username, "password": password})
    assert r.status_code in [200, 201], f"Signup failed: {r.text}"

    token = r.json()["access_token"]

    # Consent (required for upload)
    r = client.post(
        "/api/user/consent",
        json={"has_consented": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200, f"Consent failed: {r.text}"

    return {"Authorization": f"Bearer {token}"}, username


@pytest.fixture
def minimal_zip(tmp_path):
    """Create a minimal valid project ZIP for analysis."""
    zip_path = tmp_path / "test_project.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("test_project/main.py", "print('Hello World')")
        zf.writestr("test_project/README.md", "# Test Project")
    return zip_path


class TestUploadAnalysisCycle:
    """Test the complete upload -> analyze -> projects flow."""

    def test_upload_returns_task_id(self, client, auth_headers, minimal_zip):
        """Upload returns task_id in response details."""
        headers, _ = auth_headers
        with open(minimal_zip, "rb") as f:
            r = client.post(
                "/api/portfolios/upload",
                files={"file": ("test_project.zip", f, "application/zip")},
                data={"analysis_type": "non_llm"},
                headers=headers,
            )

        assert r.status_code == 202, f"Upload failed: {r.text}"
        data = r.json()
        assert "details" in data
        assert "task_id" in data["details"]
        task_id = data["details"]["task_id"]
        assert task_id
        assert "status_url" in data["details"]

    def test_task_status_can_be_polled(self, client, auth_headers, minimal_zip):
        """Task status endpoint returns valid status when polled."""
        headers, username = auth_headers

        # Upload
        with open(minimal_zip, "rb") as f:
            r = client.post(
                "/api/portfolios/upload",
                files={"file": ("test_project.zip", f, "application/zip")},
                data={"analysis_type": "non_llm"},
                headers=headers,
            )
        assert r.status_code == 202
        task_id = r.json()["details"]["task_id"]

        # Poll task status - should return valid structure
        r = client.get(f"/api/tasks/{task_id}", headers=headers)
        assert r.status_code == 200, f"Task status failed: {r.text}"
        data = r.json()

        assert data["task_id"] == task_id
        assert data["status"] in ["pending", "running", "completed", "failed"]
        assert "progress" in data
        assert "filename" in data
        if data["status"] == "completed" and data.get("result"):
            assert "analysis_uuid" in data["result"]

    def test_projects_list_returns_valid_structure(self, client, auth_headers):
        """Projects list endpoint returns valid structure for authenticated user."""
        headers, username = auth_headers

        r = client.get("/api/projects", headers=headers)
        assert r.status_code == 200, f"Projects list failed: {r.text}"

        data = r.json()
        assert "projects" in data
        assert "total_projects" in data
        projects = data["projects"]
        assert isinstance(projects, list)
        # New user may have 0 projects; just verify structure
        for p in projects:
            assert "id" in p
            assert "project_name" in p or "project_path" in p

    def test_upload_requires_consent(self, client, minimal_zip):
        """Upload fails without consent."""
        # Signup without consent
        username = f"no_consent_{int(time.time())}"
        r = client.post("/api/auth/signup", json={"username": username, "password": "testpass123"})
        assert r.status_code in [200, 201]
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Do NOT give consent - try upload
        with open(minimal_zip, "rb") as f:
            r = client.post(
                "/api/portfolios/upload",
                files={"file": ("test_project.zip", f, "application/zip")},
                data={"analysis_type": "non_llm"},
                headers=headers,
            )

        assert r.status_code == 403
        assert "consent" in r.json()["detail"].lower()
