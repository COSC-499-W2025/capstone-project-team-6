from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .. import analysis_database as db


@dataclass
class ProjectEntry:
    project_name: str
    analysis_timestamp: str
    primary_language: Optional[str]
    total_files: Optional[int]
    has_tests: Optional[bool]
    has_ci_cd: Optional[bool]
    has_docker: Optional[bool]


def _row_to_bool(value: Optional[int]) -> Optional[bool]:
    if value is None:
        return None
    return bool(value)


def get_projects_timeline() -> List[ProjectEntry]:
    """Return projects across all analyses ordered by analysis timestamp.

    Uses `analyses.analysis_timestamp` for ordering (ISO string expected).
    """
    with db.get_connection() as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        rows = conn.execute(
            """
            SELECT p.project_name,
                   a.analysis_timestamp,
                   p.primary_language,
                   p.total_files,
                   p.has_tests,
                   p.has_ci_cd,
                   p.has_docker
            FROM projects p
            JOIN analyses a ON a.id = p.analysis_id
            ORDER BY a.analysis_timestamp ASC, p.id ASC
            """
        ).fetchall()

    return [
        ProjectEntry(
            project_name=row["project_name"],
            analysis_timestamp=row["analysis_timestamp"],
            primary_language=row["primary_language"],
            total_files=row["total_files"],
            has_tests=_row_to_bool(row["has_tests"]),
            has_ci_cd=_row_to_bool(row["has_ci_cd"]),
            has_docker=_row_to_bool(row["has_docker"]),
        )
        for row in rows
    ]


@dataclass
class SkillEntry:
    date: str
    skills: Dict[str, List[str]]  # {"languages": [...], "frameworks": [...]}


def get_skills_timeline() -> List[SkillEntry]:
    """Aggregate languages and frameworks over time based on analyses.

    Each entry represents an analysis date with unique languages/frameworks
    discovered across its projects.
    """
    with db.get_connection() as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        analyses = conn.execute("SELECT id, analysis_timestamp FROM analyses ORDER BY analysis_timestamp ASC").fetchall()

        timeline: List[SkillEntry] = []
        for arow in analyses:
            aid = arow["id"]
            ts = arow["analysis_timestamp"]

            langs = conn.execute(
                """
                SELECT DISTINCT language
                FROM project_languages pl
                JOIN projects p ON p.id = pl.project_id
                WHERE p.analysis_id = ?
                ORDER BY language ASC
                """,
                (aid,),
            ).fetchall()

            frameworks = conn.execute(
                """
                SELECT DISTINCT framework
                FROM project_frameworks pf
                JOIN projects p ON p.id = pf.project_id
                WHERE p.analysis_id = ?
                ORDER BY framework ASC
                """,
                (aid,),
            ).fetchall()

            timeline.append(
                SkillEntry(
                    date=ts,
                    skills={
                        "languages": [r["language"] for r in langs],
                        "frameworks": [r["framework"] for r in frameworks],
                    },
                )
            )

    return timeline
