"""Resume generation API endpoints."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.analysis_database import (
    get_projects_for_user,
    get_resume_items_for_project_id,
    get_portfolio_item_for_project,
)
from backend.api.auth import verify_token

router = APIRouter(prefix="/api", tags=["Resume"])


class ResumeRequest(BaseModel):
    """Request to generate a resume."""

    project_ids: List[int] = Field(..., description="List of project IDs to include")
    format: str = Field("markdown", description="Output format: markdown, pdf, latex")
    include_skills: bool = Field(True, description="Include skills section")
    include_projects: bool = Field(True, description="Include projects section")
    max_projects: Optional[int] = Field(None, description="Maximum number of projects to include")
    personal_info: Optional[Dict[str, str]] = Field(
        None,
        description="Personal information (name, email, phone, location, linkedIn, github, website)",
    )


class ResumeResponse(BaseModel):
    """Generated resume response."""

    resume_id: str
    format: str
    content: str
    metadata: Dict[str, Any]


class ResumeEditRequest(BaseModel):
    """Request to edit a resume."""

    content: str
    metadata: Optional[Dict[str, Any]] = None


@router.post("/resume/generate", response_model=ResumeResponse)
async def generate_resume(
    request: ResumeRequest,
    username: str = Depends(verify_token),
):
    """Generate a resume from selected projects."""
    try:
        import base64
        import uuid
        from datetime import datetime

        # 1) Load user's projects once (ownership validation)
        user_projects = get_projects_for_user(username)
        user_projects_by_id = {p["id"]: p for p in user_projects}

        # 2) Validate project ownership
        missing = [pid for pid in request.project_ids if pid not in user_projects_by_id]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project(s) not found or access denied: {missing}",
            )

        # 3) Build projects 
        projects_for_resume: List[Dict[str, Any]] = []

        for pid in request.project_ids:
            project_row = user_projects_by_id[pid]

            resume_rows_raw = get_resume_items_for_project_id(pid)
            resume_rows = [dict(r) for r in resume_rows_raw]  # ensure dict

            portfolio_item = get_portfolio_item_for_project(pid) or {}

            projects_for_resume.append({
                "project": project_row,       
                "resume_items": resume_rows,  
                "portfolio": portfolio_item,  
            })

        # 4) Generate resume using the existing generator 
        from backend.analysis.resume_generator import generate_resume as generate_resume_impl

        resume_content = generate_resume_impl(
            projects=projects_for_resume,
            format=request.format,
            include_skills=request.include_skills,
            include_projects=request.include_projects,
            max_projects=request.max_projects,
            personal_info=request.personal_info,
        )

        # Convert PDF bytes to base64 string for JSON response
        if request.format in ("pdf", "latex") and isinstance(resume_content, bytes):
            resume_content = base64.b64encode(resume_content).decode("utf-8")

        resume_id = str(uuid.uuid4())

        return ResumeResponse(
            resume_id=resume_id,
            format=request.format,
            content=resume_content,
            metadata={
                "username": username,
                "project_count": len(projects_for_resume),
                "total_projects": len(user_projects),
                "generated_at": datetime.now().isoformat(),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate resume: {str(e)}",
        )


@router.get("/resume/{resume_id}", response_model=ResumeResponse)
async def get_resume(resume_id: str, username: str = Depends(verify_token)):
    """Get a previously generated resume by ID (stub - needs database implementation)."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Resume retrieval not yet implemented. Resumes are currently ephemeral.",
    )


@router.post("/resume/{resume_id}/edit", response_model=ResumeResponse)
async def edit_resume(
    resume_id: str,
    edit_request: ResumeEditRequest,
    username: str = Depends(verify_token),
):
    """Edit a previously generated resume (stub - needs database implementation)."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Resume editing not yet implemented. Generate a new resume instead.",
    )
