"""Tests for the analysis database helper module."""

from __future__ import annotations

import json

import pytest

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