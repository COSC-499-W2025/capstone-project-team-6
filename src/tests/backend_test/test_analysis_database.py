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
