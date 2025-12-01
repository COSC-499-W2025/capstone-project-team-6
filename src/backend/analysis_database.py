"""SQLite helpers for storing analysis results."""

from __future__ import annotations

import json
import os
import sqlite3
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

VALID_ANALYSIS_TYPES = {"llm", "non_llm"}


def _default_db_path() -> Path:
    return Path(__file__).resolve().parent.parent / "myapp.db"


def _resolve_db_path() -> Path:
    env_path = os.getenv("ANALYSIS_DB_PATH")
    if env_path:
        return Path(env_path).expanduser().resolve()
    return _default_db_path()


_DB_PATH = _resolve_db_path()


def get_db_path() -> Path:
    return _DB_PATH


def set_db_path(path: Path | str) -> Path:
    global _DB_PATH
    previous = _DB_PATH
    _DB_PATH = Path(path).expanduser().resolve()
    return previous


def _ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


@contextmanager
def get_connection() -> sqlite3.Connection:
    db_path = get_db_path()
    _ensure_parent_dir(db_path)
    conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    with get_connection() as conn:
        conn.execute("PRAGMA foreign_keys = ON;")

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_uuid TEXT NOT NULL UNIQUE,
                analysis_type TEXT NOT NULL CHECK(analysis_type IN ('llm', 'non_llm')),
                zip_file TEXT NOT NULL,
                analysis_timestamp TEXT NOT NULL,
                total_projects INTEGER NOT NULL,
                raw_json TEXT NOT NULL,
                summary_total_files INTEGER,
                summary_total_size_bytes INTEGER,
                summary_total_size_mb REAL,
                summary_languages TEXT,
                summary_frameworks TEXT,
                llm_summary TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_id INTEGER NOT NULL REFERENCES analyses(id) ON DELETE CASCADE,
                project_name TEXT NOT NULL,
                project_path TEXT,
                primary_language TEXT,
                total_files INTEGER,
                total_size INTEGER,
                code_files INTEGER,
                test_files INTEGER,
                doc_files INTEGER,
                config_files INTEGER,
                has_tests INTEGER CHECK(has_tests IN (0, 1)),
                has_readme INTEGER CHECK(has_readme IN (0, 1)),
                has_ci_cd INTEGER CHECK(has_ci_cd IN (0, 1)),
                has_docker INTEGER CHECK(has_docker IN (0, 1)),
                test_coverage_estimate TEXT,
                is_git_repo INTEGER CHECK(is_git_repo IN (0, 1)),
                total_commits INTEGER,
                directory_depth INTEGER
            );
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS project_largest_file (
                project_id INTEGER PRIMARY KEY REFERENCES projects(id) ON DELETE CASCADE,
                path TEXT NOT NULL,
                size_bytes INTEGER NOT NULL,
                size_mb REAL NOT NULL
            );
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS project_languages (
                project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                language TEXT NOT NULL,
                file_count INTEGER,
                PRIMARY KEY (project_id, language)
            );
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS project_frameworks (
                project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                framework TEXT NOT NULL,
                PRIMARY KEY (project_id, framework)
            );
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS project_dependencies (
                project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                ecosystem TEXT NOT NULL,
                dependency TEXT NOT NULL,
                PRIMARY KEY (project_id, ecosystem, dependency)
            );
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS project_contributors (
                project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                name TEXT,
                email TEXT,
                commits INTEGER,
                files_touched INTEGER,
                PRIMARY KEY (project_id, email)
            );
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS resume_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_name TEXT NOT NULL,
                resume_text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        conn.commit()


def reset_db() -> None:
    db_path = get_db_path()
    if db_path.exists():
        db_path.unlink()
    init_db()


def initialize() -> None:
    init_db()


def _serialize_array(values: Optional[Iterable[str]]) -> Optional[str]:
    if not values:
        return None
    return json.dumps(list(values), separators=(",", ":"))


def _boolean_to_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    return int(bool(value))


def _extract_summary(summary: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "summary_total_files": summary.get("total_files"),
        "summary_total_size_bytes": summary.get("total_size_bytes"),
        "summary_total_size_mb": summary.get("total_size_mb"),
        "summary_languages": _serialize_array(summary.get("languages_used")),
        "summary_frameworks": _serialize_array(summary.get("frameworks_used")),
    }


def record_analysis(
    analysis_type: str,
    payload: Dict[str, Any],
    *,
    analysis_uuid: Optional[str] = None,
) -> int:
    if analysis_type not in VALID_ANALYSIS_TYPES:
        raise ValueError(f"analysis_type must be one of {VALID_ANALYSIS_TYPES}")

    if not payload:
        raise ValueError("payload cannot be empty")

    metadata = payload.get("analysis_metadata") or {}
    summary = payload.get("summary") or {}
    projects = payload.get("projects") or []

    if not metadata:
        raise ValueError("payload must include analysis_metadata")

    if "zip_file" not in metadata or "analysis_timestamp" not in metadata:
        raise ValueError("analysis_metadata requires zip_file and analysis_timestamp")

    analysis_uuid = analysis_uuid or str(uuid.uuid4())

    serialized_payload = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    summary_fields = _extract_summary(summary)

    with get_connection() as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        cursor = conn.execute(
            """
            INSERT INTO analyses (
                analysis_uuid,
                analysis_type,
                zip_file,
                analysis_timestamp,
                total_projects,
                raw_json,
                summary_total_files,
                summary_total_size_bytes,
                summary_total_size_mb,
                summary_languages,
                summary_frameworks,
                llm_summary
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                analysis_uuid,
                analysis_type,
                metadata["zip_file"],
                metadata["analysis_timestamp"],
                metadata.get("total_projects", len(projects)),
                serialized_payload,
                summary_fields["summary_total_files"],
                summary_fields["summary_total_size_bytes"],
                summary_fields["summary_total_size_mb"],
                summary_fields["summary_languages"],
                summary_fields["summary_frameworks"],
                payload.get("llm_summary"),
            ),
        )
        analysis_id = cursor.lastrowid

        for project in projects:
            project_cursor = conn.execute(
                """
                INSERT INTO projects (
                    analysis_id,
                    project_name,
                    project_path,
                    primary_language,
                    total_files,
                    total_size,
                    code_files,
                    test_files,
                    doc_files,
                    config_files,
                    has_tests,
                    has_readme,
                    has_ci_cd,
                    has_docker,
                    test_coverage_estimate,
                    is_git_repo,
                    total_commits,
                    directory_depth
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    analysis_id,
                    project.get("project_name"),
                    project.get("project_path"),
                    project.get("primary_language"),
                    project.get("total_files"),
                    project.get("total_size"),
                    project.get("code_files"),
                    project.get("test_files"),
                    project.get("doc_files"),
                    project.get("config_files"),
                    _boolean_to_int(project.get("has_tests")),
                    _boolean_to_int(project.get("has_readme")),
                    _boolean_to_int(project.get("has_ci_cd")),
                    _boolean_to_int(project.get("has_docker")),
                    project.get("test_coverage_estimate"),
                    _boolean_to_int(project.get("is_git_repo")),
                    project.get("total_commits"),
                    project.get("directory_depth"),
                ),
            )
            project_id = project_cursor.lastrowid

            languages = project.get("languages") or {}
            for language, file_count in languages.items():
                conn.execute(
                    """
                    INSERT INTO project_languages (project_id, language, file_count)
                    VALUES (?, ?, ?)
                    """,
                    (project_id, language, file_count),
                )

            frameworks = project.get("frameworks") or []
            for framework in frameworks:
                conn.execute(
                    """
                    INSERT INTO project_frameworks (project_id, framework)
                    VALUES (?, ?)
                    """,
                    (project_id, framework),
                )

            dependencies = project.get("dependencies") or {}
            for ecosystem, deps in dependencies.items():
                for dependency in deps or []:
                    conn.execute(
                        """
                        INSERT INTO project_dependencies (project_id, ecosystem, dependency)
                        VALUES (?, ?, ?)
                        """,
                        (project_id, ecosystem, dependency),
                    )

            contributors = project.get("contributors") or []
            for contributor in contributors:
                conn.execute(
                    """
                    INSERT INTO project_contributors (
                        project_id,
                        name,
                        email,
                        commits,
                        files_touched
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        project_id,
                        contributor.get("name"),
                        contributor.get("email"),
                        contributor.get("commits"),
                        contributor.get("files_touched"),
                    ),
                )

            largest_file = project.get("largest_file")
            if largest_file:
                conn.execute(
                    """
                    INSERT INTO project_largest_file (project_id, path, size_bytes, size_mb)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        project_id,
                        largest_file.get("path"),
                        largest_file.get("size"),
                        largest_file.get("size_mb"),
                    ),
                )

        conn.commit()

    return analysis_id


def get_analysis(analysis_id: int) -> Optional[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM analyses WHERE id = ?",
            (analysis_id,),
        ).fetchone()


def get_projects_for_analysis(analysis_id: int) -> List[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM projects WHERE analysis_id = ? ORDER BY id",
            (analysis_id,),
        ).fetchall()


def get_analysis_by_zip_file(zip_file: str) -> Optional[sqlite3.Row]:
    """Get the most recent analysis for a given zip file path."""
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT * FROM analyses 
            WHERE zip_file = ? 
            ORDER BY created_at DESC 
            LIMIT 1
            """,
            (zip_file,),
        ).fetchone()


def get_analysis_report(zip_file: str) -> Optional[Dict[str, Any]]:
    """Retrieve the full analysis report (JSON) for a given zip file path."""
    analysis = get_analysis_by_zip_file(zip_file)
    if not analysis:
        return None

    try:
        return json.loads(analysis["raw_json"])
    except (json.JSONDecodeError, KeyError):
        return None


def store_resume_item(project_name: str, resume_text: str) -> None:
    if not project_name or not resume_text:
        raise ValueError("project_name and resume_text are required")

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO resume_items (project_name, resume_text)
            VALUES (?, ?)
            """,
            (project_name, resume_text),
        )
        conn.commit()


def get_all_resume_items() -> List[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT id, project_name, resume_text, created_at
            FROM resume_items
            ORDER BY created_at DESC
            """
        ).fetchall()


def get_resume_items_for_project(project_name: str) -> List[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT id, project_name, resume_text, created_at
            FROM resume_items
            WHERE project_name = ?
            ORDER BY created_at DESC
            """,
            (project_name,),
        ).fetchall()


def delete_resume_item(item_id: int) -> None:
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM resume_items WHERE id = ?",
            (item_id,),
        )
        conn.commit()


def clear_resume_items() -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM resume_items")
        conn.commit()
