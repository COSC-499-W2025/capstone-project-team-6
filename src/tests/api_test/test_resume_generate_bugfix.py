"""
Regression tests for the resume generation bug fixes.

Four bugs were fixed and each has a dedicated test class here:

  Bug 1 — Field name mismatch: frontend sent `project_ids` but backend
           expected `portfolio_ids`, causing an immediate 422 on every request.

  Bug 2 — Wrong ID type: integer DB IDs were passed to get_analysis_by_uuid()
           which queries by UUID string, always returning 404.

  Bug 3 — Single-portfolio constraint: backend rejected any request with more
           than one ID, making multi-select impossible.

  Bug 4 — Wrong data shape: raw analysis JSON was passed to generate_resume()
           which expects {project, resume_items, portfolio} bundles, so all
           projects rendered as blank placeholders.
"""

import json
import sys
import uuid
from pathlib import Path
from unittest.mock import call, patch

import pytest
from fastapi.testclient import TestClient

src_dir = Path(__file__).resolve().parent.parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from backend import analysis_database as adb
from backend import database as udb
from backend.api.auth import active_tokens
from backend.api_server import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def clear_tokens():
    active_tokens.clear()
    yield
    active_tokens.clear()


@pytest.fixture(autouse=True)
def setup_temp_db(tmp_path):
    db_path = tmp_path / "bugfix_test.db"
    prev_user = udb.set_db_path(db_path)
    prev_analysis = adb.set_db_path(db_path)
    if db_path.exists():
        db_path.unlink()
    udb.init_db()
    adb.init_db()
    yield
    adb.set_db_path(prev_analysis)
    udb.set_db_path(prev_user)


@pytest.fixture
def auth_token():
    username = f"user_{uuid.uuid4().hex[:8]}"
    resp = client.post("/api/auth/signup", json={"username": username, "password": "pw1234"})
    return resp.json()["access_token"], username


# ---------------------------------------------------------------------------
# Bug 1 — Field name mismatch
# ---------------------------------------------------------------------------


class TestBug1FieldNameMismatch:
    """
    The request model used `portfolio_ids: List[str]` while the frontend
    sent `project_ids`.  Pydantic rejected every request with 422.
    """

    def test_project_ids_field_is_accepted_by_pydantic(self):
        """ResumeRequest must accept project_ids as a list of integers."""
        from backend.api.resume import ResumeRequest

        req = ResumeRequest(project_ids=[1, 2, 3])
        assert req.project_ids == [1, 2, 3]

    def test_portfolio_ids_field_is_rejected_with_422(self, auth_token):
        """Sending the old 'portfolio_ids' field with no 'project_ids' causes 422."""
        token, _ = auth_token
        response = client.post(
            "/api/resume/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "portfolio_ids": [str(uuid.uuid4())],  # old field name
                "format": "markdown",
            },
        )
        # Pydantic rejects the body because project_ids is required and missing
        assert response.status_code == 422

    def test_project_ids_as_integers_accepted_by_endpoint(self, auth_token):
        """
        Sending project_ids as integers must reach the endpoint logic
        (not be rejected at the Pydantic validation layer).
        We expect 404 here because the DB is empty, not 422.
        """
        token, _ = auth_token
        response = client.post(
            "/api/resume/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={"project_ids": [1], "format": "markdown"},
        )
        # 404 means the body passed validation and the endpoint ran
        assert response.status_code == 404
        assert response.status_code != 422

    def test_project_ids_as_uuid_strings_rejected_with_422(self, auth_token):
        """Sending UUID strings for project_ids should cause a 422 (wrong type)."""
        token, _ = auth_token
        response = client.post(
            "/api/resume/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={"project_ids": [str(uuid.uuid4())], "format": "markdown"},
        )
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Bug 2 — Wrong ID type (integer IDs vs UUID strings)
# ---------------------------------------------------------------------------


class TestBug2IntegerProjectIds:
    """
    The backend previously passed integer IDs to get_analysis_by_uuid() which
    queries by UUID string, always returning None → always 404.
    Now the endpoint looks up projects by integer ID via get_projects_for_user().
    """

    @patch("backend.api.resume.get_projects_for_user")
    @patch("backend.api.resume.get_resume_items_for_project_id")
    @patch("backend.api.resume.get_portfolio_item_for_project")
    @patch("backend.analysis.resume_generator.generate_resume")
    def test_integer_project_id_resolves_correctly(
        self, mock_gen, mock_portfolio, mock_items, mock_projects, auth_token
    ):
        """An integer project ID must resolve to the correct project dict."""
        token, username = auth_token
        mock_projects.return_value = [{"id": 42, "project_name": "MyApp", "primary_language": "Rust"}]
        mock_items.return_value = []
        mock_portfolio.return_value = {}
        mock_gen.return_value = "## Projects\n\n**MyApp** | *Rust*\n"

        response = client.post(
            "/api/resume/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={"project_ids": [42], "format": "markdown"},
        )
        assert response.status_code == 200
        assert "MyApp" in response.json()["content"]

    @patch("backend.api.resume.get_projects_for_user")
    @patch("backend.api.resume.get_resume_items_for_project_id")
    @patch("backend.api.resume.get_portfolio_item_for_project")
    @patch("backend.analysis.resume_generator.generate_resume")
    def test_get_analysis_by_uuid_is_never_called(
        self, mock_gen, mock_portfolio, mock_items, mock_projects, auth_token
    ):
        """The old UUID-based lookup must not be invoked at all."""
        token, _ = auth_token
        mock_projects.return_value = [{"id": 1, "project_name": "Proj", "primary_language": "Go"}]
        mock_items.return_value = []
        mock_portfolio.return_value = {}
        mock_gen.return_value = "content"

        with patch("backend.api.resume.get_analysis_by_uuid") as mock_uuid_lookup:
            client.post(
                "/api/resume/generate",
                headers={"Authorization": f"Bearer {token}"},
                json={"project_ids": [1], "format": "markdown"},
            )
            mock_uuid_lookup.assert_not_called()

    def test_non_owned_integer_ids_return_404(self, auth_token):
        """Integer IDs that don't belong to the user produce 404, not 200."""
        token, _ = auth_token
        # DB is empty for this user; project ID 999 doesn't exist
        response = client.post(
            "/api/resume/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={"project_ids": [999], "format": "markdown"},
        )
        assert response.status_code == 404
        assert "projects" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Bug 3 — Single-portfolio constraint removed
# ---------------------------------------------------------------------------


class TestBug3MultipleProjectsSupported:
    """
    The backend previously raised 404 if anything other than exactly one ID
    was passed.  Multi-select is now fully supported.
    """

    @patch("backend.api.resume.get_projects_for_user")
    @patch("backend.api.resume.get_resume_items_for_project_id")
    @patch("backend.api.resume.get_portfolio_item_for_project")
    @patch("backend.analysis.resume_generator.generate_resume")
    def test_two_projects_succeed(
        self, mock_gen, mock_portfolio, mock_items, mock_projects, auth_token
    ):
        token, _ = auth_token
        mock_projects.return_value = [
            {"id": 1, "project_name": "Alpha", "primary_language": "Python"},
            {"id": 2, "project_name": "Beta", "primary_language": "TypeScript"},
        ]
        mock_items.return_value = []
        mock_portfolio.return_value = {}
        mock_gen.return_value = "**Alpha**\n**Beta**\n"

        response = client.post(
            "/api/resume/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={"project_ids": [1, 2], "format": "markdown"},
        )
        assert response.status_code == 200
        assert response.json()["metadata"]["project_count"] == 2

    @patch("backend.api.resume.get_projects_for_user")
    @patch("backend.api.resume.get_resume_items_for_project_id")
    @patch("backend.api.resume.get_portfolio_item_for_project")
    @patch("backend.analysis.resume_generator.generate_resume")
    def test_five_projects_succeed(
        self, mock_gen, mock_portfolio, mock_items, mock_projects, auth_token
    ):
        token, _ = auth_token
        mock_projects.return_value = [
            {"id": i, "project_name": f"Project{i}", "primary_language": "Java"}
            for i in range(1, 6)
        ]
        mock_items.return_value = []
        mock_portfolio.return_value = {}
        mock_gen.return_value = "Five projects"

        response = client.post(
            "/api/resume/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={"project_ids": [1, 2, 3, 4, 5], "format": "markdown"},
        )
        assert response.status_code == 200
        assert response.json()["metadata"]["project_count"] == 5

    def test_empty_project_ids_returns_400(self, auth_token):
        """An empty project_ids list must return 400, not 422 or 500."""
        token, _ = auth_token
        response = client.post(
            "/api/resume/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={"project_ids": [], "format": "markdown"},
        )
        assert response.status_code == 400

    @patch("backend.api.resume.get_projects_for_user")
    @patch("backend.api.resume.get_resume_items_for_project_id")
    @patch("backend.api.resume.get_portfolio_item_for_project")
    @patch("backend.analysis.resume_generator.generate_resume")
    def test_generator_receives_all_bundles(
        self, mock_gen, mock_portfolio, mock_items, mock_projects, auth_token
    ):
        """generate_resume_impl must be called with one bundle per selected project."""
        token, _ = auth_token
        mock_projects.return_value = [
            {"id": 10, "project_name": "X", "primary_language": "C"},
            {"id": 20, "project_name": "Y", "primary_language": "C++"},
        ]
        mock_items.return_value = []
        mock_portfolio.return_value = {}
        mock_gen.return_value = "ok"

        client.post(
            "/api/resume/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={"project_ids": [10, 20], "format": "markdown"},
        )

        mock_gen.assert_called_once()
        bundles = mock_gen.call_args[1]["projects"]
        assert len(bundles) == 2
        project_ids_in_bundles = {b["project"]["id"] for b in bundles}
        assert project_ids_in_bundles == {10, 20}


# ---------------------------------------------------------------------------
# Bug 4 — Wrong data shape passed to generate_resume
# ---------------------------------------------------------------------------


class TestBug4CorrectBundleShape:
    """
    The old code passed raw analysis JSON dicts to generate_resume() which
    expects structured {project, resume_items, portfolio} bundles.  Every
    project rendered as a blank placeholder.
    """

    @patch("backend.api.resume.get_projects_for_user")
    @patch("backend.api.resume.get_resume_items_for_project_id")
    @patch("backend.api.resume.get_portfolio_item_for_project")
    @patch("backend.analysis.resume_generator.generate_resume")
    def test_bundle_has_project_key(
        self, mock_gen, mock_portfolio, mock_items, mock_projects, auth_token
    ):
        """Each bundle passed to generate_resume must contain a 'project' key."""
        token, _ = auth_token
        mock_projects.return_value = [{"id": 1, "project_name": "Foo", "primary_language": "Ruby"}]
        mock_items.return_value = []
        mock_portfolio.return_value = {}
        mock_gen.return_value = "ok"

        client.post(
            "/api/resume/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={"project_ids": [1], "format": "markdown"},
        )

        bundles = mock_gen.call_args[1]["projects"]
        assert len(bundles) == 1
        assert "project" in bundles[0]
        assert bundles[0]["project"]["project_name"] == "Foo"

    @patch("backend.api.resume.get_projects_for_user")
    @patch("backend.api.resume.get_resume_items_for_project_id")
    @patch("backend.api.resume.get_portfolio_item_for_project")
    @patch("backend.analysis.resume_generator.generate_resume")
    def test_bundle_has_resume_items_key(
        self, mock_gen, mock_portfolio, mock_items, mock_projects, auth_token
    ):
        """Each bundle must contain a 'resume_items' key from the DB lookup."""
        token, _ = auth_token
        mock_projects.return_value = [{"id": 5, "project_name": "Bar", "primary_language": "Kotlin"}]
        mock_items.return_value = [
            {"id": 11, "resume_text": "Built a scalable API", "bullet_order": 0}
        ]
        mock_portfolio.return_value = {}
        mock_gen.return_value = "ok"

        client.post(
            "/api/resume/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={"project_ids": [5], "format": "markdown"},
        )

        bundles = mock_gen.call_args[1]["projects"]
        assert "resume_items" in bundles[0]
        assert bundles[0]["resume_items"][0]["resume_text"] == "Built a scalable API"
        # Verify resume items were fetched for the correct project ID
        mock_items.assert_called_once_with(5)

    @patch("backend.api.resume.get_projects_for_user")
    @patch("backend.api.resume.get_resume_items_for_project_id")
    @patch("backend.api.resume.get_portfolio_item_for_project")
    @patch("backend.analysis.resume_generator.generate_resume")
    def test_bundle_portfolio_skills_parsed_from_json_string(
        self, mock_gen, mock_portfolio, mock_items, mock_projects, auth_token
    ):
        """
        skills_exercised is stored as a JSON string in the DB.
        The endpoint must parse it and expose the list under portfolio['skills'].
        """
        token, _ = auth_token
        mock_projects.return_value = [{"id": 7, "project_name": "Baz", "primary_language": "Swift"}]
        mock_items.return_value = []
        # skills_exercised as raw JSON string (as stored in SQLite)
        mock_portfolio.return_value = {
            "skills_exercised": json.dumps(["Swift", "CoreData", "Combine"]),
            "tech_stack": json.dumps(["Xcode", "SwiftUI"]),
        }
        mock_gen.return_value = "ok"

        client.post(
            "/api/resume/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={"project_ids": [7], "format": "markdown"},
        )

        bundles = mock_gen.call_args[1]["projects"]
        portfolio = bundles[0]["portfolio"]
        # skills_exercised must be a parsed list, not a raw JSON string
        assert isinstance(portfolio["skills_exercised"], list)
        assert "Swift" in portfolio["skills_exercised"]
        # skills key must be present and equal to skills_exercised
        assert portfolio["skills"] == portfolio["skills_exercised"]

    @patch("backend.api.resume.get_projects_for_user")
    @patch("backend.api.resume.get_resume_items_for_project_id")
    @patch("backend.api.resume.get_portfolio_item_for_project")
    @patch("backend.analysis.resume_generator.generate_resume")
    def test_bundle_portfolio_missing_skills_defaults_to_empty_list(
        self, mock_gen, mock_portfolio, mock_items, mock_projects, auth_token
    ):
        """When a project has no portfolio item, portfolio['skills'] must be []."""
        token, _ = auth_token
        mock_projects.return_value = [{"id": 3, "project_name": "Qux", "primary_language": "PHP"}]
        mock_items.return_value = []
        mock_portfolio.return_value = {}  # No portfolio item exists
        mock_gen.return_value = "ok"

        client.post(
            "/api/resume/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={"project_ids": [3], "format": "markdown"},
        )

        bundles = mock_gen.call_args[1]["projects"]
        assert bundles[0]["portfolio"]["skills"] == []

    @patch("backend.api.resume.get_projects_for_user")
    @patch("backend.api.resume.get_resume_items_for_project_id")
    @patch("backend.api.resume.get_portfolio_item_for_project")
    @patch("backend.analysis.resume_generator.generate_resume")
    def test_resume_items_fetched_once_per_project(
        self, mock_gen, mock_portfolio, mock_items, mock_projects, auth_token
    ):
        """get_resume_items_for_project_id must be called exactly once per project."""
        token, _ = auth_token
        mock_projects.return_value = [
            {"id": 10, "project_name": "P1", "primary_language": "Scala"},
            {"id": 20, "project_name": "P2", "primary_language": "Haskell"},
        ]
        mock_items.return_value = []
        mock_portfolio.return_value = {}
        mock_gen.return_value = "ok"

        client.post(
            "/api/resume/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={"project_ids": [10, 20], "format": "markdown"},
        )

        assert mock_items.call_count == 2
        called_ids = {c.args[0] for c in mock_items.call_args_list}
        assert called_ids == {10, 20}

    @patch("backend.api.resume.get_projects_for_user")
    @patch("backend.api.resume.get_resume_items_for_project_id")
    @patch("backend.api.resume.get_portfolio_item_for_project")
    def test_end_to_end_resume_content_contains_project_name(
        self, mock_portfolio, mock_items, mock_projects, auth_token
    ):
        """
        Full integration: with real generate_resume_impl, the output must
        contain the project name, not a blank 'Project' placeholder.
        """
        token, _ = auth_token
        mock_projects.return_value = [
            {"id": 1, "project_name": "CapstoneApp", "primary_language": "Python"}
        ]
        mock_items.return_value = [
            {"id": 1, "resume_text": "Designed a REST API for portfolio analysis", "bullet_order": 0}
        ]
        mock_portfolio.return_value = {}

        response = client.post(
            "/api/resume/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={"project_ids": [1], "format": "markdown"},
        )

        assert response.status_code == 200
        content = response.json()["content"]
        # The real generator must render the actual project name, not "Project"
        assert "CapstoneApp" in content
        assert "Designed a REST API" in content


# ---------------------------------------------------------------------------
# Metadata regression
# ---------------------------------------------------------------------------


class TestMetadataRegression:
    """The response metadata must use project_count, not the old portfolio_count."""

    @patch("backend.api.resume.get_projects_for_user")
    @patch("backend.api.resume.get_resume_items_for_project_id")
    @patch("backend.api.resume.get_portfolio_item_for_project")
    @patch("backend.analysis.resume_generator.generate_resume")
    def test_metadata_contains_project_count(
        self, mock_gen, mock_portfolio, mock_items, mock_projects, auth_token
    ):
        token, username = auth_token
        mock_projects.return_value = [
            {"id": 1, "project_name": "A", "primary_language": "Python"},
            {"id": 2, "project_name": "B", "primary_language": "Go"},
        ]
        mock_items.return_value = []
        mock_portfolio.return_value = {}
        mock_gen.return_value = "content"

        response = client.post(
            "/api/resume/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={"project_ids": [1, 2], "format": "markdown"},
        )

        metadata = response.json()["metadata"]
        assert "project_count" in metadata
        assert metadata["project_count"] == 2
        # The old field must not appear
        assert "portfolio_count" not in metadata

    @patch("backend.api.resume.get_projects_for_user")
    @patch("backend.api.resume.get_resume_items_for_project_id")
    @patch("backend.api.resume.get_portfolio_item_for_project")
    @patch("backend.analysis.resume_generator.generate_resume")
    def test_metadata_contains_required_fields(
        self, mock_gen, mock_portfolio, mock_items, mock_projects, auth_token
    ):
        token, username = auth_token
        mock_projects.return_value = [{"id": 1, "project_name": "A", "primary_language": "Python"}]
        mock_items.return_value = []
        mock_portfolio.return_value = {}
        mock_gen.return_value = "content"

        response = client.post(
            "/api/resume/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={"project_ids": [1], "format": "markdown"},
        )

        metadata = response.json()["metadata"]
        assert metadata["username"] == username
        assert "project_count" in metadata
        assert "total_projects" in metadata
        assert "generated_at" in metadata
