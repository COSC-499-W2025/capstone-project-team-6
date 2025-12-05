import sys
from datetime import datetime
from pathlib import Path

import pytest

# Make `src` directory importable as project root (like other tests)
SRC = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SRC))

from backend import analysis_database as db
from backend.analysis.chronology import get_projects_timeline, get_skills_timeline


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


def test_projects_timeline_orders_by_analysis_timestamp():
    ts1 = iso(datetime(2024, 1, 10, 12, 0, 0))
    ts2 = iso(datetime(2024, 2, 5, 9, 30, 0))

    p1 = {
        "project_name": "Alpha",
        "primary_language": "Python",
        "total_files": 10,
        "has_tests": True,
        "has_ci_cd": False,
        "has_docker": None,
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
        "languages": {"JavaScript": 5},
        "frameworks": ["React"],
    }

    seed_analysis(make_payload(ts2, [p2]))
    seed_analysis(make_payload(ts1, [p1]))

    timeline = get_projects_timeline()
    assert [t.project_name for t in timeline] == ["Alpha", "Beta"]
    assert timeline[0].analysis_timestamp == ts1
    assert timeline[1].analysis_timestamp == ts2


def test_skills_timeline_collects_unique_per_analysis():
    ts1 = iso(datetime(2024, 3, 1, 8, 0, 0))
    ts2 = iso(datetime(2024, 3, 15, 18, 45, 0))

    pA = {
        "project_name": "A",
        "primary_language": "Python",
        "languages": {"Python": 3, "Markdown": 1},
        "frameworks": ["Django"],
        "total_files": 4,
    }
    pB = {
        "project_name": "B",
        "primary_language": "JavaScript",
        "languages": {"JavaScript": 5},
        "frameworks": ["React"],
        "total_files": 5,
    }

    seed_analysis(make_payload(ts1, [pA]))
    seed_analysis(make_payload(ts2, [pB]))

    skills = get_skills_timeline()
    assert [s.date for s in skills] == [ts1, ts2]
    assert set(skills[0].skills["languages"]) == {"Markdown", "Python"}
    assert set(skills[0].skills["frameworks"]) == {"Django"}
    assert set(skills[1].skills["languages"]) == {"JavaScript"}
    assert set(skills[1].skills["frameworks"]) == {"React"}
