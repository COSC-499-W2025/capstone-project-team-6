#!/usr/bin/env python3
"""
Tests for role curation functionality.

Tests the ability to curate predicted developer roles, including:
- Saving curated roles for projects
- Retrieving curated roles
- User scoping and access control
- Custom role descriptions
- Integration with existing project data
"""

import pytest
import tempfile
from pathlib import Path
import sys
import os

# Add src directory to path so backend imports work
current_dir = Path(__file__).parent
src_dir = current_dir.parent.parent
sys.path.insert(0, str(src_dir))

from backend import analysis_database as adb
from backend.curation import (
    save_curated_role,
    get_curated_role,
    get_user_projects_with_roles,
    init_curation_tables
)
from backend.database import create_user, UserAlreadyExistsError

# Sample payload for creating test projects
SAMPLE_PAYLOAD = {
    "analysis_metadata": {
        "zip_file": "test/role_curation_project.zip",
        "analysis_timestamp": "2026-02-01T12:00:00",
        "total_projects": 1,
    },
    "projects": [
        {
            "project_name": "test_role_project",
            "project_path": "/workspace/test_role_project",
            "primary_language": "python",
            "languages": {"python": 15, "javascript": 3},
            "total_files": 25,
            "total_size": 524_288,
            "code_files": 18,
            "test_files": 5,
            "doc_files": 2,
            "config_files": 3,
            "frameworks": ["Django", "React"],
            "dependencies": {
                "python": ["django", "requests", "pytest"],
                "javascript": ["react", "react-dom"],
            },
            "has_tests": True,
            "has_readme": True,
            "has_ci_cd": True,
            "has_docker": True,
            "test_coverage_estimate": "medium",
            "is_git_repo": True,
            "target_user_email": "test@example.com",
            "target_user_stats": {
                "email": "test@example.com",
                "name": "Test User",
                "commit_count": 45,
                "percentage": 37.5,
                "last_commit_date": "2025-01-01T00:00:00",
            },
            "contribution_volume": {"test@example.com": 120},
            "blame_summary": {"test@example.com": 100},
            "contributors": [
                {
                    "email": "test@example.com",
                    "name": "Test User",
                    "commit_count": 45,
                    "percentage": 37.5,
                    "last_commit_date": "2025-01-01T00:00:00",
                }
            ],
            "collaboration_score": "low",
            "role_prediction": {
                "predicted_role": "Full Stack Developer",
                "confidence_score": 0.85,
                "reasoning": "Strong full stack skills with both frontend and backend technologies",
                "alternative_roles": [
                    ("Backend Developer", 0.75),
                    ("Senior Software Engineer", 0.70)
                ]
            }
        }
    ],
}


@pytest.fixture
def temp_analysis_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
        temp_db_path = Path(tmp_file.name)
    
    # Set the temporary database path
    original_path = adb.set_db_path(temp_db_path)
    
    # Initialize database tables
    adb.init_db()
    init_curation_tables()
    
    try:
        yield temp_db_path
    finally:
        # Restore original path and clean up
        adb.set_db_path(original_path)
        if temp_db_path.exists():
            temp_db_path.unlink()


def create_test_user_safely(username):
    """Create a test user, ignoring if they already exist."""
    try:
        create_user(username, "password123")
    except UserAlreadyExistsError:
        pass  # User already exists, that's fine


def create_test_project_with_role(username, project_name="test_project"):
    """Create a test project with role prediction data."""
    create_test_user_safely(username)
    
    # Create custom payload for this project
    payload = SAMPLE_PAYLOAD.copy()
    payload["projects"][0]["project_name"] = project_name
    payload["analysis_metadata"]["zip_file"] = f"test/{project_name}.zip"
    
    analysis_id = adb.record_analysis("non_llm", payload, username=username)
    projects = adb.get_projects_for_analysis(analysis_id)
    return projects[0] if projects else None


class TestSaveCuratedRole:
    """Test the save_curated_role function."""

    def test_save_curated_role_success(self, temp_analysis_db):
        """Test successfully saving a curated role."""
        username = "test_role_user"
        project = create_test_project_with_role(username)
        
        # Save a curated role
        success = save_curated_role(username, project["id"], "Senior Python Developer")
        assert success is True
        
        # Verify it was saved
        with adb.get_connection() as conn:
            result = conn.execute(
                "SELECT curated_role FROM projects WHERE id = ?",
                (project["id"],)
            ).fetchone()
            assert result["curated_role"] == "Senior Python Developer"

    def test_save_curated_role_custom_description(self, temp_analysis_db):
        """Test saving a custom role description."""
        username = "test_custom_user"
        project = create_test_project_with_role(username)
        
        custom_role = "Machine Learning Engineer specializing in NLP"
        success = save_curated_role(username, project["id"], custom_role)
        assert success is True
        
        # Verify the custom role was saved
        saved_role = get_curated_role(username, project["id"])
        assert saved_role == custom_role

    def test_save_curated_role_clear_role(self, temp_analysis_db):
        """Test clearing a curated role (set to None)."""
        username = "test_clear_user"
        project = create_test_project_with_role(username)
        
        # First set a role
        save_curated_role(username, project["id"], "Backend Developer")
        assert get_curated_role(username, project["id"]) == "Backend Developer"
        
        # Then clear it
        success = save_curated_role(username, project["id"], None)
        assert success is True
        assert get_curated_role(username, project["id"]) is None

    def test_save_curated_role_update_existing(self, temp_analysis_db):
        """Test updating an existing curated role."""
        username = "test_update_user"
        project = create_test_project_with_role(username)
        
        # Save initial role
        save_curated_role(username, project["id"], "Frontend Developer")
        assert get_curated_role(username, project["id"]) == "Frontend Developer"
        
        # Update the role
        success = save_curated_role(username, project["id"], "Full Stack Developer")
        assert success is True
        assert get_curated_role(username, project["id"]) == "Full Stack Developer"

    def test_save_curated_role_wrong_user(self, temp_analysis_db):
        """Test that users cannot curate roles for projects they don't own."""
        owner_user = "project_owner"
        other_user = "other_user"
        
        # Create project owned by owner_user
        project = create_test_project_with_role(owner_user)
        create_test_user_safely(other_user)
        
        # Try to curate role as other_user
        success = save_curated_role(other_user, project["id"], "Unauthorized Role")
        assert success is False
        
        # Verify no role was saved
        assert get_curated_role(other_user, project["id"]) is None

    def test_save_curated_role_nonexistent_project(self, temp_analysis_db):
        """Test saving role for non-existent project."""
        username = "test_nonexistent_user"
        create_test_user_safely(username)
        
        success = save_curated_role(username, 99999, "Some Role")
        assert success is False


class TestGetCuratedRole:
    """Test the get_curated_role function."""

    def test_get_curated_role_exists(self, temp_analysis_db):
        """Test getting a curated role that exists."""
        username = "test_get_user"
        project = create_test_project_with_role(username)
        
        # Save a role
        save_curated_role(username, project["id"], "DevOps Engineer")
        
        # Retrieve it
        role = get_curated_role(username, project["id"])
        assert role == "DevOps Engineer"

    def test_get_curated_role_not_set(self, temp_analysis_db):
        """Test getting curated role when none is set."""
        username = "test_get_none_user"
        project = create_test_project_with_role(username)
        
        # No role set - should return None
        role = get_curated_role(username, project["id"])
        assert role is None

    def test_get_curated_role_wrong_user(self, temp_analysis_db):
        """Test that users cannot access roles for projects they don't own."""
        owner_user = "role_owner"
        other_user = "role_other"
        
        # Create project and set role as owner
        project = create_test_project_with_role(owner_user)
        save_curated_role(owner_user, project["id"], "Secret Role")
        
        # Try to access as other user
        create_test_user_safely(other_user)
        role = get_curated_role(other_user, project["id"])
        assert role is None

    def test_get_curated_role_nonexistent_project(self, temp_analysis_db):
        """Test getting role for non-existent project."""
        username = "test_nonexistent_get_user"
        create_test_user_safely(username)
        
        role = get_curated_role(username, 99999)
        assert role is None


class TestGetUserProjectsWithRoles:
    """Test the get_user_projects_with_roles function."""

    def test_get_projects_with_roles_basic(self, temp_analysis_db):
        """Test getting projects with role information."""
        username = "test_projects_user"
        
        # Create multiple projects
        project1 = create_test_project_with_role(username, "project_one")
        project2 = create_test_project_with_role(username, "project_two")
        
        # Set curated role for one project
        save_curated_role(username, project1["id"], "Senior Developer")
        
        # Get projects with roles
        projects = get_user_projects_with_roles(username)
        
        assert len(projects) == 2
        project_names = [p["project_name"] for p in projects]
        assert "project_one" in project_names
        assert "project_two" in project_names
        
        # Check role information
        for project in projects:
            assert "predicted_role" in project
            assert "curated_role" in project
            assert "predicted_role_confidence" in project
            
            if project["project_name"] == "project_one":
                assert project["curated_role"] == "Senior Developer"
            elif project["project_name"] == "project_two":
                assert project["curated_role"] is None

    def test_get_projects_with_roles_no_projects(self, temp_analysis_db):
        """Test getting projects when user has none."""
        username = "test_no_projects_user"
        create_test_user_safely(username)
        
        projects = get_user_projects_with_roles(username)
        assert projects == []

    def test_get_projects_with_roles_predicted_data(self, temp_analysis_db):
        """Test that predicted role data is included correctly."""
        username = "test_predicted_user"
        project = create_test_project_with_role(username)
        
        projects = get_user_projects_with_roles(username)
        assert len(projects) == 1
        
        project_data = projects[0]
        assert project_data["predicted_role"] == "Full Stack Developer"
        assert project_data["predicted_role_confidence"] == 0.85
        assert project_data["role_prediction_data"] is not None

    def test_get_projects_with_roles_user_scoping(self, temp_analysis_db):
        """Test that users only see their own projects."""
        user1 = "test_scope_user1"
        user2 = "test_scope_user2"
        
        # Create projects for each user
        project1 = create_test_project_with_role(user1, "user1_project")
        project2 = create_test_project_with_role(user2, "user2_project")
        
        # Each user should only see their own projects
        user1_projects = get_user_projects_with_roles(user1)
        user2_projects = get_user_projects_with_roles(user2)
        
        assert len(user1_projects) == 1
        assert len(user2_projects) == 1
        assert user1_projects[0]["project_name"] == "user1_project"
        assert user2_projects[0]["project_name"] == "user2_project"


class TestRoleCurationIntegration:
    """Test integration scenarios for role curation."""

    def test_role_curation_with_existing_prediction(self, temp_analysis_db):
        """Test that curated roles work alongside existing predictions."""
        username = "test_integration_user"
        project = create_test_project_with_role(username)
        
        # Verify predicted role exists
        projects = get_user_projects_with_roles(username)
        assert projects[0]["predicted_role"] == "Full Stack Developer"
        
        # Add curated role
        save_curated_role(username, project["id"], "Team Lead")
        
        # Both should be available
        updated_projects = get_user_projects_with_roles(username)
        project_data = updated_projects[0]
        assert project_data["predicted_role"] == "Full Stack Developer"
        assert project_data["curated_role"] == "Team Lead"

    def test_multiple_role_updates(self, temp_analysis_db):
        """Test multiple updates to the same project's role."""
        username = "test_multiple_user"
        project = create_test_project_with_role(username)
        
        roles_to_test = [
            "Junior Developer",
            "Backend Developer", 
            "Senior Software Engineer",
            "Tech Lead",
            None,  # Clear role
            "Custom Role Description"
        ]
        
        for role in roles_to_test:
            success = save_curated_role(username, project["id"], role)
            assert success is True
            retrieved_role = get_curated_role(username, project["id"])
            assert retrieved_role == role

    def test_special_characters_in_custom_role(self, temp_analysis_db):
        """Test that custom roles with special characters work."""
        username = "test_special_user"
        project = create_test_project_with_role(username)
        
        special_roles = [
            "ML Engineer (NLP/Computer Vision)",
            "Full-Stack Developer & DevOps",
            "Senior Developer @ 50% Frontend/50% Backend",
            "データサイエンティスト",  # Japanese characters
            "Développeur Senior",  # French accents
            "Role with\nnewlines\nand\ttabs"
        ]
        
        for role in special_roles:
            success = save_curated_role(username, project["id"], role)
            assert success is True
            retrieved_role = get_curated_role(username, project["id"])
            assert retrieved_role == role

    def test_long_custom_role_description(self, temp_analysis_db):
        """Test that long custom role descriptions work."""
        username = "test_long_user"
        project = create_test_project_with_role(username)
        
        long_role = ("Senior Full Stack Developer with expertise in Python, React, and AWS. "
                    "Specializes in building scalable microservices architectures and has "
                    "extensive experience in machine learning model deployment. Also leads "
                    "a team of 5 developers and manages DevOps infrastructure including "
                    "CI/CD pipelines, monitoring, and security implementations.")
        
        success = save_curated_role(username, project["id"], long_role)
        assert success is True
        retrieved_role = get_curated_role(username, project["id"])
        assert retrieved_role == long_role

    def test_role_curation_persistence(self, temp_analysis_db):
        """Test that curated roles persist across database connections."""
        username = "test_persistence_user"
        project = create_test_project_with_role(username)
        
        # Save role
        save_curated_role(username, project["id"], "Persistent Role")
        
        # Close and reopen database connection (simulated by new function calls)
        retrieved_role = get_curated_role(username, project["id"])
        assert retrieved_role == "Persistent Role"
        
        # Verify through projects list as well
        projects = get_user_projects_with_roles(username)
        assert projects[0]["curated_role"] == "Persistent Role"


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])