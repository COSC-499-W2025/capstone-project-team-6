from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .. import analysis_database as db
from .portfolio_item_generator import generate_portfolio_item


@dataclass
class ProjectEntry:
    project_name: str
    analysis_timestamp: str
    last_commit_date: Optional[str]
    last_modified_date: Optional[str]
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
    """Return projects across all analyses ordered by last commit/modified date (with fallback to analysis timestamp).

    Uses three-tier fallback for ordering:
    1. `projects.last_commit_date` (git commit timestamp)
    2. `projects.last_modified_date` (file modification timestamp from ZIP)
    3. `analyses.analysis_timestamp` (when analysis was performed)
    """
    with db.get_connection() as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        rows = conn.execute(
            """
            SELECT p.project_name,
                   a.analysis_timestamp,
                   p.last_commit_date,
                   p.last_modified_date,
                   p.primary_language,
                   p.total_files,
                   p.has_tests,
                   p.has_ci_cd,
                   p.has_docker
            FROM projects p
            JOIN analyses a ON a.id = p.analysis_id
            ORDER BY COALESCE(p.last_commit_date, p.last_modified_date, a.analysis_timestamp) ASC, p.id ASC
            """
        ).fetchall()

    return [
        ProjectEntry(
            project_name=row["project_name"],
            analysis_timestamp=row["analysis_timestamp"],
            last_commit_date=row["last_commit_date"],
            last_modified_date=row["last_modified_date"],
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
    skills: Dict[str, List[str]]  # {"languages": [...], "frameworks": [...], "detailed_skills": [...]}


def get_skills_timeline() -> List[SkillEntry]:
    """Aggregate languages, frameworks, and detailed skills over time based on commit/modified date.

    Each entry represents a project's commit date (or file modified date, or analysis date as fallback)
    with unique languages/frameworks and detailed skills (from portfolio items) discovered across its projects.
    """
    with db.get_connection() as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        # Get analyses ordered by last commit/modified date (with fallback to analysis_timestamp)
        analyses = conn.execute(
            """
            SELECT a.id,
                   a.raw_json,
                   COALESCE(
                       (SELECT p.last_commit_date
                        FROM projects p
                        WHERE p.analysis_id = a.id
                        AND p.last_commit_date IS NOT NULL
                        ORDER BY p.last_commit_date DESC
                        LIMIT 1),
                       (SELECT p.last_modified_date
                        FROM projects p
                        WHERE p.analysis_id = a.id
                        AND p.last_modified_date IS NOT NULL
                        ORDER BY p.last_modified_date DESC
                        LIMIT 1),
                       a.analysis_timestamp
                   ) as date_key,
                   a.analysis_timestamp
            FROM analyses a
            ORDER BY date_key ASC
            """
        ).fetchall()

        timeline: List[SkillEntry] = []
        for arow in analyses:
            aid = arow["id"]
            ts = arow["date_key"]
            raw_json_str = arow["raw_json"]

            # Get languages and frameworks from database
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

            # Extract detailed skills from portfolio items
            detailed_skills_set = set()
            try:
                if raw_json_str:
                    analysis_data = json.loads(raw_json_str)
                    projects = analysis_data.get("projects", [])
                    
                    for project in projects:
                        try:
                            portfolio_item = generate_portfolio_item(project)
                            skills_exercised = portfolio_item.get("skills_exercised", [])
                            detailed_skills_set.update(skills_exercised)
                        except Exception:
                            # If portfolio item generation fails for a project, skip it
                            # but continue with other projects
                            continue
            except (json.JSONDecodeError, KeyError, TypeError):
                # If JSON parsing fails, continue without detailed skills
                pass

            timeline.append(
                SkillEntry(
                    date=ts,
                    skills={
                        "languages": [r["language"] for r in langs],
                        "frameworks": [r["framework"] for r in frameworks],
                        "detailed_skills": sorted(list(detailed_skills_set)),
                    },
                )
            )

    return timeline
