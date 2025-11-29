"""Tests for the analysis database helper module."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Add src directory to path for imports
SRC_DIR = Path(__file__).resolve().parent.parent.parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from src.backend import analysis_database as adb

SAMPLE_PAYLOAD = {
    "analysis_metadata": {
        "zip_file": "path/to/project.zip",
        "analysis_timestamp": "2025-11-03T12:34:56",
        "total_projects": 1,
    },
    "projects": [
        {
            "project_name": "my_project",
            "project_path": "/workspace/my_project",
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
            "contributors": [
                {
                    "name": "John Doe",
                    "email": "john@example.com",
                    "commits": 45,
                    "files_touched": 12,
                }
            ],
            "total_commits": 120,
            "directory_depth": 5,
            "largest_file": {
                "path": "src/main.py",
                "size": 50_000,
                "size_mb": 0.05,
            },
        }
    ],
    "summary": {
        "total_files": 25,
        "total_size_bytes": 524_288,
        "total_size_mb": 0.5,
        "languages_used": ["python", "javascript"],
        "frameworks_used": ["Django", "React"],
    },
}


@pytest.fixture
def temp_analysis_db(tmp_path):
    previous = adb.set_db_path(tmp_path / "analysis.db")
    adb.reset_db()
    yield
    adb.set_db_path(previous)


def test_record_analysis_persists_all_entities(temp_analysis_db):
    analysis_id = adb.record_analysis("llm", SAMPLE_PAYLOAD, analysis_uuid="uuid-1234")

    analysis_row = adb.get_analysis(analysis_id)
    assert analysis_row is not None
    assert analysis_row["analysis_uuid"] == "uuid-1234"
    assert analysis_row["analysis_type"] == "llm"
    assert analysis_row["total_projects"] == 1
    assert json.loads(analysis_row["raw_json"])["projects"][0]["project_name"] == "my_project"
    assert json.loads(analysis_row["summary_languages"]) == ["python", "javascript"]
    assert json.loads(analysis_row["summary_frameworks"]) == ["Django", "React"]
    assert analysis_row["summary_total_size_mb"] == pytest.approx(0.5)

    projects = adb.get_projects_for_analysis(analysis_id)
    assert len(projects) == 1
    project = projects[0]
    assert project["project_name"] == "my_project"
    assert project["total_files"] == 25
    assert project["has_tests"] == 1
    assert project["is_git_repo"] == 1

    with adb.get_connection() as conn:
        languages = conn.execute(
            "SELECT language, file_count FROM project_languages WHERE project_id = ?",
            (project["id"],),
        ).fetchall()
        assert {(row["language"], row["file_count"]) for row in languages} == {
            ("python", 15),
            ("javascript", 3),
        }

        frameworks = conn.execute(
            "SELECT framework FROM project_frameworks WHERE project_id = ?",
            (project["id"],),
        ).fetchall()
        assert {row["framework"] for row in frameworks} == {"Django", "React"}

        dependencies = conn.execute(
            "SELECT ecosystem, dependency FROM project_dependencies WHERE project_id = ?",
            (project["id"],),
        ).fetchall()
        assert {tuple(row) for row in dependencies} == {
            ("python", "django"),
            ("python", "requests"),
            ("python", "pytest"),
            ("javascript", "react"),
            ("javascript", "react-dom"),
        }

        contributors = conn.execute(
            """
            SELECT name, email, commits, files_touched
            FROM project_contributors
            WHERE project_id = ?
            """,
            (project["id"],),
        ).fetchall()
        assert contributors[0]["email"] == "john@example.com"
        assert contributors[0]["commits"] == 45

        largest = conn.execute(
            "SELECT path, size_bytes, size_mb FROM project_largest_file WHERE project_id = ?",
            (project["id"],),
        ).fetchone()
        assert largest["path"] == "src/main.py"
        assert largest["size_bytes"] == 50_000
        assert largest["size_mb"] == pytest.approx(0.05)


def test_record_analysis_validates_input(temp_analysis_db):
    with pytest.raises(ValueError, match="analysis_type"):
        adb.record_analysis("unexpected", SAMPLE_PAYLOAD)

    minimal_payload = {"analysis_metadata": {"zip_file": "x.zip", "analysis_timestamp": "now"}}
    analysis_id = adb.record_analysis("non_llm", minimal_payload)
    analysis_row = adb.get_analysis(analysis_id)
    assert analysis_row["total_projects"] == 0


def test_project_analysis_stored_in_db(temp_analysis_db):
    """Test that project analysis from analyze.py is correctly stored in the database."""
    analysis_payload = {
        "analysis_metadata": {
            "zip_file": "/path/to/test_project.zip",
            "analysis_timestamp": "2025-11-21T10:30:00",
            "total_projects": 2,
        },
        "projects": [
            {
                "project_name": "backend",
                "project_path": "backend",
                "primary_language": "python",
                "languages": {"python": 25, "yaml": 2},
                "total_files": 30,
                "total_size": 1_048_576,
                "code_files": 25,
                "test_files": 3,
                "doc_files": 1,
                "config_files": 1,
                "frameworks": ["Flask", "SQLAlchemy"],
                "dependencies": {
                    "python": ["flask", "sqlalchemy", "pytest", "black"],
                },
                "has_tests": True,
                "has_readme": True,
                "has_ci_cd": False,
                "has_docker": True,
                "test_coverage_estimate": "high",
                "is_git_repo": True,
                "total_commits": 250,
                "directory_depth": 4,
            },
            {
                "project_name": "frontend",
                "project_path": "frontend",
                "primary_language": "javascript",
                "languages": {"javascript": 40, "css": 10, "html": 5},
                "total_files": 60,
                "total_size": 2_097_152,
                "code_files": 55,
                "test_files": 4,
                "doc_files": 1,
                "config_files": 2,
                "frameworks": ["React", "Vite"],
                "dependencies": {
                    "javascript": ["react", "react-dom", "vite"],
                },
                "has_tests": True,
                "has_readme": True,
                "has_ci_cd": True,
                "has_docker": False,
                "test_coverage_estimate": "medium",
                "is_git_repo": False,
                "total_commits": 0,
                "directory_depth": 3,
            },
        ],
        "summary": {
            "total_files": 90,
            "total_size_bytes": 3_145_728,
            "total_size_mb": 3.0,
            "languages_used": ["python", "javascript", "yaml", "css", "html"],
            "frameworks_used": ["Flask", "SQLAlchemy", "React", "Vite"],
        },
    }

    analysis_id = adb.record_analysis("non_llm", analysis_payload)
    analysis_row = adb.get_analysis(analysis_id)
    assert analysis_row is not None
    assert analysis_row["analysis_type"] == "non_llm"
    assert analysis_row["zip_file"] == "/path/to/test_project.zip"
    assert analysis_row["total_projects"] == 2
    assert analysis_row["summary_total_files"] == 90
    assert analysis_row["summary_total_size_mb"] == pytest.approx(3.0)
    projects = adb.get_projects_for_analysis(analysis_id)
    assert len(projects) == 2
    backend = next(p for p in projects if p["project_name"] == "backend")
    assert backend["primary_language"] == "python"
    assert backend["total_files"] == 30
    assert backend["code_files"] == 25
    assert backend["test_files"] == 3
    assert backend["has_tests"] == 1
    assert backend["has_docker"] == 1
    assert backend["test_coverage_estimate"] == "high"
    frontend = next(p for p in projects if p["project_name"] == "frontend")
    assert frontend["primary_language"] == "javascript"
    assert frontend["total_files"] == 60
    assert frontend["has_ci_cd"] == 1
    assert frontend["has_docker"] == 0
    with adb.get_connection() as conn:
        backend_langs = conn.execute(
            "SELECT language, file_count FROM project_languages WHERE project_id = ? ORDER BY language",
            (backend["id"],),
        ).fetchall()
        assert {(row["language"], row["file_count"]) for row in backend_langs} == {
            ("python", 25),
            ("yaml", 2),
        }

        frontend_langs = conn.execute(
            "SELECT language, file_count FROM project_languages WHERE project_id = ? ORDER BY language",
            (frontend["id"],),
        ).fetchall()
        assert len(frontend_langs) == 3
        assert {row["language"] for row in frontend_langs} == {"javascript", "css", "html"}
        backend_frameworks = conn.execute(
            "SELECT framework FROM project_frameworks WHERE project_id = ?",
            (backend["id"],),
        ).fetchall()
        assert {row["framework"] for row in backend_frameworks} == {"Flask", "SQLAlchemy"}
        backend_deps = conn.execute(
            "SELECT dependency FROM project_dependencies WHERE project_id = ? AND ecosystem = 'python'",
            (backend["id"],),
        ).fetchall()
        assert {row["dependency"] for row in backend_deps} == {"flask", "sqlalchemy", "pytest", "black"}


def test_get_analysis_by_zip_file(temp_analysis_db):
    """Test retrieving analysis by zip file path."""
    zip_file_path = "/path/to/test_project.zip"
    
    analysis_id = adb.record_analysis("non_llm", SAMPLE_PAYLOAD)
    analysis = adb.get_analysis_by_zip_file(SAMPLE_PAYLOAD["analysis_metadata"]["zip_file"])
    
    assert analysis is not None
    assert analysis["id"] == analysis_id
    assert analysis["zip_file"] == "path/to/project.zip"
    assert analysis["analysis_type"] == "non_llm"
    assert analysis["total_projects"] == 1


def test_get_analysis_by_zip_file_not_found(temp_analysis_db):
    """Test retrieving analysis by zip file when it doesn't exist."""
    analysis = adb.get_analysis_by_zip_file("/nonexistent/path.zip")
    assert analysis is None

def test_get_analysis_report(temp_analysis_db):
    """Test retrieving full analysis report by zip file."""
    # Store an analysis
    analysis_id = adb.record_analysis("non_llm", SAMPLE_PAYLOAD)
    
    # Retrieve report
    report = adb.get_analysis_report(SAMPLE_PAYLOAD["analysis_metadata"]["zip_file"])
    
    assert report is not None
    assert report["analysis_metadata"]["zip_file"] == "path/to/project.zip"
    assert len(report["projects"]) == 1
    assert report["projects"][0]["project_name"] == "my_project"
    assert "summary" in report


def test_get_analysis_report_not_found(temp_analysis_db):
    """Test retrieving analysis report when it doesn't exist."""
    report = adb.get_analysis_report("/nonexistent/path.zip")
    assert report is None


def test_store_and_get_resume_items(temp_analysis_db):
    """Test storing and retrieving resume items."""
    project_name = "test_project"
    resume_text = "Test Project\nTechnologies: Python, Django\n  • Built amazing features"
    
    adb.store_resume_item(project_name, resume_text)
    
    items = adb.get_resume_items_for_project(project_name)
    
    assert len(items) == 1
    assert items[0]["project_name"] == project_name
    assert items[0]["resume_text"] == resume_text


def test_get_resume_items_for_project_not_found(temp_analysis_db):
    """Test retrieving resume items for a project that doesn't exist."""
    items = adb.get_resume_items_for_project("nonexistent_project")
    assert len(items) == 0

def test_store_resume_item_validates_input(temp_analysis_db):
    """Test that store_resume_item validates required inputs."""
    with pytest.raises(ValueError, match="project_name and resume_text are required"):
        adb.store_resume_item("", "some text")
    
    with pytest.raises(ValueError, match="project_name and resume_text are required"):
        adb.store_resume_item("project", "")
    
    with pytest.raises(ValueError, match="project_name and resume_text are required"):
        adb.store_resume_item(None, "some text")


def test_count_analyses_by_zip_file(temp_analysis_db):
    """Test counting analyses for a zip file."""
    zip_file = "/path/to/test.zip"    
    assert adb.count_analyses_by_zip_file(zip_file) == 0
    
    payload1 = {
        "analysis_metadata": {
            "zip_file": zip_file,
            "analysis_timestamp": "2025-01-01T10:00:00",
            "total_projects": 1,
        },
        "projects": [],
        "summary": {},
    }
    adb.record_analysis("non_llm", payload1)
    assert adb.count_analyses_by_zip_file(zip_file) == 1    
    payload2 = {
        "analysis_metadata": {
            "zip_file": zip_file,
            "analysis_timestamp": "2025-01-02T10:00:00",
            "total_projects": 1,
        },
        "projects": [],
        "summary": {},
    }
    adb.record_analysis("llm", payload2)
    assert adb.count_analyses_by_zip_file(zip_file) == 2
    
    # Different zip file should have 0
    assert adb.count_analyses_by_zip_file("/different/path.zip") == 0


def test_count_analyses_by_zip_file_nonexistent(temp_analysis_db):
    """Test counting analyses for a zip file that doesn't exist."""
    assert adb.count_analyses_by_zip_file("/nonexistent/path.zip") == 0


def test_delete_analyses_by_zip_file_single_analysis(temp_analysis_db):
    """Test deleting a single analysis for a zip file."""
    zip_file = "/path/to/test.zip"
    
    # Create an analysis with projects and related data
    payload = {
        "analysis_metadata": {
            "zip_file": zip_file,
            "analysis_timestamp": "2025-01-01T10:00:00",
            "total_projects": 1,
        },
        "projects": [
            {
                "project_name": "test_project",
                "project_path": "/test",
                "primary_language": "python",
                "languages": {"python": 10},
                "total_files": 10,
                "frameworks": ["Django"],
                "dependencies": {"python": ["django"]},
                "has_tests": True,
            }
        ],
        "summary": {},
    }
    analysis_id = adb.record_analysis("non_llm", payload)
    
    assert adb.count_analyses_by_zip_file(zip_file) == 1
    assert adb.get_analysis(analysis_id) is not None
    
    deleted_count = adb.delete_analyses_by_zip_file(zip_file)
    assert deleted_count == 1
    
    assert adb.count_analyses_by_zip_file(zip_file) == 0
    assert adb.get_analysis(analysis_id) is None


def test_delete_analyses_by_zip_file_multiple_analyses(temp_analysis_db):
    zip_file = "/path/to/test.zip"    
    for i in range(3):
        payload = {
            "analysis_metadata": {
                "zip_file": zip_file,
                "analysis_timestamp": f"2025-01-0{i+1}T10:00:00",
                "total_projects": 1,
            },
            "projects": [],
            "summary": {},
        }
        adb.record_analysis("non_llm", payload)
    
    assert adb.count_analyses_by_zip_file(zip_file) == 3
    
    deleted_count = adb.delete_analyses_by_zip_file(zip_file)
    assert deleted_count == 3
    
    assert adb.count_analyses_by_zip_file(zip_file) == 0


def test_delete_analyses_by_zip_file_cascade_deletion(temp_analysis_db):
    """Test that deleting analyses cascades to related data (projects, languages, etc.)."""
    zip_file = "/path/to/test.zip"
    
    # Create analysis with full project data
    payload = {
        "analysis_metadata": {
            "zip_file": zip_file,
            "analysis_timestamp": "2025-01-01T10:00:00",
            "total_projects": 1,
        },
        "projects": [
            {
                "project_name": "test_project",
                "project_path": "/test",
                "primary_language": "python",
                "languages": {"python": 10, "javascript": 5},
                "total_files": 15,
                "frameworks": ["Django", "React"],
                "dependencies": {
                    "python": ["django", "requests"],
                    "javascript": ["react"],
                },
                "contributors": [
                    {
                        "name": "John Doe",
                        "email": "john@example.com",
                        "commits": 10,
                        "files_touched": 5,
                    }
                ],
                "largest_file": {
                    "path": "src/main.py",
                    "size": 1000,
                    "size_mb": 0.001,
                },
                "has_tests": True,
            }
        ],
        "summary": {},
    }
    analysis_id = adb.record_analysis("non_llm", payload)
    
    projects = adb.get_projects_for_analysis(analysis_id)
    assert len(projects) == 1
    project_id = projects[0]["id"]
    
    with adb.get_connection() as conn:
        languages = conn.execute(
            "SELECT COUNT(*) as count FROM project_languages WHERE project_id = ?",
            (project_id,),
        ).fetchone()
        assert languages["count"] == 2
        
        frameworks = conn.execute(
            "SELECT COUNT(*) as count FROM project_frameworks WHERE project_id = ?",
            (project_id,),
        ).fetchone()
        assert frameworks["count"] == 2
        
        dependencies = conn.execute(
            "SELECT COUNT(*) as count FROM project_dependencies WHERE project_id = ?",
            (project_id,),
        ).fetchone()
        assert dependencies["count"] == 3
        
        contributors = conn.execute(
            "SELECT COUNT(*) as count FROM project_contributors WHERE project_id = ?",
            (project_id,),
        ).fetchone()
        assert contributors["count"] == 1
        
        largest_file = conn.execute(
            "SELECT COUNT(*) as count FROM project_largest_file WHERE project_id = ?",
            (project_id,),
        ).fetchone()
        assert largest_file["count"] == 1
    
    deleted_count = adb.delete_analyses_by_zip_file(zip_file)
    assert deleted_count == 1
    
    with adb.get_connection() as conn:
        projects_remaining = conn.execute(
            "SELECT COUNT(*) as count FROM projects WHERE analysis_id = ?",
            (analysis_id,),
        ).fetchone()
        assert projects_remaining["count"] == 0
        
        languages_remaining = conn.execute(
            "SELECT COUNT(*) as count FROM project_languages WHERE project_id = ?",
            (project_id,),
        ).fetchone()
        assert languages_remaining["count"] == 0
        
        frameworks_remaining = conn.execute(
            "SELECT COUNT(*) as count FROM project_frameworks WHERE project_id = ?",
            (project_id,),
        ).fetchone()
        assert frameworks_remaining["count"] == 0
        
        dependencies_remaining = conn.execute(
            "SELECT COUNT(*) as count FROM project_dependencies WHERE project_id = ?",
            (project_id,),
        ).fetchone()
        assert dependencies_remaining["count"] == 0
        
        contributors_remaining = conn.execute(
            "SELECT COUNT(*) as count FROM project_contributors WHERE project_id = ?",
            (project_id,),
        ).fetchone()
        assert contributors_remaining["count"] == 0
        
        largest_file_remaining = conn.execute(
            "SELECT COUNT(*) as count FROM project_largest_file WHERE project_id = ?",
            (project_id,),
        ).fetchone()
        assert largest_file_remaining["count"] == 0


def test_delete_analyses_preserves_resume_items(temp_analysis_db):
    """Test that deleting analyses does NOT affect resume items."""
    zip_file = "/path/to/test.zip"
    project_name = "shared_project"
    
    resume_text = "Shared Project\nTechnologies: Python, Django\n  • Built amazing features"
    adb.store_resume_item(project_name, resume_text)
    
    payload = {
        "analysis_metadata": {
            "zip_file": zip_file,
            "analysis_timestamp": "2025-01-01T10:00:00",
            "total_projects": 1,
        },
        "projects": [
            {
                "project_name": project_name,
                "project_path": "/test",
                "primary_language": "python",
                "total_files": 10,
            }
        ],
        "summary": {},
    }
    analysis_id = adb.record_analysis("non_llm", payload)
    
    resume_items = adb.get_resume_items_for_project(project_name)
    assert len(resume_items) == 1
    assert resume_items[0]["resume_text"] == resume_text
    
    deleted_count = adb.delete_analyses_by_zip_file(zip_file)
    assert deleted_count == 1
    
    assert adb.get_analysis(analysis_id) is None    
    resume_items_after = adb.get_resume_items_for_project(project_name)
    assert len(resume_items_after) == 1
    assert resume_items_after[0]["resume_text"] == resume_text
    assert resume_items_after[0]["project_name"] == project_name



def test_get_all_analyses_by_zip_file(temp_analysis_db):
    """Test retrieving all analyses (not just most recent) for a zip file."""
    zip_file = "/path/to/test.zip"
    
    # Create multiple analyses
    timestamps = [
        "2025-01-01T10:00:00",
        "2025-01-02T10:00:00",
        "2025-01-03T10:00:00",
    ]
    analysis_ids = []
    
    for i, timestamp in enumerate(timestamps):
        payload = {
            "analysis_metadata": {
                "zip_file": zip_file,
                "analysis_timestamp": timestamp,
                "total_projects": 1,
            },
            "projects": [],
            "summary": {},
        }
        analysis_id = adb.record_analysis("non_llm", payload)
        analysis_ids.append(analysis_id)
    
    all_analyses = adb.get_all_analyses_by_zip_file(zip_file)
    assert len(all_analyses) == 3
    
    retrieved_ids = {analysis["id"] for analysis in all_analyses}
    assert retrieved_ids == set(analysis_ids)
    created_ats = [analysis["created_at"] for analysis in all_analyses]
    assert created_ats == sorted(created_ats, reverse=True)

    adb.delete_analyses_by_zip_file(zip_file)    
    all_analyses_after = adb.get_all_analyses_by_zip_file(zip_file)
    assert len(all_analyses_after) == 0
