"""
Comprehensive tests for curation API endpoints.

Tests all REST API endpoints in backend.api.curation.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

# Add src directory to path
SRC = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(SRC))

from backend import analysis_database as db
from backend.curation import init_curation_tables


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path, monkeypatch):
    """Set up a temporary database for testing."""
    test_db_path = tmp_path / "test_curation_api.db"
    monkeypatch.setenv("ANALYSIS_DB_PATH", str(test_db_path))

    # Initialize tables
    db.init_db()
    init_curation_tables()

    yield test_db_path

    # Cleanup
    try:
        with db.get_connection() as conn:
            conn.execute("DELETE FROM project_chronology_corrections")
            conn.execute("DELETE FROM user_curation_settings")
            conn.execute("DELETE FROM project_skills")
            conn.execute("DELETE FROM project_frameworks")
            conn.execute("DELETE FROM project_languages")
            conn.execute("DELETE FROM projects")
            conn.execute("DELETE FROM analyses")
            conn.commit()
    except:
        pass

    if test_db_path.exists():
        test_db_path.unlink()


@pytest.fixture
def client():
    """Create an authenticated test client for the FastAPI app."""
    from backend.api_server import app
    from backend.api.auth import verify_token

    # Override the dependency to return a mock username (string, not dict)
    def mock_verify_token():
        return "test_user"
    
    app.dependency_overrides[verify_token] = mock_verify_token
    
    yield TestClient(app)
    
    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
def unauthenticated_client():
    """Create an unauthenticated test client (no auth override)."""
    from backend.api_server import app
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Create authentication headers for testing."""
    return {"Authorization": "Bearer test_token"}


@pytest.fixture
def mock_verify_token():
    """Deprecated: kept for compatibility but not used anymore."""
    # This fixture is no longer needed since we override the dependency in client fixture
    pass


@pytest.fixture
def sample_user_and_projects():
    """Create a sample user with projects."""
    user_id = "test_user"
    
    # Create user
    with db.get_connection() as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute(
            "INSERT OR IGNORE INTO users (username, password_hash) VALUES (?, ?)",
            (user_id, "test_hash"),
        )

        # Create analysis
        cursor = conn.execute(
            """
            INSERT INTO analyses
            (analysis_uuid, analysis_type, zip_file, analysis_timestamp, total_projects, raw_json, username)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "test-uuid-1",
                "non_llm",
                "test.zip",
                datetime(2024, 1, 15).isoformat(),
                3,
                json.dumps({"test": "data"}),
                user_id,
            ),
        )
        analysis_id = cursor.lastrowid

        # Create 3 sample projects
        projects = []
        for i in range(1, 4):
            cursor = conn.execute(
                """
                INSERT INTO projects
                (analysis_id, project_name, primary_language, total_files, code_files,
                 test_files, has_tests, has_readme, has_ci_cd, has_docker, total_commits,
                 last_commit_date, last_modified_date, project_start_date, project_end_date,
                 project_active_days)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    analysis_id,
                    f"Project{i}",
                    "Python",
                    20 + i,
                    15 + i,
                    2 + i,
                    1,
                    1,
                    0,
                    0,
                    30 + i,
                    datetime(2024, 1, i).isoformat(),
                    datetime(2024, 1, i + 1).isoformat(),
                    datetime(2023, 12, i).isoformat(),
                    datetime(2024, 1, i).isoformat(),
                    30 + i,
                ),
            )
            projects.append(cursor.lastrowid)
        
        conn.commit()
    
    return {"user_id": user_id, "project_ids": projects}


class TestCurationSettingsAPI:
    """Tests for GET /api/curation/settings endpoint."""

    def test_get_settings_requires_auth(self, unauthenticated_client):
        """Test that getting settings requires authentication."""
        response = unauthenticated_client.get("/api/curation/settings")
        assert response.status_code == 401

    def test_get_settings_success(self, client, sample_user_and_projects):
        """Test successfully getting curation settings."""
        response = client.get(
            "/api/curation/settings",
            headers={"Authorization": "Bearer test_token"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "comparison_attributes" in data
        assert "showcase_project_ids" in data
        assert "custom_project_order" in data
        assert "highlighted_skills" in data
        assert isinstance(data["comparison_attributes"], list)


class TestCurationProjectsAPI:
    """Tests for GET /api/curation/projects endpoint."""

    def test_get_projects_requires_auth(self, unauthenticated_client):
        """Test that getting projects requires authentication."""
        response = unauthenticated_client.get("/api/curation/projects")
        assert response.status_code == 401

    def test_get_projects_success(self, client, sample_user_and_projects):
        """Test successfully getting user projects."""
        response = client.get(
            "/api/curation/projects",
            headers={"Authorization": "Bearer test_token"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3
        
        # Check project structure
        project = data[0]
        assert "id" in project
        assert "project_name" in project
        assert "primary_language" in project


class TestShowcaseAPI:
    """Tests for showcase projects endpoints."""

    def test_get_showcase_requires_auth(self, unauthenticated_client):
        """Test that getting showcase requires authentication."""
        response = unauthenticated_client.get("/api/curation/showcase")
        assert response.status_code == 401

    def test_get_showcase_empty(self, client, sample_user_and_projects):
        """Test getting showcase when none are set."""
        response = client.get(
            "/api/curation/showcase",
            headers={"Authorization": "Bearer test_token"},
        )
        
        assert response.status_code == 200
        data = response.json()
        # GET /skills returns all available skills (not user's highlighted skills)
        assert isinstance(data, list)

    def test_save_showcase_success(self, client, sample_user_and_projects):
        """Test successfully saving showcase projects."""
        project_ids = sample_user_and_projects["project_ids"]
        
        response = client.post(
            "/api/curation/showcase",
            headers={"Authorization": "Bearer test_token"},
            json={"project_ids": [project_ids[0], project_ids[1]]},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True

    def test_save_showcase_max_three(self, client, sample_user_and_projects):
        """Test that showcase is limited to 3 projects."""
        project_ids = sample_user_and_projects["project_ids"]
        
        # Try to save more than 3
        response = client.post(
            "/api/curation/showcase",
            headers={"Authorization": "Bearer test_token"},
            json={"project_ids": project_ids + [999]},  # 4 projects
        )
        
        # Pydantic validation returns 422 for field validation errors
        assert response.status_code == 422

    def test_get_showcase_after_save(self, client, sample_user_and_projects):
        """Test getting showcase after saving."""
        project_ids = sample_user_and_projects["project_ids"]
        
        # Save showcase
        client.post(
            "/api/curation/showcase",
            headers={"Authorization": "Bearer test_token"},
            json={"project_ids": [project_ids[0]]},
        )
        
        # Get showcase - returns full project objects, not just IDs
        response = client.get(
            "/api/curation/showcase",
            headers={"Authorization": "Bearer test_token"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["id"] == project_ids[0]


class TestAttributesAPI:
    """Tests for comparison attributes endpoints."""

    def test_get_attributes_requires_auth(self, unauthenticated_client):
        """Test that getting attributes requires authentication."""
        response = unauthenticated_client.get("/api/curation/attributes")
        assert response.status_code == 401

    def test_get_attributes_default(self, client, sample_user_and_projects):
        """Test getting default attributes."""
        response = client.get(
            "/api/curation/attributes",
            headers={"Authorization": "Bearer test_token"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should return default attributes
        assert len(data) > 0

    def test_save_attributes_success(self, client, sample_user_and_projects):
        """Test successfully saving attributes."""
        response = client.post(
            "/api/curation/attributes",
            headers={"Authorization": "Bearer test_token"},
            json={"attributes": ["total_files", "has_tests", "primary_language"]},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True

    def test_save_attributes_invalid(self, client, sample_user_and_projects):
        """Test saving invalid attributes."""
        response = client.post(
            "/api/curation/attributes",
            headers={"Authorization": "Bearer test_token"},
            json={"attributes": ["invalid_attribute"]},
        )
        
        assert response.status_code == 400


class TestSkillsAPI:
    """Tests for highlighted skills endpoints."""

    def test_get_skills_requires_auth(self, unauthenticated_client):
        """Test that getting skills requires authentication."""
        response = unauthenticated_client.get("/api/curation/skills")
        assert response.status_code == 401

    def test_get_skills_empty(self, client, sample_user_and_projects):
        """Test getting skills when none are set."""
        response = client.get(
            "/api/curation/skills",
            headers={"Authorization": "Bearer test_token"},
        )
        
        assert response.status_code == 200
        data = response.json()
        # GET /skills returns all available skills (not user's highlighted skills)
        assert isinstance(data, list)

    def test_save_skills_success(self, client, sample_user_and_projects):
        """Test successfully saving skills."""
        response = client.post(
            "/api/curation/skills",
            headers={"Authorization": "Bearer test_token"},
            json={"skills": ["Python", "JavaScript", "React", "FastAPI"]},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True

    def test_save_skills_max_ten(self, client, sample_user_and_projects):
        """Test that skills are limited to 10."""
        skills = [f"Skill{i}" for i in range(11)]
        
        response = client.post(
            "/api/curation/skills",
            headers={"Authorization": "Bearer test_token"},
            json={"skills": skills},
        )
        
        # Pydantic validation returns 422 for field validation errors
        assert response.status_code == 422

    def test_get_skills_after_save(self, client, sample_user_and_projects):
        """Test getting skills after saving user's highlighted skills."""
        skills = ["Python", "JavaScript"]
        
        # Save skills
        save_response = client.post(
            "/api/curation/skills",
            headers={"Authorization": "Bearer test_token"},
            json={"skills": skills},
        )
        assert save_response.status_code == 200
        
        # Get settings to verify skills were saved (not from GET /skills which returns all available)
        response = client.get(
            "/api/curation/settings",
            headers={"Authorization": "Bearer test_token"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "highlighted_skills" in data
        assert "Python" in data["highlighted_skills"]
        assert "JavaScript" in data["highlighted_skills"]


class TestChronologyAPI:
    """Tests for chronology correction endpoint."""

    def test_save_chronology_success(self, client, sample_user_and_projects):
        """Test successfully saving chronology correction."""
        project_id = sample_user_and_projects["project_ids"][0]
        
        response = client.post(
            "/api/curation/chronology",
            headers={"Authorization": "Bearer test_token"},
            json={
                "project_id": project_id,
                "last_commit_date": "2024-01-15",
                "last_modified_date": "2024-01-20",
                "project_start_date": "2024-01-01",
                "project_end_date": "2024-01-31",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True

    def test_save_chronology_partial_dates(self, client, sample_user_and_projects):
        """Test saving chronology with only some dates."""
        project_id = sample_user_and_projects["project_ids"][0]
        
        response = client.post(
            "/api/curation/chronology",
            headers={"Authorization": "Bearer test_token"},
            json={
                "project_id": project_id,
                "last_commit_date": "2024-01-15",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True


class TestProjectOrderAPI:
    """Tests for project order endpoint."""

    def test_save_order_success(self, client, sample_user_and_projects):
        """Test successfully saving project order."""
        project_ids = sample_user_and_projects["project_ids"]
        # Reverse the order
        reversed_order = list(reversed(project_ids))
        
        response = client.post(
            "/api/curation/order",
            headers={"Authorization": "Bearer test_token"},
            json={"project_ids": reversed_order},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True

    def test_save_empty_order(self, client, sample_user_and_projects):
        """Test saving empty order (reset to default)."""
        response = client.post(
            "/api/curation/order",
            headers={"Authorization": "Bearer test_token"},
            json={"project_ids": []},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True


class TestIntegrationWorkflow:
    """Integration tests for complete curation workflow."""

    def test_complete_curation_workflow(self, client, sample_user_and_projects):
        """Test a complete curation workflow through the API."""
        headers = {"Authorization": "Bearer test_token"}
        project_ids = sample_user_and_projects["project_ids"]
        
        # 1. Get initial settings
        response = client.get("/api/curation/settings", headers=headers)
        assert response.status_code == 200
        initial_settings = response.json()
        
        # 2. Set showcase projects
        response = client.post(
            "/api/curation/showcase",
            headers=headers,
            json={"project_ids": [project_ids[0], project_ids[1]]},
        )
        assert response.status_code == 200
        
        # 3. Set comparison attributes
        response = client.post(
            "/api/curation/attributes",
            headers=headers,
            json={"attributes": ["total_files", "has_tests", "primary_language"]},
        )
        assert response.status_code == 200
        
        # 4. Set highlighted skills
        response = client.post(
            "/api/curation/skills",
            headers=headers,
            json={"skills": ["Python", "React", "PostgreSQL"]},
        )
        assert response.status_code == 200
        
        # 5. Set project order
        response = client.post(
            "/api/curation/order",
            headers=headers,
            json={"project_ids": project_ids[::-1]},  # Reversed
        )
        assert response.status_code == 200
        
        # 6. Save chronology for a project
        response = client.post(
            "/api/curation/chronology",
            headers=headers,
            json={
                "project_id": project_ids[0],
                "last_commit_date": "2024-01-15",
            },
        )
        assert response.status_code == 200
        
        # 7. Verify all settings were saved
        response = client.get("/api/curation/settings", headers=headers)
        assert response.status_code == 200
        final_settings = response.json()
        
        assert len(final_settings["showcase_project_ids"]) == 2
        assert len(final_settings["comparison_attributes"]) == 3
        assert len(final_settings["highlighted_skills"]) == 3
        assert len(final_settings["custom_project_order"]) == 3
