import sys
from datetime import datetime
from pathlib import Path

import pytest

# Make `src` directory importable as project root (like other tests)
SRC = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SRC))

from backend import analysis_database as db
from backend.analysis.chronology import (get_projects_timeline,
                                         get_skills_timeline)


def iso(ts: datetime) -> str:
    return ts.isoformat(timespec="seconds")


@pytest.fixture(autouse=True)
def reset_db_tmp(tmp_path, monkeypatch):
    # point DB to a temp file and init
    test_db = tmp_path / "analysis.db"
    monkeypatch.setenv("ANALYSIS_DB_PATH", str(test_db))
    db.set_db_path(test_db)
    db.reset_db()
    yield


def seed_analysis(payload):
    return db.record_analysis("non_llm", payload)


def make_payload(ts: str, projects):
    return {
        "analysis_metadata": {
            "zip_file": "dummy.zip",
            "analysis_timestamp": ts,
            "total_projects": len(projects),
        },
        "summary": {
            "total_files": sum(p.get("total_files", 0) for p in projects),
            "total_size_bytes": 0,
            "total_size_mb": 0,
            "languages_used": list({p.get("primary_language") for p in projects if p.get("primary_language")}),
            "frameworks_used": [],
        },
        "projects": projects,
    }


def test_projects_timeline_orders_by_commit_date():
    ts1 = iso(datetime(2024, 1, 10, 12, 0, 0))
    ts2 = iso(datetime(2024, 2, 5, 9, 30, 0))

    # Commit dates are different from analysis timestamps
    commit1 = iso(datetime(2023, 12, 15, 10, 0, 0))  # Earlier commit
    commit2 = iso(datetime(2024, 1, 20, 14, 0, 0))  # Later commit

    modified1 = iso(datetime(2023, 12, 16, 11, 0, 0))  # File modification times
    modified2 = iso(datetime(2024, 1, 21, 15, 0, 0))

    p1 = {
        "project_name": "Alpha",
        "primary_language": "Python",
        "total_files": 10,
        "has_tests": True,
        "has_ci_cd": False,
        "has_docker": None,
        "last_commit_date": commit1,
        "last_modified_date": modified1,
        "languages": {"Python": 8},
        "frameworks": ["FastAPI"],
    }

    p2 = {
        "project_name": "Beta",
        "primary_language": "JavaScript",
        "total_files": 5,
        "has_tests": False,
        "has_ci_cd": True,
        "has_docker": True,
        "last_commit_date": commit2,
        "last_modified_date": modified2,
        "languages": {"JavaScript": 5},
        "frameworks": ["React"],
    }

    # Seed with ts2 first (later analysis), but it should be ordered by commit date
    seed_analysis(make_payload(ts2, [p2]))
    seed_analysis(make_payload(ts1, [p1]))

    timeline = get_projects_timeline()
    # Should be ordered by commit date, not analysis timestamp
    assert [t.project_name for t in timeline] == ["Alpha", "Beta"]
    assert timeline[0].last_commit_date == commit1
    assert timeline[1].last_commit_date == commit2


def test_skills_timeline_collects_unique_per_analysis():
    ts1 = iso(datetime(2024, 3, 1, 8, 0, 0))
    ts2 = iso(datetime(2024, 3, 15, 18, 45, 0))

    commit1 = iso(datetime(2024, 2, 20, 10, 0, 0))
    commit2 = iso(datetime(2024, 3, 10, 14, 0, 0))

    pA = {
        "project_name": "A",
        "primary_language": "Python",
        "languages": {"Python": 3, "Markdown": 1},
        "frameworks": ["Django"],
        "total_files": 4,
        "last_commit_date": commit1,
    }
    pB = {
        "project_name": "B",
        "primary_language": "JavaScript",
        "languages": {"JavaScript": 5},
        "frameworks": ["React"],
        "total_files": 5,
        "last_commit_date": commit2,
    }

    seed_analysis(make_payload(ts1, [pA]))
    seed_analysis(make_payload(ts2, [pB]))

    skills = get_skills_timeline()
    # Skills are now ordered by commit date
    assert [s.date for s in skills] == [commit1, commit2]
    assert set(skills[0].skills["languages"]) == {"Markdown", "Python"}
    assert set(skills[0].skills["frameworks"]) == {"Django"}
    assert set(skills[1].skills["languages"]) == {"JavaScript"}
    assert set(skills[1].skills["frameworks"]) == {"React"}


def test_projects_timeline_fallback_to_analysis_timestamp():
    """Test that timeline falls back to analysis_timestamp when no commit/modified dates exist"""
    ts1 = iso(datetime(2024, 4, 1, 10, 0, 0))
    ts2 = iso(datetime(2024, 4, 15, 14, 0, 0))

    p1 = {
        "project_name": "NoGitProject",
        "primary_language": "Python",
        "total_files": 5,
        "has_tests": False,
        "last_commit_date": None,
        "last_modified_date": None,  # Also no modified date
        "languages": {"Python": 5},
        "frameworks": [],
    }

    p2 = {
        "project_name": "AnotherNoGitProject",
        "primary_language": "JavaScript",
        "total_files": 3,
        "has_tests": True,
        "last_commit_date": None,
        "last_modified_date": None,
        "languages": {"JavaScript": 3},
        "frameworks": ["Vue"],
    }

    # Seed in reverse order - should be sorted by analysis_timestamp
    seed_analysis(make_payload(ts2, [p2]))
    seed_analysis(make_payload(ts1, [p1]))

    timeline = get_projects_timeline()
    assert [t.project_name for t in timeline] == ["NoGitProject", "AnotherNoGitProject"]
    assert timeline[0].last_commit_date is None
    assert timeline[0].last_modified_date is None
    assert timeline[1].last_commit_date is None
    assert timeline[1].last_modified_date is None
    assert timeline[0].analysis_timestamp == ts1
    assert timeline[1].analysis_timestamp == ts2


def test_projects_timeline_mixed_commit_dates():
    """Test ordering when some projects have commit dates and others don't"""
    ts1 = iso(datetime(2024, 5, 1, 10, 0, 0))
    ts2 = iso(datetime(2024, 5, 15, 14, 0, 0))

    commit1 = iso(datetime(2024, 4, 10, 12, 0, 0))  # Earlier than both analysis timestamps
    modified2 = iso(datetime(2024, 4, 20, 15, 0, 0))  # Between commit1 and ts1

    p1 = {
        "project_name": "WithGit",
        "primary_language": "Python",
        "total_files": 10,
        "last_commit_date": commit1,
        "last_modified_date": iso(datetime(2024, 4, 11, 12, 0, 0)),
        "languages": {"Python": 10},
        "frameworks": [],
    }

    p2 = {
        "project_name": "WithoutGit",
        "primary_language": "JavaScript",
        "total_files": 5,
        "last_commit_date": None,
        "last_modified_date": modified2,  # Has modified date though
        "languages": {"JavaScript": 5},
        "frameworks": [],
    }

    seed_analysis(make_payload(ts1, [p1]))
    seed_analysis(make_payload(ts2, [p2]))

    timeline = get_projects_timeline()
    # Should be: commit1 (April 10) < modified2 (April 20)
    assert [t.project_name for t in timeline] == ["WithGit", "WithoutGit"]
    assert timeline[0].last_commit_date == commit1
    assert timeline[1].last_commit_date is None
    assert timeline[1].last_modified_date == modified2


def test_projects_timeline_fallback_to_modified_date():
    """Test that timeline uses modified_date when commit_date is not available"""
    ts1 = iso(datetime(2024, 6, 1, 10, 0, 0))
    ts2 = iso(datetime(2024, 6, 15, 14, 0, 0))

    # Modified dates in different order than analysis dates
    modified1 = iso(datetime(2024, 5, 25, 12, 0, 0))  # Earlier
    modified2 = iso(datetime(2024, 5, 20, 10, 0, 0))  # Even earlier

    p1 = {
        "project_name": "ProjectA",
        "primary_language": "Python",
        "total_files": 8,
        "last_commit_date": None,  # No git
        "last_modified_date": modified1,
        "languages": {"Python": 8},
        "frameworks": ["Flask"],
    }

    p2 = {
        "project_name": "ProjectB",
        "primary_language": "Go",
        "total_files": 6,
        "last_commit_date": None,  # No git
        "last_modified_date": modified2,
        "languages": {"Go": 6},
        "frameworks": [],
    }

    # Seed in one order
    seed_analysis(make_payload(ts1, [p1]))
    seed_analysis(make_payload(ts2, [p2]))

    timeline = get_projects_timeline()
    # Should be ordered by modified_date: modified2 (May 20) < modified1 (May 25)
    assert [t.project_name for t in timeline] == ["ProjectB", "ProjectA"]
    assert timeline[0].last_modified_date == modified2
    assert timeline[1].last_modified_date == modified1
    assert timeline[0].last_commit_date is None
    assert timeline[1].last_commit_date is None
