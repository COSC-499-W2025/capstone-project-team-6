"""Curation API endpoints for project management and customization."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from backend.api.auth import verify_token
from backend.curation import (
    ATTRIBUTE_DESCRIPTIONS,
    DEFAULT_COMPARISON_ATTRIBUTES,
    get_available_skills_alphabetical,
    get_chronology_corrections,
    get_showcase_projects,
    get_user_curation_settings,
    get_user_projects,
    save_chronology_correction,
    save_comparison_attributes,
    save_highlighted_skills,
    save_project_order,
    save_showcase_projects,
    validate_date_format,
)

router = APIRouter(prefix="/api/curation", tags=["Curation"])


# Pydantic Models
class CurationSettingsResponse(BaseModel):
    """User's curation settings."""

    user_id: str
    comparison_attributes: List[str]
    showcase_project_ids: List[int]
    custom_project_order: List[int]
    highlighted_skills: List[str]


class ProjectResponse(BaseModel):
    """Project information with effective dates."""

    id: int
    project_name: str
    primary_language: Optional[str] = None
    total_files: Optional[int] = None
    has_tests: bool = False
    effective_last_commit_date: Optional[str] = None
    effective_last_modified_date: Optional[str] = None
    effective_project_start_date: Optional[str] = None
    effective_project_end_date: Optional[str] = None
    correction_timestamp: Optional[str] = None
    languages: Dict[str, int] = {}
    frameworks: List[str] = []


class ChronologyRequest(BaseModel):
    """Request to update project chronology."""

    project_id: int
    last_commit_date: Optional[str] = None
    last_modified_date: Optional[str] = None
    project_start_date: Optional[str] = None
    project_end_date: Optional[str] = None

    @field_validator("last_commit_date", "last_modified_date", "project_start_date", "project_end_date")
    @classmethod
    def validate_date(cls, v):
        if v is not None and not validate_date_format(v):
            raise ValueError("Invalid date format. Use ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)")
        return v


class ShowcaseRequest(BaseModel):
    """Request to set showcase projects."""

    project_ids: List[int] = Field(..., min_length=0, max_length=3)


class AttributesRequest(BaseModel):
    """Request to set comparison attributes."""

    attributes: List[str] = Field(..., min_length=1)


class ProjectOrderRequest(BaseModel):
    """Request to set custom project order."""

    project_ids: List[int]


class SkillsRequest(BaseModel):
    """Request to set highlighted skills."""

    skills: List[str] = Field(..., min_length=0, max_length=10)


class MessageResponse(BaseModel):
    """Generic message response."""

    message: str
    success: bool = True


class AttributeInfo(BaseModel):
    """Information about a comparison attribute."""

    key: str
    description: str
    is_default: bool


# Endpoints
@router.get("/settings", response_model=CurationSettingsResponse)
async def get_curation_settings(username: str = Depends(verify_token)):
    """Get user's current curation settings."""
    settings = get_user_curation_settings(username)
    return CurationSettingsResponse(
        user_id=settings.user_id,
        comparison_attributes=settings.comparison_attributes,
        showcase_project_ids=settings.showcase_project_ids,
        custom_project_order=settings.custom_project_order,
        highlighted_skills=settings.highlighted_skills,
    )


@router.get("/projects", response_model=List[ProjectResponse])
async def get_projects_for_curation(username: str = Depends(verify_token)):
    """Get all projects for the user with effective dates and corrections."""
    projects = get_user_projects(username)

    return [
        ProjectResponse(
            id=p["id"],
            project_name=p["project_name"],
            primary_language=p.get("primary_language"),
            total_files=p.get("total_files"),
            has_tests=p.get("has_tests", False),
            effective_last_commit_date=p.get("effective_last_commit_date"),
            effective_last_modified_date=p.get("effective_last_modified_date"),
            effective_project_start_date=p.get("effective_project_start_date"),
            effective_project_end_date=p.get("effective_project_end_date"),
            correction_timestamp=p.get("correction_timestamp"),
            languages=p.get("languages", {}),
            frameworks=p.get("frameworks", []),
        )
        for p in projects
    ]


@router.get("/showcase", response_model=List[ProjectResponse])
async def get_showcase_projects_list(username: str = Depends(verify_token)):
    """Get user's showcase projects with full details."""
    projects = get_showcase_projects(username)

    return [
        ProjectResponse(
            id=p["id"],
            project_name=p["project_name"],
            primary_language=p.get("primary_language"),
            total_files=p.get("total_files"),
            has_tests=p.get("has_tests", False),
            effective_last_commit_date=p.get("effective_last_commit_date"),
            effective_last_modified_date=p.get("effective_last_modified_date"),
            effective_project_start_date=p.get("effective_project_start_date"),
            effective_project_end_date=p.get("effective_project_end_date"),
            languages=p.get("languages", {}),
            frameworks=p.get("frameworks", []),
        )
        for p in projects
    ]


@router.get("/skills", response_model=List[str])
async def get_available_skills(username: str = Depends(verify_token)):
    """Get all available skills alphabetically."""
    return get_available_skills_alphabetical()


@router.get("/attributes", response_model=List[AttributeInfo])
async def get_available_attributes(username: str = Depends(verify_token)):
    """Get all available comparison attributes."""
    attributes = []
    for key, description in ATTRIBUTE_DESCRIPTIONS.items():
        attributes.append(
            AttributeInfo(
                key=key,
                description=description,
                is_default=key in DEFAULT_COMPARISON_ATTRIBUTES,
            )
        )
    return sorted(attributes, key=lambda x: x.description)


@router.post("/chronology", response_model=MessageResponse)
async def update_chronology(
    request: ChronologyRequest,
    username: str = Depends(verify_token),
):
    """Save chronology corrections for a project."""
    success = save_chronology_correction(
        project_id=request.project_id,
        user_id=username,
        last_commit_date=request.last_commit_date,
        last_modified_date=request.last_modified_date,
        project_start_date=request.project_start_date,
        project_end_date=request.project_end_date,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to save chronology correction. Project may not exist.",
        )

    return MessageResponse(
        message="Chronology correction saved successfully",
        success=True,
    )


@router.post("/showcase", response_model=MessageResponse)
async def set_showcase_projects(
    request: ShowcaseRequest,
    username: str = Depends(verify_token),
):
    """Set showcase projects (max 3)."""
    try:
        success = save_showcase_projects(username, request.project_ids)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to save showcase projects",
            )

        return MessageResponse(
            message=f"Showcase projects updated ({len(request.project_ids)} selected)",
            success=True,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/attributes", response_model=MessageResponse)
async def set_comparison_attributes(
    request: AttributesRequest,
    username: str = Depends(verify_token),
):
    """Set comparison attributes."""
    try:
        success = save_comparison_attributes(username, request.attributes)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to save comparison attributes",
            )

        return MessageResponse(
            message=f"Comparison attributes updated ({len(request.attributes)} selected)",
            success=True,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/order", response_model=MessageResponse)
async def set_project_order(
    request: ProjectOrderRequest,
    username: str = Depends(verify_token),
):
    """Set custom project order."""
    success = save_project_order(username, request.project_ids)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to save project order",
        )

    return MessageResponse(
        message=f"Project order updated ({len(request.project_ids)} projects)",
        success=True,
    )


@router.post("/skills", response_model=MessageResponse)
async def set_highlighted_skills(
    request: SkillsRequest,
    username: str = Depends(verify_token),
):
    """Set highlighted skills (max 10)."""
    try:
        success = save_highlighted_skills(username, request.skills)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to save highlighted skills",
            )

        return MessageResponse(
            message=f"Highlighted skills updated ({len(request.skills)} selected)",
            success=True,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
