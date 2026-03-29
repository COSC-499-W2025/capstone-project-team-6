"""Task management API endpoints."""

import logging
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.api.auth import verify_token
from backend.task_manager import TaskStatus, get_task_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Tasks"])


class TaskStatusResponse(BaseModel):
    """Task status information."""

    task_id: str
    status: str
    task_type: str
    username: str
    filename: str
    created_at: str
    updated_at: str
    progress: int = 0
    error: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    analysis_phase: Optional[str] = None  # "non_llm" or "llm" during processing


def _sanitize_for_json(obj: Any) -> Any:
    """Recursively sanitize values for JSON serialization."""
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        if isinstance(obj, float) and (obj != obj or obj == float("inf") or obj == float("-inf")):
            return None
        return obj
    if isinstance(obj, (list, tuple)):
        return [_sanitize_for_json(x) for x in obj]
    if isinstance(obj, dict):
        return {str(k): _sanitize_for_json(v) for k, v in obj.items()}
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    if hasattr(obj, "__str__"):
        return str(obj)
    return None


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str, username: str = Depends(verify_token)):
    """Get status of a specific task."""
    try:
        task_manager = get_task_manager()
        task = task_manager.get_task_status(task_id)

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found",
            )

        if task.username != username:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this task",
            )

        created_at = task.created_at.isoformat() if hasattr(task.created_at, "isoformat") else str(task.created_at)
        updated_at = task.updated_at.isoformat() if hasattr(task.updated_at, "isoformat") else str(task.updated_at)
        result = _sanitize_for_json(task.result) if task.result else None

        return TaskStatusResponse(
            task_id=task.task_id,
            status=task.status.value,
            task_type=task.task_type.value,
            username=task.username,
            filename=task.filename,
            created_at=created_at,
            updated_at=updated_at,
            error=task.error,
            result=result,
            progress=task.progress,
            analysis_phase=getattr(task, "analysis_phase", None),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error getting task status")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Alias endpoint for more RESTful /status path
@router.get("/tasks/{task_id}/status", response_model=TaskStatusResponse)
async def get_task_status_alias(task_id: str, username: str = Depends(verify_token)):
    """Get status of a specific task (alias endpoint)."""
    return await get_task_status(task_id, username)


@router.get("/tasks", response_model=List[TaskStatusResponse])
async def list_user_tasks(
    username: str = Depends(verify_token),
    limit: int = 50,
):
    """List all tasks for the authenticated user (most recent first)."""
    task_manager = get_task_manager()
    all_tasks = task_manager.get_user_tasks(username)

    def _sort_key(t):
        val = t.created_at
        if isinstance(val, datetime):
            return val.isoformat()
        return str(val)

    sorted_tasks = sorted(all_tasks, key=_sort_key, reverse=True)[:limit]

    result_list = []
    for task in sorted_tasks:
        created_at = task.created_at.isoformat() if hasattr(task.created_at, "isoformat") else str(task.created_at)
        updated_at = task.updated_at.isoformat() if hasattr(task.updated_at, "isoformat") else str(task.updated_at)
        result_list.append(
            TaskStatusResponse(
                task_id=task.task_id,
                status=task.status.value,
                task_type=task.task_type.value,
                username=task.username,
                filename=task.filename,
                created_at=created_at,
                updated_at=updated_at,
                error=task.error,
                result=_sanitize_for_json(task.result) if task.result else None,
                progress=getattr(task, "progress", 0),
            )
        )
    return result_list


@router.post("/tasks/{task_id}/cancel")
async def cancel_task(task_id: str, username: str = Depends(verify_token)):
    """Cancel a running task."""
    try:
        task_manager = get_task_manager()
        task = task_manager.get_task_status(task_id)

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found",
            )

        if task.username != username:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this task",
            )

        cancelled = task_manager.cancel_task(task_id)
        return {"task_id": task_id, "cancelled": cancelled}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error cancelling task")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/admin/cleanup")
async def cleanup_completed_tasks(username: str = Depends(verify_token)):
    """Admin endpoint to clean up old completed tasks (stub for now)."""
    task_manager = get_task_manager()

    user_tasks = task_manager.get_user_tasks(username)
    completed_tasks = [t for t in user_tasks if t.status == TaskStatus.COMPLETED]

    return {
        "message": "Cleanup check completed",
        "total_tasks": len(user_tasks),
        "completed_tasks": len(completed_tasks),
        "note": "Cleanup not yet implemented",
    }
