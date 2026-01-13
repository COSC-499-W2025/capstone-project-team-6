"""
Background task management system for portfolio analysis processing.

Handles asynchronous analysis tasks with status tracking and file management.
"""

import asyncio
import hashlib
import json
import logging
import shutil
import tempfile
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

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

    def store_file_permanently(self, temp_path: Path, file_hash: str = None) -> Path:
        """Move file from temp to permanent storage with deduplication."""
        if not file_hash:
            file_hash = self.calculate_file_hash(temp_path)

        # Use hash as filename to ensure deduplication
        permanent_path = self.permanent_dir / f"{file_hash}.zip"

        if not permanent_path.exists():
            shutil.move(str(temp_path), str(permanent_path))
            logger.info(f"File stored permanently: {permanent_path}")
        else:
            # File already exists, remove temporary file
            temp_path.unlink()
            logger.info(f"Duplicate file detected, using existing: {permanent_path}")

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
            logger.error(f"Task {task_id} failed: {e}")

        task.updated_at = datetime.now()

    async def _process_new_portfolio(self, task: TaskInfo) -> Dict[str, Any]:
        """Process a new portfolio upload."""
        from .analysis_database import record_analysis
        from .cli import analyze_folder

        # Simulate processing time
        await asyncio.sleep(1)
        task.progress = 50

        # Run analysis on the uploaded file
        file_path = Path(task.file_path)

        try:
            analysis_result = analyze_folder(file_path)
            task.progress = 80

            # Store analysis in database
            analysis_id = record_analysis(task.analysis_type or "non_llm", analysis_result)
            task.progress = 90

            return {
                "analysis_id": analysis_id,
                "analysis_uuid": analysis_result.get("analysis_metadata", {}).get("analysis_uuid"),
                "total_projects": len(analysis_result.get("projects", [])),
                "file_hash": task.file_hash,
            }
        except Exception as e:
            logger.error(f"Analysis failed for task {task.task_id}: {e}")
            # Return a simplified result for now
            return {
                "analysis_id": None,
                "analysis_uuid": str(uuid.uuid4()),
                "total_projects": 0,
                "file_hash": task.file_hash,
                "error": str(e),
            }

    async def _process_incremental_upload(self, task: TaskInfo) -> Dict[str, Any]:
        """Process an incremental upload to existing portfolio."""
        from .analysis_database import get_analysis_by_uuid, record_analysis
        from .cli import analyze_folder

        # Get existing portfolio
        existing_portfolio = get_analysis_by_uuid(task.portfolio_id, task.username)
        if not existing_portfolio:
            raise ValueError(f"Portfolio {task.portfolio_id} not found")

        await asyncio.sleep(1)
        task.progress = 40

        try:
            # Analyze new file
            file_path = Path(task.file_path)
            new_analysis = analyze_folder(file_path)

            task.progress = 70

            # Merge with existing portfolio (simplified merging)
            merged_projects = existing_portfolio.get("projects", []) + new_analysis.get("projects", [])

            # Create new analysis with merged data
            merged_analysis = new_analysis.copy()
            merged_analysis["projects"] = merged_projects
            merged_analysis["total_projects"] = len(merged_projects)

            task.progress = 90

            # Store updated analysis
            analysis_id = record_analysis("incremental", merged_analysis)

            return {
                "analysis_id": analysis_id,
                "analysis_uuid": merged_analysis.get("analysis_metadata", {}).get("analysis_uuid"),
                "total_projects": len(merged_projects),
                "original_portfolio_id": task.portfolio_id,
                "added_projects": len(new_analysis.get("projects", [])),
            }
        except Exception as e:
            logger.error(f"Incremental analysis failed for task {task.task_id}: {e}")
            return {
                "analysis_id": None,
                "analysis_uuid": str(uuid.uuid4()),
                "total_projects": 0,
                "original_portfolio_id": task.portfolio_id,
                "added_projects": 0,
                "error": str(e),
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
