"""Project-related API endpoints."""
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.analysis_database import get_analysis_by_uuid
from backend.api.auth import verify_token
from backend.curation import get_user_projects

router = APIRouter(prefix="/api", tags=["Projects"])


class ProjectDetail(BaseModel):
    """Detailed project information."""
    name: str
    path: str
    metadata: Dict[str, Any]


class SkillInfo(BaseModel):
    """Aggregated skill information."""
    skill: str
    count: int
    projects: List[str]


@router.get("/projects")
async def list_all_projects(username: str = Depends(verify_token)):
    """List all projects across all portfolios for authenticated user."""
    projects = get_user_projects(username)
    return {
        "username": username,
        "total_projects": len(projects),
        "projects": projects,
    }


@router.get("/projects/{project_id}")
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

    return ProjectDetail(
        name=project.get("name", ""),
        path=project.get("path", ""),
        metadata=project.get("metadata", {}),
    )


# Alias for upload endpoint (redirects to portfolios/upload)
@router.post("/projects/upload", status_code=202)
async def upload_project_alias(username: str = Depends(verify_token)):
    """Alias for /api/portfolios/upload. Use that endpoint instead."""
    raise HTTPException(
        status_code=status.HTTP_308_PERMANENT_REDIRECT,
        detail="Use POST /api/portfolios/upload instead",
        headers={"Location": "/api/portfolios/upload"},
    )


@router.get("/skills")
async def get_aggregated_skills(username: str = Depends(verify_token)):
    """Get aggregated skills across all projects for authenticated user."""
    projects = get_user_projects(username)

    # Aggregate skills
    skills_map: Dict[str, Dict[str, Any]] = {}

    for project in projects:
        metadata = project.get("metadata", {})
        project_skills = metadata.get("skills", [])
        project_name = project.get("name", "Unknown")

        for skill in project_skills:
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
