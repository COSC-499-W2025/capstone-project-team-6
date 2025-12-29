"""Tests for the analysis database helper module."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Add src directory (and project root) to path for imports
SRC_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_ROOT = SRC_DIR.parent
for p in (SRC_DIR, PROJECT_ROOT):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

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
            "target_user_email": "john@example.com",
            "target_user_stats": {
                "email": "john@example.com",
                "name": "John Doe",
                "commit_count": 45,
                "percentage": 37.5,
                "last_commit_date": "2025-10-01T00:00:00",
            },
            "contribution_volume": {"john@example.com": 120},
            "blame_summary": {"john@example.com": 100},
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
    assert project["target_user_email"] == "john@example.com"
    assert project["target_user_name"] == "John Doe"
    assert project["target_user_commits"] == 45
    assert project["target_user_commit_pct"] == pytest.approx(37.5)
    assert project["target_user_lines_changed"] == 120
    assert project["target_user_surviving_lines"] == 100
    assert project["target_user_last_commit"] == "2025-10-01T00:00:00"

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


def test_git_extended_fields_persisted(temp_analysis_db):
    payload = {
        "analysis_metadata": {
            "zip_file": "git.zip",
            "analysis_timestamp": "2025-12-25T15:00:00",
            "total_projects": 1,
        },
        "projects": [
            {
                "project_name": "gitproj",
                "project_path": "/gitproj",
                "primary_language": "python",
                "languages": {"python": 5},
                "total_files": 5,
                "total_size": 1024,
                "code_files": 5,
                "test_files": 0,
                "doc_files": 0,
                "config_files": 0,
                "frameworks": [],
                "dependencies": {},
                "has_tests": False,
                "has_readme": True,
                "has_ci_cd": False,
                "has_docker": False,
                "is_git_repo": True,
                "total_commits": 10,
                "primary_branch": "main",
                "total_branches": 3,
                "has_remote": True,
                "project_start_date": "2024-01-10T12:00:00+00:00",
                "project_end_date": "2024-02-15T12:00:00+00:00",
                "project_active_days": 37,
                "target_user_email": "alice@example.com",
                "target_user_stats": {
                    "email": "alice@example.com",
                    "name": "Alice",
                    "commit_count": 3,
                    "percentage": 75.0,
                    "last_commit_date": "2024-02-14T12:00:00+00:00",
                },
                "remote_urls": ["https://example.com/repo.git"],
                "code_ownership": [
                    {
                        "path": "a.py",
                        "dominant_author": "Alice",
                        "dominant_email": "alice@example.com",
                        "ownership_percentage": 75.0,
                        "total_lines": 40,
                    }
                ],
                "blame_summary": {"alice@example.com": 40, "bob@example.com": 10},
                "language_breakdown": {
                    "alice@example.com": {"Python": 50},
                    "bob@example.com": {"Python": 10},
                },
                "semantic_summary": {
                    "alice@example.com": {
                        "name": "Alice",
                        "trivial_commits": 1,
                        "substantial_commits": 2,
                        "total_lines_changed": 50,
                    }
                },
                "contribution_volume": {"alice@example.com": 50, "bob@example.com": 10},
                "activity_breakdown": {
                    "alice@example.com": {"code": 40, "test": 5, "docs": 5, "design": 1},
                    "bob@example.com": {"code": 10},
                },
                "directory_depth": 2,
            }
        ],
    }

    analysis_id = adb.record_analysis("non_llm", payload)
    projects = adb.get_projects_for_analysis(analysis_id)
    assert len(projects) == 1
    project = projects[0]
    assert project["primary_branch"] == "main"
    assert project["total_branches"] == 3
    assert project["has_remote"] == 1
    assert project["project_start_date"] == "2024-01-10T12:00:00+00:00"
    assert project["project_end_date"] == "2024-02-15T12:00:00+00:00"
    assert project["project_active_days"] == 37
    assert project["target_user_email"] == "alice@example.com"
    assert project["target_user_name"] == "Alice"
    assert project["target_user_commits"] == 3
    assert project["target_user_commit_pct"] == pytest.approx(75.0)
    assert project["target_user_lines_changed"] == 50
    assert project["target_user_surviving_lines"] == 40
    assert project["target_user_last_commit"] == "2024-02-14T12:00:00+00:00"

    with adb.get_connection() as conn:
        remotes = conn.execute(
            "SELECT url FROM project_remote_urls WHERE project_id = ?", (project["id"],)
        ).fetchall()
        assert {row["url"] for row in remotes} == {"https://example.com/repo.git"}

        ownership = conn.execute(
            """
            SELECT path, dominant_author, dominant_email, ownership_percentage, total_lines
            FROM project_code_ownership WHERE project_id = ?
            """,
            (project["id"],),
        ).fetchall()
        assert len(ownership) == 1
        assert ownership[0]["path"] == "a.py"
        assert ownership[0]["dominant_email"] == "alice@example.com"
        assert ownership[0]["ownership_percentage"] == pytest.approx(75.0)
        assert ownership[0]["total_lines"] == 40

        blame = conn.execute(
            "SELECT email, surviving_lines FROM project_blame_summary WHERE project_id = ?",
            (project["id"],),
        ).fetchall()
        assert {(row["email"], row["surviving_lines"]) for row in blame} == {
            ("alice@example.com", 40),
            ("bob@example.com", 10),
        }

        lang_bd = conn.execute(
            """
            SELECT email, language, lines_changed
            FROM project_language_breakdown WHERE project_id = ?
            """,
            (project["id"],),
        ).fetchall()
        assert {(row["email"], row["language"], row["lines_changed"]) for row in lang_bd} == {
            ("alice@example.com", "Python", 50),
            ("bob@example.com", "Python", 10),
        }

        semantic = conn.execute(
            """
            SELECT email, name, trivial_commits, substantial_commits, total_lines_changed
            FROM project_semantic_summary WHERE project_id = ?
            """,
            (project["id"],),
        ).fetchall()
        assert len(semantic) == 1
        row = semantic[0]
        assert row["email"] == "alice@example.com"
        assert row["trivial_commits"] == 1
        assert row["substantial_commits"] == 2
        assert row["total_lines_changed"] == 50

        volume = conn.execute(
            "SELECT email, lines_changed FROM project_contribution_volume WHERE project_id = ?",
            (project["id"],),
        ).fetchall()
        assert {(row["email"], row["lines_changed"]) for row in volume} == {
            ("alice@example.com", 50),
            ("bob@example.com", 10),
        }

        activity = conn.execute(
            """
            SELECT email, activity_type, lines_changed
            FROM project_activity_breakdown
            WHERE project_id = ?
            """,
            (project["id"],),
        ).fetchall()
        assert {
            (row["email"], row["activity_type"], row["lines_changed"]) for row in activity
        } == {
            ("alice@example.com", "code", 40),
            ("alice@example.com", "test", 5),
            ("alice@example.com", "docs", 5),
            ("alice@example.com", "design", 1),
            ("bob@example.com", "code", 10),
        }
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
