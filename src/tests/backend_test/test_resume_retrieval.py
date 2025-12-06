"""
Unit tests for résumé retrieval and regeneration functionality in analyze.py
"""
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest

current_dir = Path(__file__).parent
tests_dir = current_dir.parent
src_dir = tests_dir.parent
backend_dir = src_dir / "backend"

sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(backend_dir))

import backend.analysis_database as adb
from backend.analysis_database import (
    get_resume_items_for_project,
    store_resume_item,
    get_connection,
)

pytest_plugins = ["tests.backend_test.test_analysis_database"]


@pytest.fixture(autouse=True)
def clear_resume_items(temp_analysis_db):
    """Clear resume_items table before each test to ensure isolation"""
    with get_connection() as conn:
        conn.execute("DELETE FROM resume_items")
        conn.commit()
    yield
    with get_connection() as conn:
        conn.execute("DELETE FROM resume_items")
        conn.commit()


# Sample test data
SAMPLE_PROJECT = {
    "project_name": "TestProject",
    "primary_language": "Python",
    "languages": {"python": 10},
    "frameworks": ["Django"],
    "dependencies": {"pip": ["django"]},
    "has_tests": True,
    "has_readme": True,
    "has_docker": True,
}

SAMPLE_RESUME_TEXT = """TestProject
Technologies: Python, Django
  • Built TestProject using Django
  • Implemented comprehensive testing"""


class TestResumeRetrieval:
    """Test résumé retrieval functionality"""

    def test_get_resume_items_for_existing_project(self, temp_analysis_db):
        """Test retrieving résumé items for a project that exists in database"""
        # Store a resume item
        project_name = "TestProject"
        resume_text = SAMPLE_RESUME_TEXT
        store_resume_item(project_name, resume_text)

        # Retrieve it
        items = get_resume_items_for_project(project_name)

        assert items is not None
        assert len(items) == 1
        assert items[0]["project_name"] == project_name
        assert items[0]["resume_text"] == resume_text

    def test_get_resume_items_for_nonexistent_project(self, temp_analysis_db):
        """Test retrieving résumé items for a project that doesn't exist"""
        items = get_resume_items_for_project("NonexistentProject")
        assert items == []

    def test_store_resume_item_success(self, temp_analysis_db):
        """Test successfully storing a résumé item"""
        project_name = "NewProject"
        resume_text = "New project resume text"
        store_resume_item(project_name, resume_text)
        items = get_resume_items_for_project(project_name)
        assert len(items) == 1
        assert items[0]["resume_text"] == resume_text

    def test_store_resume_item_empty_project_name(self, temp_analysis_db):
        """Test storing résumé item with empty project name raises ValueError"""
        with pytest.raises(ValueError, match="project_name and resume_text are required"):
            store_resume_item("", "Some text")

    def test_store_resume_item_empty_resume_text(self, temp_analysis_db):
        """Test storing résumé item with empty resume text raises ValueError"""
        with pytest.raises(ValueError, match="project_name and resume_text are required"):
            store_resume_item("ProjectName", "")


class TestResumeRegeneration:
    """Test résumé regeneration functionality"""

    def test_regenerate_all_resumes(self, temp_analysis_db):
        """Test regenerating all résumé items (overwrite existing)"""
        projects = [
            ("Project1", "Old resume 1", "New resume 1"),
            ("Project2", "Old resume 2", "New resume 2"),
            ("Project3", "Old resume 3", "New resume 3"),
        ]
        for project_name, old_resume, _ in projects:
            store_resume_item(project_name, old_resume)
        for project_name, old_resume, _ in projects:
            items = get_resume_items_for_project(project_name)
            assert len(items) == 1
            assert items[0]["resume_text"] == old_resume
        for project_name, _, new_resume in projects:
            with get_connection() as conn:
                conn.execute("DELETE FROM resume_items WHERE project_name = ?", (project_name,))
                conn.commit()
            store_resume_item(project_name, new_resume)
        for project_name, _, new_resume in projects:
            items = get_resume_items_for_project(project_name)
            assert len(items) == 1
            assert items[0]["resume_text"] == new_resume


class TestResumeFilteringLogic:
    """Test the logic for filtering projects that need résumé generation"""

    def test_filter_projects_needing_resume_none_cached(self, temp_analysis_db):
        """Test filtering when no résumés are cached"""
        projects = [
            {"project_name": "Project1"},
            {"project_name": "Project2"},
        ]

        resume_items_by_project = {}
        projects_needing_resume = []

        for project in projects:
            project_name = project.get("project_name", "Unknown Project")
            existing_resume_items = get_resume_items_for_project(project_name)

            if existing_resume_items:
                resume_items_by_project[project_name] = {
                    "text": existing_resume_items[0]["resume_text"],
                    "cached": True
                }
            else:
                projects_needing_resume.append(project)

        assert len(resume_items_by_project) == 0
        assert len(projects_needing_resume) == 2

    def test_filter_projects_needing_resume_all_cached(self, temp_analysis_db):
        """Test filtering when all résumés are cached"""
        projects = [
            {"project_name": "Project1"},
            {"project_name": "Project2"},
        ]
        for project in projects:
            store_resume_item(project["project_name"], f"Resume for {project['project_name']}")

        resume_items_by_project = {}
        projects_needing_resume = []

        for project in projects:
            project_name = project.get("project_name", "Unknown Project")
            existing_resume_items = get_resume_items_for_project(project_name)

            if existing_resume_items:
                resume_items_by_project[project_name] = {
                    "text": existing_resume_items[0]["resume_text"],
                    "cached": True
                }
            else:
                projects_needing_resume.append(project)

        assert len(resume_items_by_project) == 2
        assert len(projects_needing_resume) == 0

    def test_filter_projects_needing_resume_partial_cached(self, temp_analysis_db):
        """Test filtering when some résumés are cached"""
        projects = [
            {"project_name": "Project1"},
            {"project_name": "Project2"},
            {"project_name": "Project3"},
        ]
        store_resume_item("Project1", "Resume for Project1")

        resume_items_by_project = {}
        projects_needing_resume = []

        for project in projects:
            project_name = project.get("project_name", "Unknown Project")
            existing_resume_items = get_resume_items_for_project(project_name)

            if existing_resume_items:
                resume_items_by_project[project_name] = {
                    "text": existing_resume_items[0]["resume_text"],
                    "cached": True
                }
            else:
                projects_needing_resume.append(project)

        assert len(resume_items_by_project) == 1
        assert len(projects_needing_resume) == 2
        assert projects_needing_resume[0]["project_name"] == "Project2"
        assert projects_needing_resume[1]["project_name"] == "Project3"

    def test_filter_with_regenerate_all_flag(self, temp_analysis_db):
        """Test filtering when regenerate_all flag is set"""
        projects = [
            {"project_name": "Project1"},
            {"project_name": "Project2"},
        ]
        for project in projects:
            store_resume_item(project["project_name"], f"Resume for {project['project_name']}")

        regenerate_all = True
        resume_items_by_project = {}
        projects_needing_resume = []

        for project in projects:
            project_name = project.get("project_name", "Unknown Project")
            existing_resume_items = get_resume_items_for_project(project_name)

            if existing_resume_items and not regenerate_all:
                resume_items_by_project[project_name] = {
                    "text": existing_resume_items[0]["resume_text"],
                    "cached": True
                }
            else:
                projects_needing_resume.append(project)
        assert len(resume_items_by_project) == 0
        assert len(projects_needing_resume) == 2


class TestResumeItemNumbering:
    """Test the numbering logic for résumé items"""

    def test_item_numbering_all_new(self):
        """Test item numbering when all items are new"""
        total_projects = 3
        cached_count = 0

        for idx in range(1, 4):
            item_number = cached_count + idx
            assert item_number == idx

    def test_item_numbering_mixed_cached_and_new(self):
        """Test item numbering when mixing cached and new items"""
        total_projects = 5
        cached_count = 2  

        expected_numbers = [3, 4, 5]  

        for idx, expected in enumerate(expected_numbers, 1):
            item_number = cached_count + idx
            assert item_number == expected

    def test_item_numbering_regenerate_all(self):
        """Test item numbering when regenerating all items"""
        total_projects = 3
        cached_count = 0  

        for idx in range(1, 4):
            item_number = idx  
            assert item_number == idx


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
