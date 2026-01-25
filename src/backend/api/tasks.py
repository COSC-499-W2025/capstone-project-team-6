"""Task management API endpoints."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from datetime import datetime
from backend.api.auth import verify_token
from backend.task_manager import TaskStatus, get_task_manager

router = APIRouter(prefix="/api", tags=["Tasks"])


class TaskStatusResponse(BaseModel):
    """Task status information."""

    task_id: str
    status: str
    task_type: str
    username: str
    filename: str
    created_at: datetime
    updated_at: datetime
    progress: int = 0
    error: Optional[str] = None
    result: Optional[Dict[str, Any]] = None


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str, username: str = Depends(verify_token)):
    """Get status of a specific task."""
    task_manager = get_task_manager()
    task = task_manager.get_task(task_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )

    # Verify task belongs to user
    if task.username != username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this task",
        )

    return TaskStatusResponse(
        task_id=task.task_id,
        status=task.status.value,
        task_type=task.task_type.value,
        username=task.username,
        filename=task.filename,
        created_at=task.created_at,
        updated_at=task.updated_at,
        error=task.error,
        result=task.result,
        progress=task.progress,
    )


@router.get("/tasks", response_model=List[TaskStatusResponse])
async def list_user_tasks(
    username: str = Depends(verify_token),
    limit: int = 50,
):
    """List all tasks for the authenticated user (most recent first)."""
    task_manager = get_task_manager()
    all_tasks = task_manager.get_user_tasks(username)

    # Sort by created_at descending and limit
    sorted_tasks = sorted(
        all_tasks,
        key=lambda t: t.created_at,
        reverse=True,
    )[:limit]

    return [
        TaskStatusResponse(
            task_id=task.task_id,
            status=task.status.value,
            task_type=task.task_type.value,
            username=task.username,
            filename=task.filename,
            created_at=task.created_at,
            updated_at=task.updated_at,
            error=task.error,
            result=task.result,
            progress=task.progress,
        )
        for task in sorted_tasks
    ]


@router.post("/admin/cleanup")
async def cleanup_completed_tasks(username: str = Depends(verify_token)):
    """Admin endpoint to clean up old completed tasks (stub for now)."""
    # This would be an admin-only endpoint in production
    task_manager = get_task_manager()

    # Count tasks before cleanup
    user_tasks = task_manager.get_user_tasks(username)
    completed_tasks = [t for t in user_tasks if t.status == TaskStatus.COMPLETED]

    # In a real implementation, we'd delete old completed tasks
    # For now, just return the count
    return {
        "message": "Cleanup check completed",
        "total_tasks": len(user_tasks),
        "completed_tasks": len(completed_tasks),
        "note": "Cleanup not yet implemented",
    }
