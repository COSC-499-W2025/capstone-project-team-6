"""
Test cases for project curation functionality.

Tests chronology corrections, comparison attributes selection, and showcase projects.
"""

import json
import sqlite3
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

# Add src directory to path
SRC = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(SRC))

from backend import analysis_database as db
from backend.curation import (ATTRIBUTE_DESCRIPTIONS,
                              DEFAULT_COMPARISON_ATTRIBUTES,
                              ProjectChronologyCorrection,
                              ProjectCurationSettings,
                              format_project_comparison,
                              get_chronology_corrections,
                              get_showcase_projects,
                              get_user_curation_settings, get_user_projects,
                              init_curation_tables, save_chronology_correction,
                              save_comparison_attributes,
                              save_showcase_projects, validate_date_format)


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path, monkeypatch):
    """Set up a temporary database for testing."""
    test_db_path = tmp_path / "test_curation.db"
    monkeypatch.setenv("ANALYSIS_DB_PATH", str(test_db_path))

    # Initialize tables
    db.init_db()
    init_curation_tables()

    yield test_db_path

    # Cleanup - Clear all tables
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
def sample_projects():
    """Create sample project data for testing."""
    import uuid

    # Create analysis record with unique UUID
    analysis_data = {
        "analysis_uuid": f"test-uuid-{uuid.uuid4()}",
        "analysis_type": "non_llm",
        "zip_file": "test.zip",
        "analysis_timestamp": datetime(2024, 1, 15, 10, 0, 0).isoformat(),
        "total_projects": 2,
        "raw_json": json.dumps({"test": "data"}),
    }

    with db.get_connection() as conn:
        conn.execute("PRAGMA foreign_keys = ON;")

        # Insert analysis
        cursor = conn.execute(
            """
            INSERT INTO analyses 
            (analysis_uuid, analysis_type, zip_file, analysis_timestamp, total_projects, raw_json)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                analysis_data["analysis_uuid"],
                analysis_data["analysis_type"],
                analysis_data["zip_file"],
                analysis_data["analysis_timestamp"],
                analysis_data["total_projects"],
                analysis_data["raw_json"],
            ),
        )

        analysis_id = cursor.lastrowid

        # Insert sample projects
        projects_data = [
            {
                "project_name": "WebApp",
                "primary_language": "Python",
                "total_files": 25,
                "code_files": 18,
                "test_files": 5,
                "has_tests": 1,
                "has_readme": 1,
                "has_ci_cd": 1,
                "has_docker": 0,
                "total_commits": 42,
                "last_commit_date": datetime(2024, 1, 10, 15, 30, 0).isoformat(),
                "last_modified_date": datetime(2024, 1, 12, 9, 15, 0).isoformat(),
                "project_start_date": datetime(2023, 12, 1, 0, 0, 0).isoformat(),
                "project_end_date": datetime(2024, 1, 10, 15, 30, 0).isoformat(),
                "project_active_days": 40,
            },
            {
                "project_name": "MobileApp",
                "primary_language": "JavaScript",
                "total_files": 35,
                "code_files": 28,
                "test_files": 3,
                "has_tests": 1,
                "has_readme": 0,
                "has_ci_cd": 0,
                "has_docker": 1,
                "total_commits": 28,
                "last_commit_date": datetime(2024, 1, 5, 14, 20, 0).isoformat(),
                "last_modified_date": datetime(2024, 1, 6, 11, 45, 0).isoformat(),
                "project_start_date": datetime(2023, 11, 15, 0, 0, 0).isoformat(),
                "project_end_date": datetime(2024, 1, 5, 14, 20, 0).isoformat(),
                "project_active_days": 51,
            },
            {
                "project_name": "DataPipeline",
                "primary_language": "Go",
                "total_files": 15,
                "code_files": 12,
                "test_files": 2,
                "has_tests": 1,
                "has_readme": 1,
                "has_ci_cd": 1,
                "has_docker": 1,
                "total_commits": 18,
                "last_commit_date": datetime(2024, 1, 8, 16, 10, 0).isoformat(),
                "last_modified_date": datetime(2024, 1, 9, 13, 20, 0).isoformat(),
                "project_start_date": datetime(2023, 12, 20, 0, 0, 0).isoformat(),
                "project_end_date": datetime(2024, 1, 8, 16, 10, 0).isoformat(),
                "project_active_days": 19,
            },
        ]

        project_ids = []
        for project_data in projects_data:
            cursor = conn.execute(
                """
                INSERT INTO projects
                (analysis_id, project_name, primary_language, total_files, code_files, test_files,
                 has_tests, has_readme, has_ci_cd, has_docker, total_commits,
                 last_commit_date, last_modified_date, project_start_date, project_end_date, project_active_days)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    analysis_id,
                    project_data["project_name"],
                    project_data["primary_language"],
                    project_data["total_files"],
                    project_data["code_files"],
                    project_data["test_files"],
                    project_data["has_tests"],
                    project_data["has_readme"],
                    project_data["has_ci_cd"],
                    project_data["has_docker"],
                    project_data["total_commits"],
                    project_data["last_commit_date"],
                    project_data["last_modified_date"],
                    project_data["project_start_date"],
                    project_data["project_end_date"],
                    project_data["project_active_days"],
                ),
            )

            project_id = cursor.lastrowid
            project_ids.append(project_id)

            # Add some languages and frameworks
            if project_data["project_name"] == "WebApp":
                conn.execute(
                    "INSERT INTO project_languages (project_id, language, file_count) VALUES (?, ?, ?)",
                    (project_id, "Python", 18),
                )
                conn.execute("INSERT INTO project_frameworks (project_id, framework) VALUES (?, ?)", (project_id, "Flask"))
            elif project_data["project_name"] == "MobileApp":
                conn.execute(
                    "INSERT INTO project_languages (project_id, language, file_count) VALUES (?, ?, ?)",
                    (project_id, "JavaScript", 28),
                )
                conn.execute("INSERT INTO project_frameworks (project_id, framework) VALUES (?, ?)", (project_id, "React Native"))
            elif project_data["project_name"] == "DataPipeline":
                conn.execute(
                    "INSERT INTO project_languages (project_id, language, file_count) VALUES (?, ?, ?)", (project_id, "Go", 12)
                )
                conn.execute("INSERT INTO project_frameworks (project_id, framework) VALUES (?, ?)", (project_id, "Gin"))

        conn.commit()
        return project_ids


class TestDateValidation:
    """Test date validation functionality."""

    def test_validate_date_format_valid_dates(self):
        """Test validation of valid date formats."""
        assert validate_date_format("2024-01-15")
        assert validate_date_format("2024-01-15T10:30:00")
        assert validate_date_format("2024-01-15T10:30:00Z")
        assert validate_date_format("2024-01-15T10:30:00.123456")

    def test_validate_date_format_invalid_dates(self):
        """Test validation of invalid date formats."""
        assert not validate_date_format("invalid-date")
        assert not validate_date_format("2024-13-40")
        assert not validate_date_format("24-01-15")
        assert not validate_date_format("")
        assert not validate_date_format(None)


class TestChronologyCorrection:
    """Test chronology correction functionality."""

    def test_save_chronology_correction(self, sample_projects):
        """Test saving chronology corrections."""
        project_ids = sample_projects
        user_id = f"test_user_{project_ids[0]}"  # Unique user ID per test

        # Save correction
        new_commit_date = "2024-02-01T10:00:00"
        new_start_date = "2023-11-01T00:00:00"

        success = save_chronology_correction(
            project_ids[0], user_id, last_commit_date=new_commit_date, project_start_date=new_start_date
        )

        assert success

        # Verify correction was saved
        corrections = get_chronology_corrections(user_id)
        assert len(corrections) == 1

        correction = corrections[0]
        assert correction.project_id == project_ids[0]
        assert correction.user_id == user_id
        assert correction.last_commit_date == new_commit_date
        assert correction.project_start_date == new_start_date
        assert correction.last_modified_date is None
        assert correction.project_end_date is None
        assert correction.correction_timestamp is not None

    def test_save_chronology_correction_invalid_project(self):
        """Test saving correction for non-existent project."""
        success = save_chronology_correction(
            999999, "test_user_invalid", last_commit_date="2024-02-01T10:00:00"  # Non-existent project ID
        )

        assert not success

    def test_get_user_projects_with_corrections(self, sample_projects):
        """Test getting user projects with chronology corrections applied."""
        project_ids = sample_projects
        user_id = f"test_user_corrected_{project_ids[0]}"

        # Save corrections for first project
        new_commit_date = "2024-03-01T15:00:00"
        save_chronology_correction(project_ids[0], user_id, last_commit_date=new_commit_date)

        # Get projects
        projects = get_user_projects(user_id)

        assert len(projects) == 3

        # Find the corrected project
        corrected_project = next(p for p in projects if p["id"] == project_ids[0])
        uncorrected_project = next(p for p in projects if p["id"] == project_ids[1])

        # Check corrected project uses new date
        assert corrected_project["effective_last_commit_date"] == new_commit_date
        assert corrected_project["correction_timestamp"] is not None

        # Check uncorrected project uses original date
        assert uncorrected_project["correction_timestamp"] is None
        assert uncorrected_project["effective_last_commit_date"] == uncorrected_project["last_commit_date"]


class TestComparisonAttributes:
    """Test comparison attributes functionality."""

    def test_save_comparison_attributes_valid(self):
        """Test saving valid comparison attributes."""
        user_id = "test_user_comp_valid"
        attributes = ["total_files", "has_tests", "primary_language"]

        success = save_comparison_attributes(user_id, attributes)
        assert success

        # Verify attributes were saved
        settings = get_user_curation_settings(user_id)
        assert set(settings.comparison_attributes) == set(attributes)

    def test_save_comparison_attributes_invalid(self):
        """Test saving invalid comparison attributes."""
        user_id = "test_user_comp_invalid"
        attributes = ["invalid_attribute", "another_invalid"]

        success = save_comparison_attributes(user_id, attributes)
        assert not success

    def test_get_user_curation_settings_defaults(self):
        """Test getting default curation settings for new user."""
        user_id = "new_user_defaults"

        settings = get_user_curation_settings(user_id)

        assert settings.user_id == user_id
        assert set(settings.comparison_attributes) == set(DEFAULT_COMPARISON_ATTRIBUTES)
        assert settings.showcase_project_ids == []

    def test_format_project_comparison(self, sample_projects):
        """Test formatting project comparison table."""
        user_id = f"test_user_format_{sample_projects[0]}"

        # Set specific comparison attributes
        attributes = ["total_files", "has_tests", "primary_language"]
        save_comparison_attributes(user_id, attributes)

        # Get projects
        projects = get_user_projects(user_id)

        # Format comparison
        comparison = format_project_comparison(projects, user_id)

        assert "Project" in comparison
        assert "Total files count" in comparison
        assert "Has test suite" in comparison
        assert "Primary programming language" in comparison
        assert "WebApp" in comparison
        assert "MobileApp" in comparison
        assert "DataPipeline" in comparison


class TestShowcaseProjects:
    """Test showcase projects functionality."""

    def test_save_showcase_projects_valid(self, sample_projects):
        """Test saving valid showcase project selection."""
        project_ids = sample_projects
        user_id = f"test_user_showcase_valid_{project_ids[0]}"

        # Select first 2 projects
        selected_ids = project_ids[:2]

        success = save_showcase_projects(user_id, selected_ids)
        assert success

        # Verify selection was saved
        settings = get_user_curation_settings(user_id)
        assert set(settings.showcase_project_ids) == set(selected_ids)

    def test_save_showcase_projects_too_many(self, sample_projects):
        """Test saving too many showcase projects (>3)."""
        project_ids = sample_projects + [999]  # 4 projects
        user_id = f"test_user_showcase_too_many_{sample_projects[0]}"

        success = save_showcase_projects(user_id, project_ids)
        assert not success

    def test_save_showcase_projects_invalid_id(self, sample_projects):
        """Test saving showcase projects with invalid ID."""
        user_id = f"test_user_showcase_invalid_{sample_projects[0]}"
        invalid_ids = [999999]  # Non-existent project ID

        success = save_showcase_projects(user_id, invalid_ids)
        assert not success

    def test_get_showcase_projects(self, sample_projects):
        """Test getting showcase projects with full details."""
        project_ids = sample_projects
        user_id = f"test_user_get_showcase_{project_ids[0]}"

        # Select showcase projects
        selected_ids = project_ids[:2]
        save_showcase_projects(user_id, selected_ids)

        # Get showcase projects
        showcase = get_showcase_projects(user_id)

        assert len(showcase) == 2

        # Check projects are in correct order
        assert showcase[0]["id"] == selected_ids[0]
        assert showcase[1]["id"] == selected_ids[1]

        # Check project details
        for project in showcase:
            assert "project_name" in project
            assert "primary_language" in project
            assert "languages" in project
            assert "frameworks" in project
            assert project["languages"]  # Should have language data

    def test_get_showcase_projects_empty(self):
        """Test getting showcase projects when none selected."""
        user_id = "test_user_showcase_empty"

        showcase = get_showcase_projects(user_id)
        assert showcase == []


class TestCurationIntegration:
    """Test integration of curation features."""

    def test_full_curation_workflow(self, sample_projects):
        """Test complete curation workflow."""
        project_ids = sample_projects
        user_id = f"test_user_workflow_{project_ids[0]}"

        # 1. Correct chronology
        new_date = "2024-04-01T10:00:00"
        success = save_chronology_correction(project_ids[0], user_id, last_commit_date=new_date)
        assert success

        # 2. Set comparison attributes
        attributes = ["total_files", "has_tests", "has_ci_cd"]
        success = save_comparison_attributes(user_id, attributes)
        assert success

        # 3. Select showcase projects
        showcase_ids = project_ids[:2]
        success = save_showcase_projects(user_id, showcase_ids)
        assert success

        # 4. Verify all settings
        settings = get_user_curation_settings(user_id)
        assert set(settings.comparison_attributes) == set(attributes)
        assert set(settings.showcase_project_ids) == set(showcase_ids)

        # 5. Verify corrected chronology
        projects = get_user_projects(user_id)
        corrected_project = next(p for p in projects if p["id"] == project_ids[0])
        assert corrected_project["effective_last_commit_date"] == new_date

        # 6. Verify showcase projects
        showcase = get_showcase_projects(user_id)
        assert len(showcase) == 2
        assert {p["id"] for p in showcase} == set(showcase_ids)

    def test_multiple_users_isolation(self, sample_projects):
        """Test that different users' curation settings are isolated."""
        project_ids = sample_projects
        user1_id = f"user1_isolation_{project_ids[0]}"
        user2_id = f"user2_isolation_{project_ids[0]}"

        # User 1 settings
        save_comparison_attributes(user1_id, ["total_files", "has_tests"])
        save_showcase_projects(user1_id, [project_ids[0]])

        # User 2 settings
        save_comparison_attributes(user2_id, ["primary_language", "has_ci_cd"])
        save_showcase_projects(user2_id, [project_ids[1], project_ids[2]])

        # Verify isolation
        settings1 = get_user_curation_settings(user1_id)
        settings2 = get_user_curation_settings(user2_id)

        assert set(settings1.comparison_attributes) == {"total_files", "has_tests"}
        assert settings1.showcase_project_ids == [project_ids[0]]

        assert set(settings2.comparison_attributes) == {"primary_language", "has_ci_cd"}
        assert set(settings2.showcase_project_ids) == {project_ids[1], project_ids[2]}


class TestErrorHandling:
    """Test error handling in curation functionality."""

    def test_database_error_handling(self, tmp_path, monkeypatch):
        """Test handling of database errors."""
        # Point to non-existent directory to trigger errors
        bad_db_path = tmp_path / "nonexistent" / "bad.db"
        monkeypatch.setenv("ANALYSIS_DB_PATH", str(bad_db_path))

        # These operations should fail gracefully
        user_id = "test_user"

        # Should handle database connection errors
        try:
            settings = get_user_curation_settings(user_id)
            # If it doesn't error, it should return defaults
            assert settings.user_id == user_id
            assert settings.comparison_attributes == DEFAULT_COMPARISON_ATTRIBUTES
        except Exception:
            # Database errors are acceptable in this test
            pass

    def test_attribute_descriptions_coverage(self):
        """Test that all default attributes have descriptions."""
        for attr in DEFAULT_COMPARISON_ATTRIBUTES:
            assert attr in ATTRIBUTE_DESCRIPTIONS, f"Missing description for {attr}"
            assert ATTRIBUTE_DESCRIPTIONS[attr], f"Empty description for {attr}"


if __name__ == "__main__":
    pytest.main([__file__])
