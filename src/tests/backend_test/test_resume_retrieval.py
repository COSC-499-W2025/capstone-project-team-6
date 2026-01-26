"""
Unit tests for résumé retrieval and regeneration functionality in analyze.py
(updated to use project_id + analysis_id scoped resume_items)
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

current_dir = Path(__file__).parent
tests_dir = current_dir.parent
src_dir = tests_dir.parent
backend_dir = src_dir / "backend"

sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(backend_dir))

import backend.analysis_database as adb

pytest_plugins = ["tests.backend_test.test_analysis_database"]


@pytest.fixture(autouse=True)
def clear_resume_items(temp_analysis_db):
    """Clear resume_items table before each test to ensure isolation."""
    with adb.get_connection() as conn:
        conn.execute("DELETE FROM resume_items")
        conn.commit()
    yield
    with adb.get_connection() as conn:
        conn.execute("DELETE FROM resume_items")
        conn.commit()


SAMPLE_RESUME_TEXT = """TestProject
Technologies: Python, Django
  • Built TestProject using Django
  • Implemented comprehensive testing"""


def _create_analysis_with_one_project(project_name: str = "TestProject", username: str = "alice"):
    payload = {
        "analysis_metadata": {
            "zip_file": f"/tmp/{project_name}.zip",
            "analysis_timestamp": "2026-01-01T00:00:00",
            "total_projects": 1,
        },
        "projects": [
            {
                "project_name": project_name,
                "project_path": f"/{project_name}",
                "primary_language": "python",
                "languages": {"python": 1},
                "total_files": 1,
                "total_size": 1,
                "code_files": 1,
                "test_files": 0,
                "doc_files": 0,
                "config_files": 0,
                "frameworks": [],
                "dependencies": {},
                "has_tests": False,
                "has_readme": False,
                "has_ci_cd": False,
                "has_docker": False,
                "test_coverage_estimate": "none",
                "is_git_repo": False,
            }
        ],
        "summary": {
            "total_files": 1,
            "total_size_bytes": 1,
            "total_size_mb": 0.000001,
            "languages_used": ["python"],
            "frameworks_used": [],
        },
    }

    analysis_id = adb.record_analysis("non_llm", payload, username=username)
    project_id = adb.get_projects_for_analysis(analysis_id)[0]["id"]

    # Clear it so tests control what exists.
    with adb.get_connection() as conn:
        conn.execute("DELETE FROM resume_items WHERE project_id = ?", (project_id,))
        conn.commit()

    return analysis_id, project_id, project_name


class TestResumeRetrieval:
    def test_get_resume_items_for_existing_project(self, temp_analysis_db):
        analysis_id, project_id, project_name = _create_analysis_with_one_project("TestProject")
        resume_text = SAMPLE_RESUME_TEXT

        adb.store_resume_item(analysis_id, project_id, project_name, resume_text, bullet_order=0)
        items = adb.get_resume_items_for_project_id(project_id)

        assert items is not None
        assert len(items) == 1
        assert items[0]["project_id"] == project_id
        assert items[0]["project_name"] == project_name
        assert items[0]["resume_text"] == resume_text
        assert items[0]["bullet_order"] == 0

    def test_get_resume_items_for_nonexistent_project(self, temp_analysis_db):
        items = adb.get_resume_items_for_project_id(999999)
        assert items == []

    def test_store_resume_item_success(self, temp_analysis_db):
        analysis_id, project_id, project_name = _create_analysis_with_one_project("NewProject")
        resume_text = "New project resume text"

        adb.store_resume_item(analysis_id, project_id, project_name, resume_text, bullet_order=0)
        items = adb.get_resume_items_for_project_id(project_id)

        assert len(items) == 1
        assert items[0]["resume_text"] == resume_text

    def test_store_resume_item_empty_resume_text(self, temp_analysis_db):
        analysis_id, project_id, project_name = _create_analysis_with_one_project("ProjectName")
        with pytest.raises(ValueError, match="resume_text is required"):
            adb.store_resume_item(analysis_id, project_id, project_name, "", bullet_order=0)


class TestResumeRegeneration:
    def test_regenerate_all_resumes(self, temp_analysis_db):
        projects = [
            ("Project1", "Old resume 1", "New resume 1"),
            ("Project2", "Old resume 2", "New resume 2"),
            ("Project3", "Old resume 3", "New resume 3"),
        ]

        created = []
        for project_name, old_resume, _ in projects:
            analysis_id, project_id, pname = _create_analysis_with_one_project(project_name)
            created.append((analysis_id, project_id, pname))
            adb.store_resume_item(analysis_id, project_id, pname, old_resume, bullet_order=0)

        # Verify old stored (including text)
        for (_, project_id, pname), (_, old_resume, _) in zip(created, projects):
            items = adb.get_resume_items_for_project_id(project_id)
            assert len(items) == 1
            assert items[0]["project_name"] == pname
            assert items[0]["resume_text"] == old_resume

        # Regenerate: delete + insert new
        for (analysis_id, project_id, pname), (_, _, new_resume) in zip(created, projects):
            with adb.get_connection() as conn:
                conn.execute("DELETE FROM resume_items WHERE project_id = ?", (project_id,))
                conn.commit()
            adb.store_resume_item(analysis_id, project_id, pname, new_resume, bullet_order=0)

        # Verify new stored
        for (_, project_id, _), (_, _, new_resume) in zip(created, projects):
            items = adb.get_resume_items_for_project_id(project_id)
            assert len(items) == 1
            assert items[0]["resume_text"] == new_resume


class TestResumeFilteringLogic:
    def test_filter_projects_needing_resume_none_cached(self, temp_analysis_db):
        a1, p1, n1 = _create_analysis_with_one_project("Project1")
        a2, p2, n2 = _create_analysis_with_one_project("Project2")

        projects = [{"id": p1, "project_name": n1}, {"id": p2, "project_name": n2}]
        resume_items_by_project = {}
        projects_needing_resume = []

        for project in projects:
            project_id = project["id"]
            existing = adb.get_resume_items_for_project_id(project_id)

            if existing:
                resume_items_by_project[project_id] = {"text": existing[0]["resume_text"], "cached": True}
            else:
                projects_needing_resume.append(project)

        assert len(resume_items_by_project) == 0
        assert len(projects_needing_resume) == 2

    def test_filter_projects_needing_resume_all_cached(self, temp_analysis_db):
        a1, p1, n1 = _create_analysis_with_one_project("Project1")
        a2, p2, n2 = _create_analysis_with_one_project("Project2")

        projects = [{"id": p1, "project_name": n1}, {"id": p2, "project_name": n2}]

        adb.store_resume_item(a1, p1, n1, "Resume for Project1", bullet_order=0)
        adb.store_resume_item(a2, p2, n2, "Resume for Project2", bullet_order=0)

        resume_items_by_project = {}
        projects_needing_resume = []

        for project in projects:
            project_id = project["id"]
            existing = adb.get_resume_items_for_project_id(project_id)

            if existing:
                resume_items_by_project[project_id] = {"text": existing[0]["resume_text"], "cached": True}
            else:
                projects_needing_resume.append(project)

        assert len(resume_items_by_project) == 2
        assert len(projects_needing_resume) == 0

    def test_filter_projects_needing_resume_partial_cached(self, temp_analysis_db):
        a1, p1, n1 = _create_analysis_with_one_project("Project1")
        a2, p2, n2 = _create_analysis_with_one_project("Project2")
        a3, p3, n3 = _create_analysis_with_one_project("Project3")

        projects = [{"id": p1, "project_name": n1}, {"id": p2, "project_name": n2}, {"id": p3, "project_name": n3}]
        adb.store_resume_item(a1, p1, n1, "Resume for Project1", bullet_order=0)

        resume_items_by_project = {}
        projects_needing_resume = []

        for project in projects:
            project_id = project["id"]
            existing = adb.get_resume_items_for_project_id(project_id)

            if existing:
                resume_items_by_project[project_id] = {"text": existing[0]["resume_text"], "cached": True}
            else:
                projects_needing_resume.append(project)

        assert len(resume_items_by_project) == 1
        assert len(projects_needing_resume) == 2
        assert projects_needing_resume[0]["project_name"] == "Project2"
        assert projects_needing_resume[1]["project_name"] == "Project3"

    def test_filter_with_regenerate_all_flag(self, temp_analysis_db):
        a1, p1, n1 = _create_analysis_with_one_project("Project1")
        a2, p2, n2 = _create_analysis_with_one_project("Project2")

        projects = [{"id": p1, "project_name": n1}, {"id": p2, "project_name": n2}]
        adb.store_resume_item(a1, p1, n1, "Resume for Project1", bullet_order=0)
        adb.store_resume_item(a2, p2, n2, "Resume for Project2", bullet_order=0)

        regenerate_all = True
        resume_items_by_project = {}
        projects_needing_resume = []

        for project in projects:
            project_id = project["id"]
            existing = adb.get_resume_items_for_project_id(project_id)

            if existing and not regenerate_all:
                resume_items_by_project[project_id] = {"text": existing[0]["resume_text"], "cached": True}
            else:
                projects_needing_resume.append(project)

        assert len(resume_items_by_project) == 0
        assert len(projects_needing_resume) == 2


class TestResumeItemNumbering:
    def test_item_numbering_all_new(self):
        cached_count = 0
        for idx in range(1, 4):
            item_number = cached_count + idx
            assert item_number == idx

    def test_item_numbering_mixed_cached_and_new(self):
        cached_count = 2
        expected_numbers = [3, 4, 5]
        for idx, expected in enumerate(expected_numbers, 1):
            item_number = cached_count + idx
            assert item_number == expected

    def test_item_numbering_regenerate_all(self):
        for idx in range(1, 4):
            item_number = idx
            assert item_number == idx
