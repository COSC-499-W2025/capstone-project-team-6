"""Resume generation API endpoints."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.analysis_database import (get_all_analyses_for_user,
                                       get_analysis_by_uuid)
from backend.api.auth import verify_token

router = APIRouter(prefix="/api", tags=["Resume"])


class ResumeRequest(BaseModel):
    """Request to generate a resume."""

    portfolio_ids: List[str] = Field(..., description="List of portfolio UUIDs to include")
    format: str = Field("markdown", description="Output format: markdown, pdf, html")
    include_skills: bool = Field(True, description="Include skills section")
    include_projects: bool = Field(True, description="Include projects section")
    max_projects: Optional[int] = Field(None, description="Maximum number of projects to include")


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
    """Generate a resume from selected portfolios."""
    try:
        from backend.analysis.resume_generator import generate_resume
        import base64

        # Validate all portfolios exist and belong to user
        portfolios = []
        for portfolio_id in request.portfolio_ids:
            analysis = get_analysis_by_uuid(portfolio_id, username)
            if not analysis:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Portfolio {portfolio_id} not found or access denied",
                )
            portfolios.append(analysis)

        # Generate resume
        resume_content = generate_resume(
            portfolios=portfolios,
            format=request.format,
            include_skills=request.include_skills,
            include_projects=request.include_projects,
            max_projects=request.max_projects,
        )

        # Convert PDF bytes to base64 string for JSON response
        if request.format == "pdf" and isinstance(resume_content, bytes):
            resume_content = base64.b64encode(resume_content).decode('utf-8')

        # Generate resume ID (in production, save to database)
        import uuid

        resume_id = str(uuid.uuid4())

        return ResumeResponse(
            resume_id=resume_id,
            format=request.format,
            content=resume_content,
            metadata={
                "username": username,
                "portfolio_count": len(portfolios),
                "total_projects": sum(p["total_projects"] for p in portfolios),
                "generated_at": __import__("datetime").datetime.now().isoformat(),
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
    # This is a stub - in production, fetch from database
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
    # This is a stub - in production, update in database
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Resume editing not yet implemented. Generate a new resume instead.",
    )
