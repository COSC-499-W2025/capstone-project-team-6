"""
Background task management system for portfolio analysis processing.

Handles asynchronous analysis tasks with status tracking and file management.
"""

import asyncio
import contextlib
import hashlib
import io
import json
import logging
import shutil
import tempfile
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

# Thread pool for blocking operations
_executor = ThreadPoolExecutor(max_workers=4)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """Task status enumeration."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(str, Enum):
    """Task type enumeration."""

    NEW_PORTFOLIO = "new_portfolio"
    INCREMENTAL_UPLOAD = "incremental_upload"


class TaskInfo(BaseModel):
    """Task information model."""

    task_id: str
    task_type: TaskType
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    username: str
    filename: str
    file_path: Optional[str] = None
    file_hash: Optional[str] = None
    progress: int = 0
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    analysis_type: Optional[str] = None
    portfolio_id: Optional[str] = None  # For incremental uploads
    project_name: Optional[str] = None  # User-provided project name override
    analysis_phase: Optional[str] = None  # "non_llm" or "llm" for display during processing


class FileManager:
    """Manages file storage, deduplication and cleanup."""

    def __init__(self, storage_dir: Path = None):
        self.storage_dir = storage_dir or Path(tempfile.gettempdir()) / "mda_storage"
        self.storage_dir.mkdir(exist_ok=True, parents=True)
        self.temp_dir = self.storage_dir / "temp"
        self.permanent_dir = self.storage_dir / "permanent"
        self.temp_dir.mkdir(exist_ok=True)
        self.permanent_dir.mkdir(exist_ok=True)

    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()

    '''
    def store_file_permanently(self, temp_path: Path, file_hash: str = None) -> Path:
        """Store file in permanent storage with deduplication.

        IMPORTANT:
        - If the file is in our temp upload directory, we can move/delete it.
        - If it's a user-provided path elsewhere, we MUST NOT delete/move it.
          We copy it instead.

          This change was made as the whole zip file was moved to temp and made it look like the file was permenently deleted.
        """
        if not file_hash:
            file_hash = self.calculate_file_hash(temp_path)

        permanent_path = self.permanent_dir / f"{file_hash}.zip"

        if permanent_path.exists():
            # already stored; only delete source if it's our temp file
            try:
                if temp_path.resolve().is_relative_to(self.temp_dir.resolve()):
                    temp_path.unlink(missing_ok=True)
            except Exception:
                pass
            logger.info(f"Duplicate file detected, using existing: {permanent_path}")
            return permanent_path

        # Decide whether we can safely delete the source
        can_delete_source = False
        try:
            can_delete_source = temp_path.resolve().is_relative_to(self.temp_dir.resolve())
        except Exception:
            can_delete_source = False

        if can_delete_source:
            # safe: uploaded temp file
            shutil.move(str(temp_path), str(permanent_path))
            logger.info(f"File moved to permanent storage: {permanent_path}")
        else:
            # safe: user file (do not remove from their computer)
            shutil.copy2(str(temp_path), str(permanent_path))
            logger.info(f"File copied to permanent storage (source preserved): {permanent_path}")

        return permanent_path
    '''

    def store_file_permanently(
        self,
        temp_path: Path,
        file_hash: str = None,
        *,
        preserve_source: Optional[bool] = None,
    ) -> Path:
        """
        Store file in permanent storage with deduplication.

        preserve_source:
          - None: auto-detect (preserve if NOT in self.temp_dir)
          - True: always preserve original (copy)
          - False: safe to delete/move original (move; and delete if dedup hit)

        Rationale:
          - Uploaded temp files should be removable.
          - User-provided paths (fixed path projects) must not be deleted.
        """
        if not file_hash:
            file_hash = self.calculate_file_hash(temp_path)

        permanent_path = self.permanent_dir / f"{file_hash}.zip"

        # Decide behavior if not explicitly provided
        if preserve_source is None:
            try:
                # If it's inside our temp upload dir, we can delete/move it.
                preserve_source = not temp_path.resolve().is_relative_to(self.temp_dir.resolve())
            except Exception:
                # Conservative default: preserve
                preserve_source = True

        # If already stored, dedup: optionally remove the source if allowed
        if permanent_path.exists():
            if not preserve_source:
                try:
                    temp_path.unlink(missing_ok=True)
                except Exception:
                    pass
            logger.info(f"Duplicate file detected, using existing: {permanent_path}")
            return permanent_path

        # First time storing
        if preserve_source:
            shutil.copy2(str(temp_path), str(permanent_path))
            logger.info(f"File copied to permanent storage (source preserved): {permanent_path}")
        else:
            shutil.move(str(temp_path), str(permanent_path))
            logger.info(f"File moved to permanent storage: {permanent_path}")

        return permanent_path

    def cleanup_temp_files(self, older_than_hours: int = 24):
        """Clean up temporary files older than specified hours."""
        cutoff_time = datetime.now().timestamp() - (older_than_hours * 3600)
        cleaned = 0

        for file_path in self.temp_dir.iterdir():
            if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                try:
                    file_path.unlink()
                    cleaned += 1
                except OSError:
                    pass

        logger.info(f"Cleaned up {cleaned} temporary files")
        return cleaned

    def get_file_by_hash(self, file_hash: str) -> Optional[Path]:
        """Get permanent file path by hash."""
        file_path = self.permanent_dir / f"{file_hash}.zip"
        return file_path if file_path.exists() else None


class TaskManager:
    """Manages background tasks and their lifecycle."""

    def __init__(self):
        self.tasks: Dict[str, TaskInfo] = {}
        self.file_manager = FileManager()

    def create_task(
        self,
        task_type: TaskType,
        username: str,
        filename: str,
        file_path: Path,
        analysis_type: str = None,
        portfolio_id: str = None,
        project_name: str = None,
    ) -> str:
        """Create a new task and return task ID."""
        task_id = str(uuid.uuid4())
        file_hash = self.file_manager.calculate_file_hash(file_path)

        task = TaskInfo(
            task_id=task_id,
            task_type=task_type,
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            username=username,
            filename=filename,
            file_path=str(file_path),
            file_hash=file_hash,
            analysis_type=analysis_type,
            portfolio_id=portfolio_id,
            project_name=project_name,
        )

        self.tasks[task_id] = task
        logger.info(f"Created task {task_id} for user {username}")

        # Start processing in background
        asyncio.create_task(self._process_task(task_id))

        return task_id

    def get_task_status(self, task_id: str) -> Optional[TaskInfo]:
        """Get current task status."""
        return self.tasks.get(task_id)

    def get_user_tasks(self, username: str, limit: int = 50) -> List[TaskInfo]:
        """Get tasks for a specific user."""
        user_tasks = [task for task in self.tasks.values() if task.username == username]
        # Sort by creation time, newest first
        user_tasks.sort(key=lambda t: t.created_at, reverse=True)
        return user_tasks[:limit]

    async def _process_task(self, task_id: str):
        """Process a task asynchronously."""
        task = self.tasks.get(task_id)
        if not task:
            return

        try:
            # Update status to running
            task.status = TaskStatus.RUNNING
            task.updated_at = datetime.now()
            task.progress = 10

            logger.info(f"Starting processing task {task_id}")

            # Store file permanently (with deduplication)
            temp_path = Path(task.file_path)
            permanent_path = self.file_manager.store_file_permanently(temp_path, task.file_hash)
            task.file_path = str(permanent_path)
            task.progress = 30

            if task.task_type == TaskType.NEW_PORTFOLIO:
                result = await self._process_new_portfolio(task)
            elif task.task_type == TaskType.INCREMENTAL_UPLOAD:
                result = await self._process_incremental_upload(task)
            else:
                raise ValueError(f"Unknown task type: {task.task_type}")

            task.result = result
            task.status = TaskStatus.COMPLETED
            task.progress = 100
            logger.info(f"Task {task_id} completed successfully")

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.progress = 0
            logger.error(f"Task {task_id} failed: {e}", exc_info=True)
            raise

        finally:
            task.updated_at = datetime.now()

    '''
    async def _process_new_portfolio(self, task: TaskInfo) -> Dict[str, Any]:
        """Process a new portfolio upload.

        Offloads blocking analyze_folder to thread executor.
        """
        from .analysis_database import record_analysis
        from .cli import analyze_folder

        # Simulate processing time
        await asyncio.sleep(1)
        task.progress = 50

        # Run analysis on the uploaded file
        file_path = Path(task.file_path)

        # Offload blocking operation to thread pool
        loop = asyncio.get_event_loop()
        analysis_result = await loop.run_in_executor(
            _executor,
            analyze_folder,
            file_path,
        )
        task.progress = 80

        # Store analysis in database
        analysis_id = record_analysis(task.analysis_type or "non_llm", analysis_result, username=task.username)
        task.progress = 90

        return {
            "analysis_id": analysis_id,
            "analysis_uuid": analysis_result.get("analysis_metadata", {}).get("analysis_uuid"),
            "total_projects": len(analysis_result.get("projects", [])),
            "file_hash": task.file_hash,
        }
    '''

    async def _process_new_portfolio(self, task: TaskInfo) -> Dict[str, Any]:
        """Process a new portfolio upload (webapp pipeline).

        Option B:
        - Always run non-LLM analysis + store it for this user.
        - If user has consent, run LLM analysis + store it for this user.
        - LLM failures do not fail the whole task.
        """
        from backend.database import check_user_consent

        from .analysis.llm_pipeline import run_gemini_analysis
        from .analysis_database import get_analysis, record_analysis
        from .cli import analyze_folder

        await asyncio.sleep(1)
        task.progress = 50

        if not task.file_path:
            raise ValueError("Task file_path is missing")
        file_path = Path(task.file_path)
        loop = asyncio.get_event_loop()

        # 1) NON-LLM ANALYSIS (always)
        task.analysis_phase = "non_llm"
        analysis_result = await loop.run_in_executor(_executor, analyze_folder, file_path)
        task.progress = 80

        # Override project name with user-provided value if set
        if task.project_name and task.project_name.strip():
            projects = analysis_result.get("projects", [])
            if len(projects) == 1:
                projects[0]["project_name"] = task.project_name.strip()
            elif len(projects) > 1:
                for p in projects:
                    if (p.get("project_path") or "") == "" or p.get("project_name") == "root_project":
                        p["project_name"] = task.project_name.strip()
                        break

        analysis_id = record_analysis(task.analysis_type or "non_llm", analysis_result, username=task.username)
        row = get_analysis(analysis_id)
        analysis_uuid = row["analysis_uuid"] if row and "analysis_uuid" in row else None

        task.progress = 90

        result_payload: Dict[str, Any] = {
            "analysis_id": analysis_id,
            "analysis_uuid": analysis_uuid,
            "total_projects": len(analysis_result.get("projects", [])),
            "file_hash": task.file_hash,
            "llm_ran": False,
            "llm_analysis_id": None,
            "llm_error": None,
        }

        # 2) LLM ANALYSIS (only if consent)
        try:
            has_consented = check_user_consent(task.username)
        except Exception as e:
            has_consented = False
            result_payload["llm_error"] = f"Consent check failed: {e}"

        if has_consented and (task.analysis_type or "non_llm") == "llm":
            task.analysis_phase = "llm"
            task.progress = 92
            try:
                # Choose active features
                active_features = ["architecture", "complexity", "security", "skills", "domain", "resume"]

                # Run LLM analysis
                llm_results = await loop.run_in_executor(
                    _executor,
                    run_gemini_analysis,
                    file_path,
                    active_features,
                    None,  # prompt_override
                    None,  # progress_callback
                )

                task.progress = 97

                # Store LLM under same user. Use empty projects to avoid duplicate project rows
                # (non_llm analysis already stored the projects; LLM only adds enhancements)
                llm_results["non_llm_results"] = analysis_result
                llm_payload = {**llm_results, "projects": []}
                llm_analysis_id = record_analysis("llm", llm_payload, username=task.username)

                result_payload["llm_ran"] = True
                result_payload["llm_analysis_id"] = llm_analysis_id
                result_payload["llm_error"] = None

            except Exception as e:
                # do NOT fail entire task if LLM fails
                result_payload["llm_ran"] = False
                result_payload["llm_error"] = str(e)

        task.progress = 99
        return result_payload

    async def _process_incremental_upload(self, task: TaskInfo) -> Dict[str, Any]:
        """Process an incremental upload to existing portfolio."""
        from .analysis_database import get_analysis_by_uuid, get_connection
        from .cli import analyze_folder
        from .project_comparison import process_incremental_projects

        # Get existing portfolio
        existing_portfolio = get_analysis_by_uuid(task.portfolio_id, task.username)
        if not existing_portfolio:
            raise ValueError(f"Portfolio {task.portfolio_id} not found")

        await asyncio.sleep(1)
        task.progress = 40

        # Analyze new file using existing pipeline - offload to thread pool
        file_path = Path(task.file_path)
        loop = asyncio.get_event_loop()
        new_analysis = await loop.run_in_executor(
            _executor,
            analyze_folder,
            file_path,
        )

        task.progress = 60

        # Process projects: add new, update existing with >50% change
        existing_projects = existing_portfolio.get("projects", [])
        new_projects = new_analysis.get("projects", [])

        # Use utility function to process incremental projects
        result = process_incremental_projects(
            existing_projects=existing_projects, new_projects=new_projects, change_threshold=30.0
        )

        merged_projects = result["merged_projects"]
        added_projects = result["added_projects"]
        updated_projects = result["updated_projects"]
        skipped_projects = result["skipped_projects"]

        # Log details
        for update in updated_projects:
            logger.info(f"Updated project '{update['project_path']}' with {update['change_percentage']:.1f}% changes")

        for skip in skipped_projects:
            logger.info(f"Skipped project '{skip['project_path']}' with only {skip['change_percentage']:.1f}% changes")

        for project in added_projects:
            logger.info(f"Added new project '{project.get('project_path', 'unknown')}'")

        # Merge and recompute metadata
        merged_data = self._merge_analysis_metadata(
            existing=existing_portfolio,
            new=new_analysis,
            merged_projects=merged_projects,
        )

        # Update the analysis and re-record projects
        from .analysis_database import get_connection as get_analysis_conn

        with get_analysis_conn() as conn:
            # Get the analysis_id
            analysis_row = conn.execute("SELECT id FROM analyses WHERE analysis_uuid = ?", (task.portfolio_id,)).fetchone()

            if not analysis_row:
                raise ValueError(f"Analysis {task.portfolio_id} not found")

            analysis_id = analysis_row["id"]

            # Delete old projects and their related data (cascades automatically)
            conn.execute("DELETE FROM projects WHERE analysis_id = ?", (analysis_id,))

            # Update the analysis row with new data
            summary_fields = merged_data.get("summary", {})
            languages_str = json.dumps(summary_fields.get("languages", []))
            frameworks_str = json.dumps(summary_fields.get("frameworks", []))

            conn.execute(
                """UPDATE analyses 
                   SET raw_json = ?, 
                       total_projects = ?,
                       analysis_timestamp = datetime('now'),
                       summary_total_files = ?,
                       summary_total_size_bytes = ?,
                       summary_total_size_mb = ?,
                       summary_languages = ?,
                       summary_frameworks = ?
                   WHERE analysis_uuid = ?""",
                (
                    json.dumps(merged_data),
                    len(merged_projects),
                    summary_fields.get("total_files", 0),
                    summary_fields.get("total_size", 0),
                    summary_fields.get("total_size_mb", 0.0),
                    languages_str,
                    frameworks_str,
                    task.portfolio_id,
                ),
            )

            # Now insert updated project records
            from .analysis_database import (_normalize_project_path_value,
                                            _normalize_username_value)

            owner_username = _normalize_username_value(task.username)

            for project in merged_projects:
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

                # Role prediction
                role_prediction_data = project.get("role_prediction", {})
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
                    role_prediction_json = json.dumps(role_prediction_data)

                cursor = conn.execute(
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
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        analysis_id,
                        project_name,
                        project_path,
                        owner_username,
                        project.get("primary_language"),
                        project.get("total_files", 0),
                        project.get("total_size", 0),
                        project.get("code_files", 0),
                        project.get("test_files", 0),
                        project.get("doc_files", 0),
                        project.get("config_files", 0),
                        project.get("has_tests", False),
                        project.get("has_readme", False),
                        project.get("has_ci_cd", False),
                        project.get("has_docker", False),
                        project.get("test_coverage_estimate"),
                        project.get("is_git_repo", False),
                        project.get("total_commits", 0),
                        project.get("primary_branch"),
                        project.get("total_branches", 0),
                        project.get("has_remote", False),
                        project.get("last_commit_date"),
                        project.get("last_modified_date"),
                        project.get("directory_depth", 0),
                        project.get("project_start_date"),
                        project.get("project_end_date"),
                        project.get("project_active_days", 0),
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
                project_id = cursor.lastrowid

                try:
                    from .analysis.portfolio_item_generator import generate_portfolio_item

                    portfolio_item = generate_portfolio_item(project)
                    skills_exercised = portfolio_item.get("skills_exercised", []) or []

                    for skill in skills_exercised:
                        conn.execute(
                            """
                            INSERT OR IGNORE INTO project_skills (project_id, skill)
                            VALUES (?, ?)
                            """,
                            (project_id, skill),
                        )

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
                            json.dumps(portfolio_item.get("tech_stack", [])),
                            json.dumps(portfolio_item.get("skills_exercised", [])),
                            stats.get("quality_score"),
                            stats.get("sophistication_level"),
                            json.dumps(stats),
                        ),
                    )
                except Exception as e:
                    logger.warning(f"Failed to generate portfolio item for project {project_path}: {e}")

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
                except Exception as e:
                    # If resume item generation fails, continue without breaking
                    logger.warning(f"Failed to generate resume items for project {project_path}: {e}")

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

            conn.commit()

        task.progress = 90

        logger.info(
            f"Incremental upload {task.task_id}: "
            f"added {len(added_projects)} projects, "
            f"updated {len(updated_projects)} projects, "
            f"skipped {len(skipped_projects)} projects, "
            f"total now {len(merged_projects)}"
        )

        return {
            "analysis_uuid": task.portfolio_id,
            "total_projects": len(merged_projects),
            "original_portfolio_id": task.portfolio_id,
            "added_projects": len(added_projects),
            "updated_projects": len(updated_projects),
            "skipped_projects": len(skipped_projects),
            "update_details": {
                "added": [p.get("project_path", "unknown") if isinstance(p, dict) else "unknown" for p in added_projects],
                "updated": updated_projects,
                "skipped": skipped_projects,
            },
        }

    def _merge_analysis_metadata(
        self,
        existing: Dict[str, Any],
        new: Dict[str, Any],
        merged_projects: list,
    ) -> Dict[str, Any]:
        """Merge analysis metadata.

        Updates summaries, skills, timestamps, and other computed fields
        to reflect the combined project set.
        """
        existing_meta = existing.get("analysis_metadata", {})
        new_meta = new.get("analysis_metadata", {})

        # Merge skills (combine and deduplicate)
        existing_skills = set(existing_meta.get("skills", []))
        new_skills = set(new_meta.get("skills", []))
        merged_skills = sorted(list(existing_skills | new_skills))

        # Merge languages (combine and deduplicate)
        existing_langs = set(existing_meta.get("languages", []))
        new_langs = set(new_meta.get("languages", []))
        merged_langs = sorted(list(existing_langs | new_langs))

        # Update totals and timestamps
        merged_metadata = existing_meta.copy()
        merged_metadata.update(
            {
                "total_projects": len(merged_projects),
                "skills": merged_skills,
                "languages": merged_langs,
                "total_files": (existing_meta.get("total_files", 0) + new_meta.get("total_files", 0)),
                "total_lines_of_code": (existing_meta.get("total_lines_of_code", 0) + new_meta.get("total_lines_of_code", 0)),
                "last_updated": datetime.now().isoformat(),
            }
        )

        return {
            **existing,
            "projects": merged_projects,
            "analysis_metadata": merged_metadata,
        }

    def cleanup_completed_tasks(self, older_than_hours: int = 48):
        """Clean up completed tasks older than specified hours."""
        cutoff_time = datetime.now().timestamp() - (older_than_hours * 3600)
        to_remove = []

        for task_id, task in self.tasks.items():
            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED] and task.updated_at.timestamp() < cutoff_time:
                to_remove.append(task_id)

        for task_id in to_remove:
            del self.tasks[task_id]

        logger.info(f"Cleaned up {len(to_remove)} old tasks")
        return len(to_remove)


# Global task manager instance
_task_manager: Optional[TaskManager] = None


def get_task_manager() -> TaskManager:
    """Get the global task manager instance."""
    global _task_manager
    if _task_manager is None:
        _task_manager = TaskManager()
    return _task_manager


def cleanup_background_tasks():
    """Clean up old tasks and temporary files."""
    manager = get_task_manager()
    manager.cleanup_completed_tasks()
    manager.file_manager.cleanup_temp_files()
