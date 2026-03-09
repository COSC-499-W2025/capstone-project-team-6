"""SQLite helpers for storing analysis results."""

from __future__ import annotations

import json
import os
import sqlite3
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Union

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


def set_db_path(path: Union[Path, str]) -> Path:
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
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    with get_connection() as conn:
        conn.execute("PRAGMA foreign_keys = ON;")

        # Ensure a minimal users table exists so the FK on analyses.username is valid
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        # Per-user profile info (used for resume personal info autofill)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_profile (
                username TEXT PRIMARY KEY REFERENCES users(username) ON DELETE CASCADE,
                personal_info_json TEXT,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS uploads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL REFERENCES users(username),
                zip_path TEXT, -- will be cleared after analysis + deletion
                original_filename TEXT,
                status TEXT NOT NULL DEFAULT 'uploaded'
                    CHECK(status IN ('uploaded','analyzing','done','failed')),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

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
                username TEXT REFERENCES users(username),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        # Ensure the username column exists for installations created before this field was added.
        existing_columns = {row["name"] for row in conn.execute("PRAGMA table_info(analyses)")}
        if "username" not in existing_columns:
            conn.execute("ALTER TABLE analyses ADD COLUMN username TEXT REFERENCES users(username);")
            conn.commit()

        existing_columns = {row["name"] for row in conn.execute("PRAGMA table_info(analyses)")}
        if "upload_id" not in existing_columns:
            conn.execute("ALTER TABLE analyses ADD COLUMN upload_id INTEGER REFERENCES uploads(id);")
            conn.commit()

        existing_columns = {row["name"] for row in conn.execute("PRAGMA table_info(analyses)")}
        if "zip_file_hash" not in existing_columns:
            conn.execute("ALTER TABLE analyses ADD COLUMN zip_file_hash TEXT;")
            conn.commit()
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_analyses_hash_user "
            "ON analyses (zip_file_hash, username) WHERE zip_file_hash IS NOT NULL;"
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_id INTEGER NOT NULL REFERENCES analyses(id) ON DELETE CASCADE,
                project_name TEXT NOT NULL,
                project_path TEXT,
                owner_username TEXT,
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
                primary_branch TEXT,
                total_branches INTEGER,
                has_remote INTEGER CHECK(has_remote IN (0, 1)),
                last_commit_date TEXT,
                last_modified_date TEXT,
                directory_depth INTEGER,
                project_start_date TEXT,
                project_end_date TEXT,
                project_active_days INTEGER,
                target_user_email TEXT,
                target_user_name TEXT,
                target_user_commits INTEGER,
                target_user_commit_pct REAL,
                target_user_lines_changed INTEGER,
                target_user_surviving_lines INTEGER,
                target_user_last_commit TEXT,
                predicted_role TEXT,
                predicted_role_confidence REAL,
                curated_role TEXT,
                role_prediction_data TEXT
            );
            """
        )

        # Add role prediction columns if they don't exist (for existing databases)
        existing_project_columns = {row["name"] for row in conn.execute("PRAGMA table_info(projects)")}
        role_columns = ["predicted_role", "predicted_role_confidence", "curated_role", "role_prediction_data"]

        for column in role_columns:
            if column not in existing_project_columns:
                if column == "predicted_role_confidence":
                    conn.execute(f"ALTER TABLE projects ADD COLUMN {column} REAL;")
                else:
                    conn.execute(f"ALTER TABLE projects ADD COLUMN {column} TEXT;")

        conn.commit()

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
            CREATE TABLE IF NOT EXISTS project_skills (
                project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                skill TEXT NOT NULL,
                PRIMARY KEY (project_id, skill)
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
            CREATE TABLE IF NOT EXISTS project_remote_urls (
                project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                url TEXT NOT NULL,
                PRIMARY KEY (project_id, url)
            );
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS project_code_ownership (
                project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                path TEXT NOT NULL,
                dominant_author TEXT,
                dominant_email TEXT,
                ownership_percentage REAL,
                total_lines INTEGER,
                PRIMARY KEY (project_id, path)
            );
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS project_blame_summary (
                project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                email TEXT NOT NULL,
                surviving_lines INTEGER,
                PRIMARY KEY (project_id, email)
            );
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS project_language_breakdown (
                project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                email TEXT NOT NULL,
                language TEXT NOT NULL,
                lines_changed INTEGER,
                PRIMARY KEY (project_id, email, language)
            );
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS project_semantic_summary (
                project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                email TEXT NOT NULL,
                name TEXT,
                trivial_commits INTEGER,
                substantial_commits INTEGER,
                total_lines_changed INTEGER,
                PRIMARY KEY (project_id, email)
            );
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS project_contribution_volume (
                project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                email TEXT NOT NULL,
                lines_changed INTEGER,
                PRIMARY KEY (project_id, email)
            );
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS project_activity_breakdown (
                project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                email TEXT NOT NULL,
                activity_type TEXT NOT NULL,
                lines_changed INTEGER,
                PRIMARY KEY (project_id, email, activity_type)
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

        # Resume items
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS resume_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_id INTEGER NOT NULL REFERENCES analyses(id) ON DELETE CASCADE,
                project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                project_name TEXT NOT NULL,
                resume_text TEXT NOT NULL,
                bullet_order INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        # Stored user resumes and their selected bullets
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_resumes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL REFERENCES users(username) ON DELETE CASCADE,
                title TEXT NOT NULL,
                format TEXT NOT NULL,
                content_text TEXT NOT NULL,
                original_filename TEXT,
                original_mime TEXT,
                original_blob BLOB,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_resume_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resume_id INTEGER NOT NULL REFERENCES user_resumes(id) ON DELETE CASCADE,
                resume_item_id INTEGER REFERENCES resume_items(id) ON DELETE SET NULL,
                analysis_id INTEGER,
                project_id INTEGER,
                bullet_text TEXT NOT NULL,
                bullet_order INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        conn.execute("CREATE INDEX IF NOT EXISTS idx_user_resumes_user ON user_resumes(username);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_user_resume_items_resume ON user_resume_items(resume_id, bullet_order);")

        # Migrations for older installs (add missing columns safely)
        existing = {row["name"] for row in conn.execute("PRAGMA table_info(resume_items)")}

        if "analysis_id" not in existing:
            conn.execute("ALTER TABLE resume_items ADD COLUMN analysis_id INTEGER REFERENCES analyses(id) ON DELETE CASCADE;")
        if "project_id" not in existing:
            conn.execute("ALTER TABLE resume_items ADD COLUMN project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE;")
        if "project_name" not in existing:
            conn.execute("ALTER TABLE resume_items ADD COLUMN project_name TEXT;")
        if "bullet_order" not in existing:
            conn.execute("ALTER TABLE resume_items ADD COLUMN bullet_order INTEGER;")

        # index for quick fetch per project/analysis
        conn.execute("CREATE INDEX IF NOT EXISTS idx_resume_items_project ON resume_items(project_id, bullet_order);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_resume_items_analysis ON resume_items(analysis_id);")

        conn.commit()

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS portfolio_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                project_name TEXT NOT NULL,
                text_summary TEXT,
                tech_stack TEXT,
                skills_exercised TEXT,
                quality_score INTEGER,
                sophistication_level TEXT,
                project_statistics TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        # Database migration: Add new columns if they don't exist
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(projects)")
        existing_columns = {row[1] for row in cursor.fetchall()}

        if "owner_username" not in existing_columns:
            conn.execute("ALTER TABLE projects ADD COLUMN owner_username TEXT")

        if "last_commit_date" not in existing_columns:
            conn.execute("ALTER TABLE projects ADD COLUMN last_commit_date TEXT")

        if "last_modified_date" not in existing_columns:
            conn.execute("ALTER TABLE projects ADD COLUMN last_modified_date TEXT")

        if "primary_branch" not in existing_columns:
            conn.execute("ALTER TABLE projects ADD COLUMN primary_branch TEXT")

        if "total_branches" not in existing_columns:
            conn.execute("ALTER TABLE projects ADD COLUMN total_branches INTEGER")

        if "has_remote" not in existing_columns:
            conn.execute("ALTER TABLE projects ADD COLUMN has_remote INTEGER CHECK(has_remote IN (0, 1))")

        if "project_start_date" not in existing_columns:
            conn.execute("ALTER TABLE projects ADD COLUMN project_start_date TEXT")

        if "project_end_date" not in existing_columns:
            conn.execute("ALTER TABLE projects ADD COLUMN project_end_date TEXT")

        if "project_active_days" not in existing_columns:
            conn.execute("ALTER TABLE projects ADD COLUMN project_active_days INTEGER")

        if "target_user_email" not in existing_columns:
            conn.execute("ALTER TABLE projects ADD COLUMN target_user_email TEXT")

        if "target_user_name" not in existing_columns:
            conn.execute("ALTER TABLE projects ADD COLUMN target_user_name TEXT")

        if "target_user_commits" not in existing_columns:
            conn.execute("ALTER TABLE projects ADD COLUMN target_user_commits INTEGER")

        if "target_user_commit_pct" not in existing_columns:
            conn.execute("ALTER TABLE projects ADD COLUMN target_user_commit_pct REAL")

        if "target_user_lines_changed" not in existing_columns:
            conn.execute("ALTER TABLE projects ADD COLUMN target_user_lines_changed INTEGER")

        if "target_user_surviving_lines" not in existing_columns:
            conn.execute("ALTER TABLE projects ADD COLUMN target_user_surviving_lines INTEGER")

        if "target_user_last_commit" not in existing_columns:
            conn.execute("ALTER TABLE projects ADD COLUMN target_user_last_commit TEXT")

        if "thumbnail_image_path" not in existing_columns:
            conn.execute("ALTER TABLE projects ADD COLUMN thumbnail_image_path TEXT")

        # Ensure activity breakdown table exists in migrations as well
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS project_activity_breakdown (
                project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                email TEXT NOT NULL,
                activity_type TEXT NOT NULL,
                lines_changed INTEGER,
                PRIMARY KEY (project_id, email, activity_type)
            );
            """
        )

        # Normalize/dedupe existing projects so we can enforce uniqueness.
        # Drop the unique index temporarily to avoid conflicts during cleanup.
        conn.execute("DROP INDEX IF EXISTS idx_projects_unique_name_path_owner")
        conn.execute("UPDATE projects SET project_path = '' WHERE project_path IS NULL")
        conn.execute("UPDATE projects SET owner_username = '' WHERE owner_username IS NULL")
        conn.execute(
            """
            DELETE FROM projects
            WHERE id NOT IN (
                SELECT MAX(id)
                FROM projects
                GROUP BY project_name, project_path, owner_username
            )
            """
        )

        # Enforce uniqueness so re-analyses replace prior project rows.
        conn.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_projects_unique_name_path_owner
            ON projects (project_name, project_path, owner_username)
            """
        )

        # Clean analyses with no projects only if projects data exists (avoid legacy losses).
        has_projects = conn.execute("SELECT 1 FROM projects LIMIT 1").fetchone()
        if has_projects:
            conn.execute(
                """
                DELETE FROM analyses
                WHERE NOT EXISTS (
                    SELECT 1 FROM projects WHERE projects.analysis_id = analyses.id
                )
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


def _normalize_project_path_value(path: Optional[str]) -> str:
    """Ensure project_path participates in uniqueness (avoid NULL grouping)."""
    return path or ""


def _normalize_username_value(username: Optional[str]) -> str:
    """Ensure username participates in uniqueness (avoid NULL grouping)."""
    return username or ""


def _clear_project_children(conn: sqlite3.Connection, project_id: int, project_name: str) -> None:
    """Remove all child rows for a project so fresh data can be inserted."""
    child_tables = [
        "project_languages",
        "project_frameworks",
        "project_skills",
        "project_dependencies",
        "project_contributors",
        "project_largest_file",
        "project_remote_urls",
        "project_code_ownership",
        "project_blame_summary",
        "project_language_breakdown",
        "project_semantic_summary",
        "project_contribution_volume",
        "project_activity_breakdown",
        "portfolio_items",
    ]
    for table in child_tables:
        conn.execute(f"DELETE FROM {table} WHERE project_id = ?", (project_id,))

    # Resume items historically lacked project_id, so clear by both id and name defensively.
    try:
        conn.execute("DELETE FROM resume_items WHERE project_id = ?", (project_id,))
    except sqlite3.OperationalError:
        conn.execute("DELETE FROM resume_items WHERE project_name = ?", (project_name,))
    else:
        conn.execute("DELETE FROM resume_items WHERE project_name = ?", (project_name,))


def create_upload(username: str, zip_path: str, original_filename: str) -> int:
    init_db()
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO uploads (username, zip_path, original_filename, status)
            VALUES (?, ?, ?, 'uploaded')
            """,
            (username, zip_path, original_filename),
        )
        conn.commit()
        return int(cur.lastrowid)


def get_upload(upload_id: int, username: str):
    init_db()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM uploads WHERE id = ? AND username = ?",
            (upload_id, username),
        ).fetchone()
        return dict(row) if row else None


def update_upload_status(upload_id: int, username: str, status: str) -> None:
    init_db()
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE uploads
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND username = ?
            """,
            (status, upload_id, username),
        )
        conn.commit()


def clear_upload_zip_path(upload_id: int, username: str) -> None:
    init_db()
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE uploads
            SET zip_path = NULL, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND username = ?
            """,
            (upload_id, username),
        )
        conn.commit()


def list_uploads_for_user(username: str, limit: int = 50):
    init_db()
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM uploads
            WHERE username = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (username, limit),
        ).fetchall()
        return [dict(r) for r in rows]


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
    username: Optional[str] = None,
    analysis_uuid: Optional[str] = None,
    zip_file_hash: Optional[str] = None,
) -> int:
    if analysis_type not in VALID_ANALYSIS_TYPES:
        raise ValueError(f"analysis_type must be one of {VALID_ANALYSIS_TYPES}")

    if not payload:
        raise ValueError("payload cannot be empty")

    metadata = payload.get("analysis_metadata") or {}
    summary = payload.get("summary") or {}
    projects = payload.get("projects") or (payload.get("non_llm_results") or {}).get("projects") or []

    if not metadata:
        raise ValueError("payload must include analysis_metadata")

    if "zip_file" not in metadata or "analysis_timestamp" not in metadata:
        raise ValueError("analysis_metadata requires zip_file and analysis_timestamp")

    analysis_uuid = analysis_uuid or str(uuid.uuid4())

    serialized_payload = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    summary_fields = _extract_summary(summary)

    with get_connection() as conn:
        conn.execute("PRAGMA foreign_keys = ON;")

        # Ensure username exists in analysis DB users table (required for FK)
        if username:
            conn.execute(
                """
                INSERT OR IGNORE INTO users (username)
                VALUES (?)
                """,
                (username,),
            )

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
                llm_summary,
                username,
                zip_file_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                username,
                zip_file_hash,
            ),
        )
        analysis_id = cursor.lastrowid
        obsolete_analysis_ids: set[int] = set()
        owner_username = _normalize_username_value(username)

        for project in projects:
            target_user_stats = project.get("target_user_stats") or {}
            target_user_email = project.get("target_user_email") or target_user_stats.get("email")
            target_user_name = target_user_stats.get("name")
            target_user_commits = target_user_stats.get("commit_count") or target_user_stats.get("commits")
            target_user_commit_pct = target_user_stats.get("percentage")
            contribution_volume = project.get("contribution_volume") or {}
            blame_summary = project.get("blame_summary") or {}
            target_user_lines_changed = contribution_volume.get(target_user_email) if target_user_email else None
            target_user_surviving_lines = blame_summary.get(target_user_email) if target_user_email else None
            target_user_last_commit = target_user_stats.get("last_commit_date") or project.get("last_commit_date")
            project_name = project.get("project_name") or "Project"
            project_path = _normalize_project_path_value(project.get("project_path"))

            # Role prediction extraction
            role_prediction_data = project.get("role_prediction", {})
            predicted_role = None
            predicted_role_confidence = None
            role_prediction_json = None

            if role_prediction_data:
                predicted_role = role_prediction_data.get("predicted_role")
                predicted_role_confidence = role_prediction_data.get("confidence_score")
                role_prediction_json = json.dumps(role_prediction_data) if role_prediction_data else None

            # Role prediction extraction
            role_prediction_data = project.get("role_prediction")
            predicted_role = None
            predicted_role_confidence = None
            role_prediction_json = None

            if role_prediction_data:
                predicted_role = (
                    role_prediction_data.get("predicted_role", {}).get("value")
                    if isinstance(role_prediction_data.get("predicted_role"), dict)
                    else str(role_prediction_data.get("predicted_role"))
                )
                predicted_role_confidence = role_prediction_data.get("confidence_score")
                role_prediction_json = json.dumps(role_prediction_data) if role_prediction_data else None

            existing_project = conn.execute(
                """
                SELECT id, analysis_id FROM projects
                WHERE project_name = ? AND project_path = ? AND owner_username = ?
                """,
                (project_name, project_path, owner_username),
            ).fetchone()
            if existing_project and existing_project["analysis_id"] is not None:
                obsolete_analysis_ids.add(existing_project["analysis_id"])

            conn.execute(
                """
                INSERT INTO projects (
                    analysis_id,
                    project_name,
                    project_path,
                    owner_username,
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
                    primary_branch,
                    total_branches,
                    has_remote,
                    last_commit_date,
                    last_modified_date,
                    directory_depth,
                    project_start_date,
                    project_end_date,
                    project_active_days,
                    target_user_email,
                    target_user_name,
                    target_user_commits,
                    target_user_commit_pct,
                    target_user_lines_changed,
                    target_user_surviving_lines,
                    target_user_last_commit,
                    predicted_role,
                    predicted_role_confidence,
                    role_prediction_data
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
                ON CONFLICT(project_name, project_path, owner_username) DO UPDATE SET
                    analysis_id = excluded.analysis_id,
                    project_path = excluded.project_path,
                    owner_username = excluded.owner_username,
                    primary_language = excluded.primary_language,
                    total_files = excluded.total_files,
                    total_size = excluded.total_size,
                    code_files = excluded.code_files,
                    test_files = excluded.test_files,
                    doc_files = excluded.doc_files,
                    config_files = excluded.config_files,
                    has_tests = excluded.has_tests,
                    has_readme = excluded.has_readme,
                    has_ci_cd = excluded.has_ci_cd,
                    has_docker = excluded.has_docker,
                    test_coverage_estimate = excluded.test_coverage_estimate,
                    is_git_repo = excluded.is_git_repo,
                    total_commits = excluded.total_commits,
                    primary_branch = excluded.primary_branch,
                    total_branches = excluded.total_branches,
                    has_remote = excluded.has_remote,
                    last_commit_date = excluded.last_commit_date,
                    last_modified_date = excluded.last_modified_date,
                    directory_depth = excluded.directory_depth,
                    project_start_date = excluded.project_start_date,
                    project_end_date = excluded.project_end_date,
                    project_active_days = excluded.project_active_days,
                    target_user_email = excluded.target_user_email,
                    target_user_name = excluded.target_user_name,
                    target_user_commits = excluded.target_user_commits,
                    target_user_commit_pct = excluded.target_user_commit_pct,
                    target_user_lines_changed = excluded.target_user_lines_changed,
                    target_user_surviving_lines = excluded.target_user_surviving_lines,
                    target_user_last_commit = excluded.target_user_last_commit,
                    predicted_role = excluded.predicted_role,
                    predicted_role_confidence = excluded.predicted_role_confidence,
                    role_prediction_data = excluded.role_prediction_data
                """,
                (
                    analysis_id,
                    project_name,
                    project_path,
                    owner_username,
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
                    project.get("primary_branch"),
                    project.get("total_branches"),
                    _boolean_to_int(project.get("has_remote")),
                    project.get("last_commit_date"),
                    project.get("last_modified_date"),
                    project.get("directory_depth"),
                    project.get("project_start_date"),
                    project.get("project_end_date"),
                    project.get("project_active_days"),
                    target_user_email,
                    target_user_name,
                    target_user_commits,
                    target_user_commit_pct,
                    target_user_lines_changed,
                    target_user_surviving_lines,
                    target_user_last_commit,
                    predicted_role,
                    predicted_role_confidence,
                    role_prediction_json,
                ),
            )
            project_row = conn.execute(
                """
                SELECT id FROM projects WHERE project_name = ? AND project_path = ? AND owner_username = ?
                """,
                (project_name, project_path, owner_username),
            ).fetchone()
            if not project_row:
                raise RuntimeError(f"Failed to upsert project '{project_name}' at path '{project_path}'")
            project_id = project_row["id"]

            _clear_project_children(conn, project_id, project_name)

            # Store resume bullets EXACTLY as CLI generates them
            try:
                from .analysis.resume_generator import _generate_project_items

                bullets = _generate_project_items(project)
                for idx, bullet in enumerate(bullets):
                    if not bullet or not bullet.strip():
                        continue

                    conn.execute(
                        """
                        INSERT INTO resume_items (analysis_id, project_id, project_name, resume_text, bullet_order)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (analysis_id, project_id, project.get("project_name", "Project"), bullet.strip(), idx),
                    )

            except Exception:
                pass

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

            # Generate portfolio item and store skills_exercised
            try:
                from .analysis.portfolio_item_generator import \
                    generate_portfolio_item

                portfolio_item = generate_portfolio_item(project)
                skills_exercised = portfolio_item.get("skills_exercised", []) or []

                # Store skills
                for skill in skills_exercised:
                    conn.execute(
                        """
                        INSERT OR IGNORE INTO project_skills (project_id, skill)
                        VALUES (?, ?)
                        """,
                        (project_id, skill),
                    )

                # Store portfolio item
                stats = portfolio_item.get("project_statistics") or {}
                conn.execute(
                    """
                    INSERT INTO portfolio_items (
                        project_id,
                        project_name,
                        text_summary,
                        tech_stack,
                        skills_exercised,
                        quality_score,
                        sophistication_level,
                        project_statistics
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        project_id,
                        project.get("project_name"),
                        portfolio_item.get("text_summary"),
                        _serialize_array(portfolio_item.get("tech_stack")),
                        _serialize_array(portfolio_item.get("skills_exercised")),
                        stats.get("quality_score"),
                        stats.get("sophistication_level"),
                        json.dumps(stats),
                    ),
                )
            except Exception:
                # If portfolio item generation fails, continue without storing skills
                # This ensures analysis can still be stored even if skills generation fails
                pass

            dependencies = project.get("dependencies") or {}
            for ecosystem, deps in dependencies.items():
                seen_deps = set()
                for dependency in deps or []:
                    if dependency in seen_deps:
                        continue
                    seen_deps.add(dependency)
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

            # Git analysis extended fields
            remote_urls = project.get("remote_urls") or []
            for url in remote_urls:
                conn.execute(
                    """
                    INSERT INTO project_remote_urls (project_id, url)
                    VALUES (?, ?)
                    """,
                    (project_id, url),
                )

            code_ownership = project.get("code_ownership") or []
            for entry in code_ownership:
                conn.execute(
                    """
                    INSERT INTO project_code_ownership (
                        project_id,
                        path,
                        dominant_author,
                        dominant_email,
                        ownership_percentage,
                        total_lines
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        project_id,
                        entry.get("path"),
                        entry.get("dominant_author"),
                        entry.get("dominant_email"),
                        entry.get("ownership_percentage"),
                        entry.get("total_lines"),
                    ),
                )

            blame_summary = project.get("blame_summary") or {}
            for email, lines in blame_summary.items():
                conn.execute(
                    """
                    INSERT INTO project_blame_summary (project_id, email, surviving_lines)
                    VALUES (?, ?, ?)
                    """,
                    (project_id, email, lines),
                )

            language_breakdown = project.get("language_breakdown") or {}
            for email, langs in language_breakdown.items():
                for language, lines in (langs or {}).items():
                    conn.execute(
                        """
                        INSERT INTO project_language_breakdown (project_id, email, language, lines_changed)
                        VALUES (?, ?, ?, ?)
                        """,
                        (project_id, email, language, lines),
                    )

            semantic_summary = project.get("semantic_summary") or {}
            for email, stats in semantic_summary.items():
                conn.execute(
                    """
                    INSERT INTO project_semantic_summary (
                        project_id,
                        email,
                        name,
                        trivial_commits,
                        substantial_commits,
                        total_lines_changed
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        project_id,
                        email,
                        stats.get("name"),
                        stats.get("trivial_commits"),
                        stats.get("substantial_commits"),
                        stats.get("total_lines_changed"),
                    ),
                )

            contribution_volume = project.get("contribution_volume") or {}
            for email, lines in contribution_volume.items():
                conn.execute(
                    """
                    INSERT INTO project_contribution_volume (project_id, email, lines_changed)
                    VALUES (?, ?, ?)
                    """,
                    (project_id, email, lines),
                )

            activity_breakdown = project.get("activity_breakdown") or {}
            for email, activities in activity_breakdown.items():
                for activity_type, lines in (activities or {}).items():
                    if lines is None or lines == 0:
                        continue
                    conn.execute(
                        """
                        INSERT INTO project_activity_breakdown (project_id, email, activity_type, lines_changed)
                        VALUES (?, ?, ?, ?)
                        """,
                        (project_id, email, activity_type, lines),
                    )

        if obsolete_analysis_ids:
            placeholders = ",".join("?" for _ in obsolete_analysis_ids)
            conn.execute(
                f"""
                DELETE FROM analyses
                WHERE id IN ({placeholders})
                AND NOT EXISTS (
                    SELECT 1 FROM projects WHERE projects.analysis_id = analyses.id
                )
                """,
                tuple(obsolete_analysis_ids),
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


def get_projects_for_user(username: str) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                p.id,
                p.project_name,
                p.primary_language,
                p.total_files,
                p.has_tests,
                p.last_modified_date,
                a.username AS owner_username,
                a.analysis_timestamp AS analysis_timestamp
            FROM projects p
            JOIN analyses a ON a.id = p.analysis_id
            WHERE a.username = ?
            ORDER BY p.id DESC
            """,
            (username,),
        ).fetchall()

        return [dict(r) for r in rows]


def get_analysis_by_zip_file(zip_file: str, username: Optional[str] = None) -> Optional[sqlite3.Row]:
    """Get the most recent analysis for a given zip file path scoped to a user."""
    if not username:
        raise ValueError("username is required for get_analysis_by_zip_file")

    with get_connection() as conn:
        return conn.execute(
            """
            SELECT * FROM analyses
            WHERE zip_file = ? AND username = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (zip_file, username),
        ).fetchone()


def get_analysis_by_file_hash(
    file_hash: str,
    username: str,
    analysis_type: str = "non_llm",
) -> Optional[sqlite3.Row]:
    """Return the most recent analysis for a ZIP content hash scoped to a user."""
    if not file_hash or not username:
        return None
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT * FROM analyses
            WHERE zip_file_hash = ? AND username = ? AND analysis_type = ?
            AND total_projects > 0
            ORDER BY created_at DESC LIMIT 1
            """,
            (file_hash, username, analysis_type),
        ).fetchone()


def get_all_analyses_by_zip_file(zip_file: str, username: Optional[str] = None) -> List[sqlite3.Row]:
    """Get all analyses (not just the most recent) for a given zip file path scoped to a user."""
    if not username:
        raise ValueError("username is required for get_all_analyses_by_zip_file")

    with get_connection() as conn:
        return conn.execute(
            """
            SELECT * FROM analyses 
            WHERE zip_file = ? AND username = ?
            ORDER BY created_at DESC
            """,
            (zip_file, username),
        ).fetchall()


def get_analysis_report(zip_file: str, username: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Retrieve the full analysis report (JSON) for a given zip file path scoped to a user."""
    analysis = get_analysis_by_zip_file(zip_file, username=username)
    if not analysis:
        return None

    try:
        return json.loads(analysis["raw_json"])
    except (json.JSONDecodeError, KeyError):
        return None


def count_analyses_by_zip_file(zip_file: str) -> int:
    """Count the number of analyses for a given zip file path."""
    with get_connection() as conn:
        result = conn.execute(
            "SELECT COUNT(*) as count FROM analyses WHERE zip_file = ?",
            (zip_file,),
        ).fetchone()
        return result["count"] if result else 0


def delete_project_for_user(project_id: int, username: str) -> bool:
    """
    Delete a single project owned by `username`.

    NOTE:
    - This deletes from `projects` which cascades to resume_items, portfolio_items,
      and all project_* tables because they have ON DELETE CASCADE.
    - We also decrement analyses.total_projects for the owning analysis row.
    """
    with get_connection() as conn:
        conn.execute("PRAGMA foreign_keys = ON;")

        # Find the analysis row that owns this project
        row = conn.execute(
            """
            SELECT p.analysis_id
            FROM projects p
            JOIN analyses a ON a.id = p.analysis_id
            WHERE p.id = ? AND a.username = ?
            """,
            (project_id, username),
        ).fetchone()

        if not row:
            return False

        analysis_id = row["analysis_id"]

        # Delete project (cascades to related rows)
        cur = conn.execute(
            "DELETE FROM projects WHERE id = ?",
            (project_id,),
        )

        if cur.rowcount > 0:
            conn.execute(
                """
                UPDATE analyses
                SET total_projects = CASE
                    WHEN total_projects > 0 THEN total_projects - 1
                    ELSE 0
                END
                WHERE id = ?
                """,
                (analysis_id,),
            )

        conn.commit()
        return cur.rowcount > 0


def delete_all_projects_for_user(username: str) -> int:
    """Delete ALL projects owned by `username`.

    Notes:
    - Projects are user-scoped via their owning analysis row (analyses.username).
    - Deleting from `projects` cascades to resume_items / portfolio_items and all project_* tables
      because they reference projects(id) with ON DELETE CASCADE.
    - We also decrement analyses.total_projects for each affected analysis row.
    """
    if not username:
        raise ValueError("username is required")

    with get_connection() as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("BEGIN;")

        try:
            # Count how many projects we are deleting per analysis row (so we can update totals).
            counts = conn.execute(
                """
                SELECT p.analysis_id AS analysis_id, COUNT(*) AS cnt
                FROM projects p
                JOIN analyses a ON a.id = p.analysis_id
                WHERE a.username = ?
                GROUP BY p.analysis_id
                """,
                (username,),
            ).fetchall()

            # Delete all projects that belong to this user (via analyses.username)
            cur = conn.execute(
                """
                DELETE FROM projects
                WHERE id IN (
                    SELECT p.id
                    FROM projects p
                    JOIN analyses a ON a.id = p.analysis_id
                    WHERE a.username = ?
                )
                """,
                (username,),
            )
            deleted_count = int(cur.rowcount or 0)

            # Update total_projects for each analysis row that had projects removed
            for row in counts:
                analysis_id = row["analysis_id"]
                cnt = int(row["cnt"] or 0)
                conn.execute(
                    """
                    UPDATE analyses
                    SET total_projects = CASE
                        WHEN total_projects - ? > 0 THEN total_projects - ?
                        ELSE 0
                    END
                    WHERE id = ? AND username = ?
                    """,
                    (cnt, cnt, analysis_id, username),
                )

            conn.execute("COMMIT;")
            return deleted_count
        except Exception:
            conn.execute("ROLLBACK;")
            raise


def delete_analyses_by_zip_file(zip_file: str, username: Optional[str] = None) -> int:
    """Delete all analyses for a given zip file path scoped to a user."""
    if not zip_file:
        raise ValueError("zip_file path cannot be empty")
    if not username:
        raise ValueError("username is required for delete_analyses_by_zip_file")

    try:
        with get_connection() as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            count_result = conn.execute(
                "SELECT COUNT(*) as count FROM analyses WHERE zip_file = ? AND username = ?",
                (zip_file, username),
            ).fetchone()
            count = count_result["count"] if count_result else 0

            if count > 0:
                cursor = conn.execute(
                    "DELETE FROM analyses WHERE zip_file = ? AND username = ?",
                    (zip_file, username),
                )
                deleted_rows = cursor.rowcount
                conn.commit()
                if deleted_rows != count:
                    import logging

                    logging.warning(f"Expected to delete {count} analyses, but only deleted {deleted_rows}")

                return deleted_rows

            return 0
    except Exception as e:
        import logging

        logging.error(f"Error deleting analyses for {zip_file}: {e}")
        raise


def store_resume_item(
    analysis_id: int,
    project_id: int,
    project_name: str,
    resume_text: str,
    bullet_order: int = 0,
) -> None:
    if not resume_text or not resume_text.strip():
        raise ValueError("resume_text is required")

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO resume_items (analysis_id, project_id, project_name, resume_text, bullet_order)
            VALUES (?, ?, ?, ?, ?)
            """,
            (analysis_id, project_id, project_name, resume_text.strip(), bullet_order),
        )
        conn.commit()


def get_all_resume_items(username: Optional[str] = None) -> List[sqlite3.Row]:
    """
    If username is provided, scope results to that user's analyses.
    """
    with get_connection() as conn:
        if username:
            return conn.execute(
                """
                SELECT
                    ri.id, ri.analysis_id, ri.project_id, ri.project_name, ri.resume_text, ri.bullet_order, ri.created_at
                FROM resume_items ri
                JOIN analyses a ON a.id = ri.analysis_id
                WHERE a.username = ?
                ORDER BY ri.created_at DESC
                """,
                (username,),
            ).fetchall()

        return conn.execute(
            """
            SELECT id, analysis_id, project_id, project_name, resume_text, bullet_order, created_at
            FROM resume_items
            ORDER BY created_at DESC
            """
        ).fetchall()


def create_user_resume(
    username: str,
    title: str,
    format: str,
    content_text: str,
    original_filename: Optional[str] = None,
    original_mime: Optional[str] = None,
    original_blob: Optional[bytes] = None,
) -> int:
    if not content_text or not content_text.strip():
        raise ValueError("content_text is required")

    with get_connection() as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute(
            """
            INSERT OR IGNORE INTO users (username)
            VALUES (?)
            """,
            (username,),
        )
        cursor = conn.execute(
            """
            INSERT INTO user_resumes (username, title, format, content_text, original_filename, original_mime, original_blob)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (username, title.strip(), format, content_text, original_filename, original_mime, original_blob),
        )
        conn.commit()
        return int(cursor.lastrowid)


def list_user_resumes(username: str) -> List[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT id, username, title, format, content_text, original_filename, original_mime, created_at, updated_at
            FROM user_resumes
            WHERE username = ?
            ORDER BY updated_at DESC
            """,
            (username,),
        ).fetchall()


def get_user_resume(resume_id: int, username: str) -> Optional[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT id, username, title, format, content_text, original_filename, original_mime, created_at, updated_at
            FROM user_resumes
            WHERE id = ? AND username = ?
            """,
            (resume_id, username),
        ).fetchone()


def update_user_resume_content(resume_id: int, username: str, content_text: str) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE user_resumes
            SET content_text = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND username = ?
            """,
            (content_text, resume_id, username),
        )
        conn.commit()


def add_items_to_user_resume(
    resume_id: int,
    username: str,
    items: List[Dict[str, Any]],
) -> None:
    with get_connection() as conn:
        owner = conn.execute(
            "SELECT id FROM user_resumes WHERE id = ? AND username = ?",
            (resume_id, username),
        ).fetchone()
        if not owner:
            raise ValueError("resume not found")

        for idx, item in enumerate(items):
            conn.execute(
                """
                INSERT INTO user_resume_items (
                    resume_id, resume_item_id, analysis_id, project_id, bullet_text, bullet_order
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    resume_id,
                    item.get("resume_item_id"),
                    item.get("analysis_id"),
                    item.get("project_id"),
                    item["bullet_text"],
                    item.get("bullet_order", idx),
                ),
            )
        conn.commit()


def get_user_resume_items(resume_id: int, username: str) -> List[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT uri.id, uri.resume_id, uri.resume_item_id, uri.analysis_id, uri.project_id,
                   uri.bullet_text, uri.bullet_order, uri.created_at
            FROM user_resume_items uri
            JOIN user_resumes ur ON ur.id = uri.resume_id
            WHERE uri.resume_id = ? AND ur.username = ?
            ORDER BY uri.bullet_order ASC, uri.id ASC
            """,
            (resume_id, username),
        ).fetchall()


def get_resume_items_for_project(project_id: int) -> List[sqlite3.Row]:
    """
    Backwards-compatible alias for older code/tests.
    """
    return get_resume_items_for_project_id(project_id)


def get_resume_items_for_project_id(project_id: int) -> List[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT id, analysis_id, project_id, project_name, resume_text, bullet_order, created_at
            FROM resume_items
            WHERE project_id = ?
            ORDER BY bullet_order ASC, id ASC
            """,
            (project_id,),
        ).fetchall()


def get_resume_items_for_analysis(analysis_id: int) -> List[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT id, analysis_id, project_id, project_name, resume_text, bullet_order, created_at
            FROM resume_items
            WHERE analysis_id = ?
            ORDER BY project_id ASC, bullet_order ASC, id ASC
            """,
            (analysis_id,),
        ).fetchall()


def get_portfolio_item_for_project(project_id: int) -> Optional[dict]:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT
                id, project_id, project_name, text_summary, tech_stack,
                skills_exercised, quality_score, sophistication_level,
                project_statistics, created_at
            FROM portfolio_items
            WHERE project_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (project_id,),
        ).fetchone()

        return dict(row) if row else None


def get_portfolio_items_for_analysis(analysis_uuid: str, username: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fetch all portfolio items for one analysis, with JSON fields deserialized."""
    with get_connection() as conn:
        if username:
            rows = conn.execute(
                """
                SELECT
                    pi.id,
                    pi.project_id,
                    pi.project_name,
                    pi.text_summary,
                    pi.tech_stack,
                    pi.skills_exercised,
                    pi.quality_score,
                    pi.sophistication_level,
                    pi.project_statistics,
                    pi.created_at
                FROM portfolio_items pi
                JOIN projects p ON p.id = pi.project_id
                JOIN analyses a ON a.id = p.analysis_id
                WHERE a.analysis_uuid = ? AND a.username = ?
                  AND pi.id = (
                      SELECT MAX(pi2.id)
                      FROM portfolio_items pi2
                      WHERE pi2.project_id = p.id
                  )
                ORDER BY p.id ASC, pi.id ASC
                """,
                (analysis_uuid, username),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT
                    pi.id,
                    pi.project_id,
                    pi.project_name,
                    pi.text_summary,
                    pi.tech_stack,
                    pi.skills_exercised,
                    pi.quality_score,
                    pi.sophistication_level,
                    pi.project_statistics,
                    pi.created_at
                FROM portfolio_items pi
                JOIN projects p ON p.id = pi.project_id
                JOIN analyses a ON a.id = p.analysis_id
                WHERE a.analysis_uuid = ?
                  AND pi.id = (
                      SELECT MAX(pi2.id)
                      FROM portfolio_items pi2
                      WHERE pi2.project_id = p.id
                  )
                ORDER BY p.id ASC, pi.id ASC
                """,
                (analysis_uuid,),
            ).fetchall()

    items: List[Dict[str, Any]] = []
    for row in rows:
        item = dict(row)

        for key in ("tech_stack", "skills_exercised"):
            value = item.get(key)
            if not value:
                item[key] = []
                continue
            try:
                parsed = json.loads(value)
                item[key] = parsed if isinstance(parsed, list) else []
            except (TypeError, json.JSONDecodeError):
                item[key] = []

        stats = item.get("project_statistics")
        if not stats:
            item["project_statistics"] = {}
        else:
            try:
                parsed_stats = json.loads(stats)
                item["project_statistics"] = parsed_stats if isinstance(parsed_stats, dict) else {}
            except (TypeError, json.JSONDecodeError):
                item["project_statistics"] = {}

        items.append(item)

    return items


def delete_user_personal_info(username: str) -> bool:
    """
    Remove a user's stored personal info entirely.
    Returns True if something was deleted, False if there was nothing to delete.
    """
    if not username:
        raise ValueError("username is required")

    with get_connection() as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        cur = conn.execute(
            """
            DELETE FROM user_profile
            WHERE username = ?
            """,
            (username,),
        )
        conn.commit()
        return (cur.rowcount or 0) > 0


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


def get_all_analyses(username: Optional[str] = None) -> List[sqlite3.Row]:
    """
    Get analyses ordered by most recent first.

    Warning: username is required to avoid cross-user data leakage.
    """
    if not username:
        raise ValueError("username is required for get_all_analyses")

    with get_connection() as conn:
        return conn.execute(
            """
            SELECT * FROM analyses 
            WHERE username = ?
            ORDER BY created_at DESC
            """,
            (username,),
        ).fetchall()


def get_all_analyses_for_user(username: str) -> List[Dict[str, Any]]:
    """Get all analyses for a specific user."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT analysis_uuid, analysis_type, zip_file, analysis_timestamp, 
                   total_projects, raw_json
            FROM analyses 
            WHERE username = ?
            ORDER BY created_at DESC
            """,
            (username,),
        ).fetchall()

        payloads: List[Dict[str, Any]] = []
        for row in rows:
            project_names: List[str] = []
            raw_json = row["raw_json"]
            if raw_json:
                try:
                    parsed = json.loads(raw_json)
                    projects = parsed.get("projects", [])
                    if isinstance(projects, list):
                        for project in projects:
                            if not isinstance(project, dict):
                                continue
                            name = project.get("project_name") or project.get("name")
                            if isinstance(name, str) and name.strip():
                                project_names.append(name.strip())
                except (TypeError, json.JSONDecodeError):
                    project_names = []

            payloads.append(
                {
                    "analysis_uuid": row["analysis_uuid"],
                    "analysis_type": row["analysis_type"],
                    "zip_file": row["zip_file"],
                    "analysis_timestamp": row["analysis_timestamp"],
                    "total_projects": row["total_projects"],
                    "project_names": project_names,
                }
            )

        return payloads


def get_analysis_by_uuid(uuid_str: str, username: str = None) -> Optional[Dict[str, Any]]:
    """Get analysis details by UUID for a specific user."""
    with get_connection() as conn:
        if username:
            row = conn.execute(
                """
                SELECT analysis_uuid, analysis_type, zip_file, analysis_timestamp, 
                       total_projects, raw_json
                FROM analyses 
                WHERE analysis_uuid = ? AND username = ?
                """,
                (uuid_str, username),
            ).fetchone()
        else:
            row = conn.execute(
                """
                SELECT analysis_uuid, analysis_type, zip_file, analysis_timestamp, 
                       total_projects, raw_json
                FROM analyses 
                WHERE analysis_uuid = ?
                """,
                (uuid_str,),
            ).fetchone()

        if not row:
            return None

        # Parse the JSON data to get projects and other details
        raw_data = json.loads(row["raw_json"]) if row["raw_json"] else {}

        return {
            "analysis_uuid": row["analysis_uuid"],
            "analysis_type": row["analysis_type"],
            "zip_file": row["zip_file"],
            "analysis_timestamp": row["analysis_timestamp"],
            "total_projects": row["total_projects"],
            "projects": raw_data.get("projects", []),
            "skills": raw_data.get("skills", []),
            "summary": raw_data.get("summary"),
            "portfolio_items": get_portfolio_items_for_analysis(uuid_str, username),
        }


def delete_analysis(uuid_str: str, username: str = None) -> bool:
    """Delete an analysis by UUID."""
    with get_connection() as conn:
        if username:
            cursor = conn.execute(
                """
                DELETE FROM analyses
                WHERE analysis_uuid = ? AND username = ?
                """,
                (uuid_str, username),
            )
        else:
            cursor = conn.execute(
                """
                DELETE FROM analyses
                WHERE analysis_uuid = ?
                """,
                (uuid_str,),
            )
        conn.commit()
        return cursor.rowcount > 0


def update_project_thumbnail(project_id: int, thumbnail_path: Optional[str]) -> bool:
    """Update the thumbnail image path for a project.

    Args:
        project_id: The project's database ID
        thumbnail_path: Path to the thumbnail image file, or None to remove

    Returns:
        True if update was successful, False otherwise
    """
    with get_connection() as conn:
        cursor = conn.execute(
            """
            UPDATE projects
            SET thumbnail_image_path = ?
            WHERE id = ?
            """,
            (thumbnail_path, project_id),
        )
        conn.commit()
        return cursor.rowcount > 0


def get_project_by_path_and_portfolio(portfolio_uuid: str, project_path: str, username: str) -> Optional[sqlite3.Row]:
    """Get a project by its path within a specific portfolio.

    Args:
        portfolio_uuid: UUID of the portfolio
        project_path: Path of the project within the portfolio
        username: Username to verify access

    Returns:
        Project row if found, None otherwise
    """
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT p.*
            FROM projects p
            JOIN analyses a ON a.id = p.analysis_id
            WHERE a.analysis_uuid = ?
            AND p.project_path = ?
            AND a.username = ?
            """,
            (portfolio_uuid, project_path, username),
        ).fetchone()


def get_project_thumbnail(project_id: int) -> Optional[str]:
    """Get the thumbnail path for a project.

    Args:
        project_id: The project's database ID

    Returns:
        Thumbnail path if set, None otherwise
    """
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT thumbnail_image_path
            FROM projects
            WHERE id = ?
            """,
            (project_id,),
        ).fetchone()
        return row["thumbnail_image_path"] if row else None


def get_user_personal_info(username: str) -> Dict[str, str]:
    if not username:
        return {}

    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT personal_info_json
            FROM user_profile
            WHERE username = ?
            """,
            (username,),
        ).fetchone()

        if not row or not row["personal_info_json"]:
            return {}

        try:
            data = json.loads(row["personal_info_json"])
            return data if isinstance(data, dict) else {}
        except json.JSONDecodeError:
            return {}


def upsert_user_personal_info(username: str, personal_info: Dict[str, str]) -> None:
    if not username:
        raise ValueError("username is required")

    cleaned: Dict[str, str] = {}
    for k, v in (personal_info or {}).items():
        if v is None:
            continue
        cleaned[str(k)] = str(v).strip()

    with get_connection() as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("INSERT OR IGNORE INTO users (username) VALUES (?)", (username,))

        conn.execute(
            """
            INSERT INTO user_profile (username, personal_info_json)
            VALUES (?, ?)
            ON CONFLICT(username) DO UPDATE SET
                personal_info_json = excluded.personal_info_json,
                updated_at = CURRENT_TIMESTAMP
            """,
            (username, json.dumps(cleaned, separators=(",", ":"))),
        )
        conn.commit()
