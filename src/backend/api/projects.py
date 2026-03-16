"""Project-related API endpoints."""

import logging
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

from fastapi import (APIRouter, Depends, File, HTTPException, Request,
                     UploadFile, status)
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel

from backend.analysis_database import (get_analysis_by_uuid,
                                       get_project_by_path_and_portfolio,
                                       update_project_thumbnail)
from backend.api.auth import verify_token
from backend.api.portfolios import upload_new_portfolio
from backend.curation import get_user_projects

router = APIRouter(prefix="/api", tags=["Projects"])

# Configuration for thumbnail uploads
THUMBNAIL_UPLOAD_DIR = Path(__file__).parent.parent / "uploads" / "project_thumbnails"
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_THUMBNAIL_SIZE_MB = 5


class ProjectDetail(BaseModel):
    """Detailed project information."""

    name: str
    path: str
    metadata: Dict[str, Any]
    thumbnail_url: Optional[str] = None


class ThumbnailUploadResponse(BaseModel):
    """Response after uploading a thumbnail."""

    message: str
    thumbnail_url: str
    project_id: str


class SkillInfo(BaseModel):
    """Aggregated skill information."""

    skill: str
    count: int
    projects: List[str]


@router.get("/projects", operation_id="list_all_projects")
async def list_all_projects(username: str = Depends(verify_token)):
    """List all projects across all portfolios for authenticated user."""
    projects = get_user_projects(username)
    return {
        "username": username,
        "total_projects": len(projects),
        "projects": projects,
    }


@router.get("/projects/{project_id}", operation_id="get_project_detail")
async def get_project_detail(project_id: str, username: str = Depends(verify_token)):
    """Get detailed information about a specific project."""
    # Project ID format: {portfolio_uuid}:{project_path}
    if ":" not in project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid project_id format. Expected format: {portfolio_uuid}:{project_path}",
        )

    portfolio_uuid, project_path = project_id.split(":", 1)

    # Get the portfolio
    analysis = get_analysis_by_uuid(portfolio_uuid, username)
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio {portfolio_uuid} not found",
        )

    # Find the project
    projects = analysis.get("projects", [])
    project = None
    for p in projects:
        if p.get("path") == project_path:
            project = p
            break

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_path} not found in portfolio {portfolio_uuid}",
        )

    # Get thumbnail if available
    project_db_row = get_project_by_path_and_portfolio(portfolio_uuid, project_path, username)
    thumbnail_url = None
    if project_db_row and project_db_row["thumbnail_image_path"]:
        thumbnail_url = f"/api/projects/{project_id}/thumbnail"

    return ProjectDetail(
        name=project.get("name", ""),
        path=project.get("path", ""),
        metadata=project.get("metadata", {}),
        thumbnail_url=thumbnail_url,
    )


# Alias for upload endpoint (redirects to portfolios/upload)
@router.post("/projects/upload", status_code=202, operation_id="upload_project_alias")
async def upload_project_alias(
    request: Request,
    username: str = Depends(verify_token),
):
    """Accept project upload and forward to /api/portfolios/upload logic."""
    return await upload_new_portfolio(request, username)


@router.get("/skills", operation_id="get_aggregated_skills")
async def get_aggregated_skills(username: str = Depends(verify_token)):
    """Get aggregated skills across all projects for authenticated user."""
    from ..analysis_database import get_connection

    projects = get_user_projects(username)

    # Aggregate skills from project_skills table
    skills_map: Dict[str, Dict[str, Any]] = {}

    for project in projects:
        project_id = project.get("id")
        project_name = project.get("project_name") or project.get("name", "Unknown")
        metadata = project.get("metadata", {})
        skills_from_metadata = metadata.get("skills", [])

        if skills_from_metadata:
            for skill in skills_from_metadata:
                if skill not in skills_map:
                    skills_map[skill] = {"skill": skill, "count": 0, "projects": []}
                skills_map[skill]["count"] += 1
                if project_name not in skills_map[skill]["projects"]:
                    skills_map[skill]["projects"].append(project_name)
        elif project_id:
            with get_connection() as conn:
                skills_rows = conn.execute("SELECT skill FROM project_skills WHERE project_id = ?", (project_id,)).fetchall()
                for row in skills_rows:
                    skill = row["skill"]
                    if skill not in skills_map:
                        skills_map[skill] = {"skill": skill, "count": 0, "projects": []}
                    skills_map[skill]["count"] += 1
                    if project_name not in skills_map[skill]["projects"]:
                        skills_map[skill]["projects"].append(project_name)

    # Convert to list and sort by count
    skills_list = sorted(
        skills_map.values(),
        key=lambda x: x["count"],
        reverse=True,
    )

    return {
        "username": username,
        "total_skills": len(skills_list),
        "skills": skills_list,
    }


@router.post("/projects/{project_id}/thumbnail", response_model=ThumbnailUploadResponse, operation_id="upload_project_thumbnail")
async def upload_project_thumbnail(
    project_id: str,
    file: UploadFile = File(..., description="Thumbnail image file (JPG, PNG, GIF, WebP)"),
    username: str = Depends(verify_token),
):
    """Upload a thumbnail image for a specific project.

    The project_id should be in format: {portfolio_uuid}:{project_path}
    """
    # Parse project_id
    if ":" not in project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid project_id format. Expected format: {portfolio_uuid}:{project_path}",
        )

    portfolio_uuid, project_path = project_id.split(":", 1)

    # Verify project exists and user has access
    project_db_row = get_project_by_path_and_portfolio(portfolio_uuid, project_path, username)
    if not project_db_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project not found or access denied",
        )

    # Validate file type
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided",
        )

    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}",
        )

    # Read and validate file size
    content = await file.read()
    file_size_mb = len(content) / (1024 * 1024)
    if file_size_mb > MAX_THUMBNAIL_SIZE_MB:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size ({file_size_mb:.2f}MB) exceeds maximum allowed size ({MAX_THUMBNAIL_SIZE_MB}MB)",
        )

    # Create thumbnails directory if it doesn't exist
    THUMBNAIL_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # Get old thumbnail path before uploading new one
    old_thumbnail_path = project_db_row["thumbnail_image_path"]

    # Generate unique filename to avoid conflicts
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = THUMBNAIL_UPLOAD_DIR / unique_filename

    # Save the file
    try:
        file_path.write_bytes(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save thumbnail: {str(e)}",
        )

    # Update database with thumbnail path
    relative_path = f"uploads/project_thumbnails/{unique_filename}"
    success = update_project_thumbnail(project_db_row["id"], relative_path)

    if not success:
        # Clean up uploaded file if database update fails
        file_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update project thumbnail in database",
        )

    # Delete old thumbnail file to prevent orphaned files
    if old_thumbnail_path:
        old_full_path = Path(__file__).parent.parent / old_thumbnail_path
        # Validate path to prevent directory traversal
        try:
            old_full_path = old_full_path.resolve()
            if THUMBNAIL_UPLOAD_DIR.resolve() in old_full_path.parents or old_full_path.parent == THUMBNAIL_UPLOAD_DIR.resolve():
                if old_full_path.exists():
                    old_full_path.unlink()
            else:
                logger.warning(f"Attempted to delete file outside thumbnail directory: {old_full_path}")
        except Exception as e:
            # Log but don't fail - the new thumbnail was uploaded successfully
            logger.error(f"Failed to delete old thumbnail {old_thumbnail_path}: {e}")

    thumbnail_url = f"/api/projects/{project_id}/thumbnail"

    return ThumbnailUploadResponse(
        message="Thumbnail uploaded successfully",
        thumbnail_url=thumbnail_url,
        project_id=project_id,
    )


@router.get("/projects/{project_id}/thumbnail")
async def get_project_thumbnail(project_id: str, username: str = Depends(verify_token)):
    """Get the thumbnail image for a specific project.

    Returns the actual image file.
    """
    # Parse project_id
    if ":" not in project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid project_id format. Expected format: {portfolio_uuid}:{project_path}",
        )

    portfolio_uuid, project_path = project_id.split(":", 1)

    # Verify project exists and user has access
    project_db_row = get_project_by_path_and_portfolio(portfolio_uuid, project_path, username)
    if not project_db_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied",
        )

    # Get thumbnail path
    thumbnail_path = project_db_row["thumbnail_image_path"]
    if not thumbnail_path:
        return Response(status_code=204)

    # Construct full file path and validate to prevent directory traversal
    full_path = (Path(__file__).parent.parent / thumbnail_path).resolve()

    # Ensure the path is within the thumbnail upload directory
    if THUMBNAIL_UPLOAD_DIR.resolve() not in full_path.parents and full_path.parent != THUMBNAIL_UPLOAD_DIR.resolve():
        logger.warning(f"Attempted directory traversal in get_thumbnail: {thumbnail_path}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid thumbnail path",
        )

    if not full_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thumbnail file not found on disk",
        )

    # Determine media type from file extension
    media_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    file_ext = full_path.suffix.lower()
    media_type = media_types.get(file_ext, "application/octet-stream")

    return FileResponse(full_path, media_type=media_type)


@router.delete("/projects/{project_id}/thumbnail")
async def delete_project_thumbnail(project_id: str, username: str = Depends(verify_token)):
    """Delete the thumbnail image for a specific project."""
    # Parse project_id
    if ":" not in project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid project_id format. Expected format: {portfolio_uuid}:{project_path}",
        )

    portfolio_uuid, project_path = project_id.split(":", 1)

    # Verify project exists and user has access
    project_db_row = get_project_by_path_and_portfolio(portfolio_uuid, project_path, username)
    if not project_db_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied",
        )

    # Get current thumbnail path
    thumbnail_path = project_db_row["thumbnail_image_path"]
    if not thumbnail_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No thumbnail set for this project",
        )

    # Delete the file from disk with path validation
    full_path = (Path(__file__).parent.parent / thumbnail_path).resolve()

    # Ensure the path is within the thumbnail upload directory
    if THUMBNAIL_UPLOAD_DIR.resolve() not in full_path.parents and full_path.parent != THUMBNAIL_UPLOAD_DIR.resolve():
        logger.warning(f"Attempted directory traversal in delete_thumbnail: {thumbnail_path}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid thumbnail path",
        )

    if full_path.exists():
        try:
            full_path.unlink()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete thumbnail file: {str(e)}",
            )

    # Update database to remove thumbnail reference
    success = update_project_thumbnail(project_db_row["id"], None)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update database",
        )

    return {"message": "Thumbnail deleted successfully", "project_id": project_id}
