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

import asyncio
import sys
import tempfile
import time
import zipfile
from pathlib import Path
import pytest

src_dir = Path(__file__).resolve().parent.parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

import httpx
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
def async_client(temp_dbs):
    """Async client - shares event loop with app so asyncio.create_task runs."""
    active_tokens.clear()
    transport = httpx.ASGITransport(app=app)
    yield httpx.AsyncClient(transport=transport, base_url="http://test")
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


@pytest.fixture
def multi_project_zip(tmp_path):
    """Create a ZIP containing multiple projects (for multi-project detection)."""
    zip_path = tmp_path / "multi_project.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        # Project A: Python with requirements.txt
        zf.writestr("project_a/main.py", "print('Project A')")
        zf.writestr("project_a/requirements.txt", "requests==1.0")
        zf.writestr("project_a/README.md", "# Project A")
        # Project B: Node with package.json
        zf.writestr("project_b/index.js", "console.log('Project B')")
        zf.writestr("project_b/package.json", '{"name": "project-b"}')
        zf.writestr("project_b/README.md", "# Project B")
    return zip_path


@pytest.fixture
def auth_headers_no_consent(client):
    """Sign up without consent and return auth headers."""
    username = f"no_consent_{int(time.time())}"
    password = "testpass123"
    r = client.post("/api/auth/signup", json={"username": username, "password": password})
    assert r.status_code in [200, 201], f"Signup failed: {r.text}"
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, username


class TestUploadAnalysisCycle:
    """Test the complete upload -> analyze -> projects flow."""

    def test_upload_returns_task_id(self, client, auth_headers, minimal_zip):
        """Upload returns task_id in response details."""
        headers, _ = auth_headers
        with open(minimal_zip, "rb") as f:
            r = client.post(
                "/api/portfolios/upload",
                files={"file": ("test_project.zip", f, "application/zip")},
                data={"analysis_type": "non_llm", "project_name": "Test Project"},
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
                data={"analysis_type": "non_llm", "project_name": "Test Project"},
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

    def test_upload_non_llm_without_consent_succeeds(self, client, auth_headers_no_consent, minimal_zip):
        """Non-LLM upload succeeds without consent."""
        headers, _ = auth_headers_no_consent
        with open(minimal_zip, "rb") as f:
            r = client.post(
                "/api/portfolios/upload",
                files={"file": ("test_project.zip", f, "application/zip")},
                data={"analysis_type": "non_llm", "project_name": "My Test Project"},
                headers=headers,
            )
        assert r.status_code == 202, f"Non-LLM upload without consent should succeed: {r.text}"
        assert "task_id" in r.json().get("details", {})

    def test_upload_llm_without_consent_fails(self, client, auth_headers_no_consent, minimal_zip):
        """LLM upload fails without consent."""
        headers, _ = auth_headers_no_consent
        with open(minimal_zip, "rb") as f:
            r = client.post(
                "/api/portfolios/upload",
                files={"file": ("test_project.zip", f, "application/zip")},
                data={"analysis_type": "llm", "project_name": "My Test Project"},
                headers=headers,
            )
        assert r.status_code == 403, f"LLM upload without consent should fail: {r.text}"
        assert "consent" in r.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_multi_project_zip_analyzed_correctly(
        self, client, async_client, auth_headers, multi_project_zip
    ):
        """Single ZIP with multiple projects is analyzed and all projects appear.

        Uses AsyncClient so asyncio.create_task in the upload handler runs on the same
        event loop; TestClient does not run background tasks.
        """
        headers, username = auth_headers

        with open(multi_project_zip, "rb") as f:
            r = await async_client.post(
                "/api/portfolios/upload",
                files={"file": ("multi_project.zip", f, "application/zip")},
                data={"analysis_type": "non_llm", "project_name": "Multi Portfolio"},
                headers=headers,
            )
        assert r.status_code == 202, f"Upload failed: {r.text}"
        task_id = r.json()["details"]["task_id"]

        # Poll until complete (AsyncClient shares event loop, so background task runs)
        max_wait = 120
        poll_interval = 1
        elapsed = 0
        while elapsed < max_wait:
            r = await async_client.get(f"/api/tasks/{task_id}", headers=headers)
            assert r.status_code == 200, f"Task status failed: {r.text}"
            data = r.json()
            if data["status"] == "completed":
                result = data.get("result", {})
                total = result.get("total_projects", 0)
                assert total >= 2, f"Expected at least 2 projects, got {total}"
                break
            if data["status"] == "failed":
                pytest.fail(f"Task failed: {data.get('error', 'Unknown error')}")
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
        else:
            pytest.fail("Task did not complete within timeout")

        # Verify projects appear in /api/projects
        r = await async_client.get("/api/projects", headers=headers)
        assert r.status_code == 200
        projects_data = r.json()
        projects = projects_data.get("projects", [])
        assert len(projects) >= 2, f"Expected at least 2 projects in list, got {len(projects)}"

    @pytest.mark.skip(reason="LLM requires Gemini API; run manually with API key")
    def test_llm_analysis_no_duplicate_projects(self, client, auth_headers, minimal_zip):
        """LLM analysis should not create duplicate project rows (single project = 1 row)."""
        headers, username = auth_headers

        with open(minimal_zip, "rb") as f:
            r = client.post(
                "/api/portfolios/upload",
                files={"file": ("test_project.zip", f, "application/zip")},
                data={"analysis_type": "llm", "project_name": "Single Project"},
                headers=headers,
            )
        assert r.status_code == 202
        task_id = r.json()["details"]["task_id"]

        max_wait = 180  # LLM can take longer
        poll_interval = 1
        elapsed = 0
        while elapsed < max_wait:
            r = client.get(f"/api/tasks/{task_id}", headers=headers)
            assert r.status_code == 200
            data = r.json()
            if data["status"] == "completed":
                break
            if data["status"] == "failed":
                pytest.fail(f"Task failed: {data.get('error')}")
            time.sleep(poll_interval)
            elapsed += poll_interval
        else:
            pytest.fail("Task did not complete within timeout")

        r = client.get("/api/projects", headers=headers)
        assert r.status_code == 200
        projects = r.json().get("projects", [])
        assert len(projects) == 1, f"Expected 1 project (no duplicates), got {len(projects)}"
