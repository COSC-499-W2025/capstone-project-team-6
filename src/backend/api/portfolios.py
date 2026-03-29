"""Portfolio management API endpoints."""

import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import (APIRouter, Depends, File, Form, HTTPException, UploadFile,
                     Query, status)
from pydantic import BaseModel, Field

from backend.analysis_database import (delete_analysis,
                                       get_user_portfolio_settings,
                                       get_all_analyses_for_user,
                                       get_analysis_by_file_hash,
                                       get_analysis_by_uuid,
                                       get_public_portfolio_detail,
                                       list_public_portfolios,
                                       set_portfolio_visibility,
                                       upsert_user_portfolio_settings)
from backend.api.auth import verify_token
from backend.database import check_user_consent
from backend.task_manager import TaskType, get_task_manager

router = APIRouter(prefix="/api", tags=["Portfolios"])


class PortfolioListItem(BaseModel):
    analysis_uuid: str
    zip_file: str
    analysis_timestamp: str
    total_projects: int
    analysis_type: str
    project_names: List[str] = Field(default_factory=list)
    is_public: bool = False
    published_at: Optional[str] = None


class PortfolioDetail(BaseModel):
    analysis_uuid: str
    analysis_type: str
    zip_file: str
    analysis_timestamp: str
    total_projects: int
    projects: List[Dict[str, Any]]
    skills: List[Dict[str, Any]]
    summary: Optional[Dict[str, Any]] = None
    items: List[Dict[str, Any]] = Field(default_factory=list)
    portfolio_items: List[Dict[str, Any]] = Field(default_factory=list)


class MessageResponse(BaseModel):
    message: str
    details: Optional[Dict[str, Any]] = None


class ConsentRequest(BaseModel):
    has_consented: bool


class ConsentResponse(BaseModel):
    has_consented: bool
    message: str


class PortfolioVisibilityRequest(BaseModel):
    is_public: bool


class PortfolioVisibilityResponse(BaseModel):
    analysis_uuid: str
    is_public: bool
    message: str


class PublicPortfolioCard(BaseModel):
    analysis_uuid: str
    username: str
    analysis_type: str
    analysis_timestamp: str
    published_at: Optional[str] = None
    total_projects: int
    project_names: List[str] = Field(default_factory=list)
    project_types: List[str] = Field(default_factory=list)
    top_languages: List[str] = Field(default_factory=list)
    top_skills: List[str] = Field(default_factory=list)
    has_tests: bool = False


class PublicPortfolioListResponse(BaseModel):
    items: List[PublicPortfolioCard] = Field(default_factory=list)
    total: int
    page: int
    page_size: int


class PublicPortfolioDetail(BaseModel):
    analysis_uuid: str
    username: str
    analysis_type: str
    zip_file: str
    analysis_timestamp: str
    published_at: Optional[str] = None
    total_projects: int
    projects: List[Dict[str, Any]] = Field(default_factory=list)
    skills: List[Dict[str, Any]] = Field(default_factory=list)
    summary: Optional[Dict[str, Any]] = None
    portfolio_items: List[Dict[str, Any]] = Field(default_factory=list)
    portfolio_settings: Dict[str, Any] = Field(default_factory=dict)
    analysis_timestamps: List[str] = Field(default_factory=list)


class PortfolioSettingsRequest(BaseModel):
    settings: Dict[str, Any] = Field(default_factory=dict)


class PortfolioSettingsResponse(BaseModel):
    settings: Dict[str, Any] = Field(default_factory=dict)


@router.get("/portfolios", response_model=List[PortfolioListItem], operation_id="list_portfolios")
async def list_portfolios(username: str = Depends(verify_token)):
    """List all portfolios for the authenticated user."""
    analyses = get_all_analyses_for_user(username)

    return [
        PortfolioListItem(
            analysis_uuid=a["analysis_uuid"],
            zip_file=a["zip_file"],
            analysis_timestamp=a["analysis_timestamp"],
            total_projects=a["total_projects"],
            analysis_type=a["analysis_type"],
            project_names=a.get("project_names", []),
            is_public=bool(a.get("is_public")),
            published_at=a.get("published_at"),
        )
        for a in analyses
    ]


@router.get(
    "/portfolio/settings",
    response_model=PortfolioSettingsResponse,
    operation_id="get_portfolio_settings",
)
async def get_portfolio_settings(username: str = Depends(verify_token)):
    settings = get_user_portfolio_settings(username)
    return PortfolioSettingsResponse(settings=settings)


@router.post(
    "/portfolio/settings",
    response_model=PortfolioSettingsResponse,
    operation_id="save_portfolio_settings",
)
async def save_portfolio_settings(
    request: PortfolioSettingsRequest,
    username: str = Depends(verify_token),
):
    settings = upsert_user_portfolio_settings(username, request.settings)
    return PortfolioSettingsResponse(settings=settings)


@router.post(
    "/portfolios/{portfolio_id}/visibility",
    response_model=PortfolioVisibilityResponse,
    operation_id="set_portfolio_visibility",
)
async def update_portfolio_visibility(
    portfolio_id: str,
    request: PortfolioVisibilityRequest,
    username: str = Depends(verify_token),
):
    """Update whether a portfolio is publicly visible."""
    updated = set_portfolio_visibility(portfolio_id, username, request.is_public)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio {portfolio_id} not found",
        )

    return PortfolioVisibilityResponse(
        analysis_uuid=portfolio_id,
        is_public=request.is_public,
        message="Portfolio published successfully" if request.is_public else "Portfolio set to private",
    )


@router.get(
    "/portfolios/public",
    response_model=PublicPortfolioListResponse,
    operation_id="list_public_portfolios",
)
async def get_public_portfolios(
    q: Optional[str] = Query(None, description="Search text for user/projects/skills"),
    username: Optional[str] = Query(None, description="Username filter (partial match)"),
    project_type: Optional[str] = Query(None, description="Project type / role filter"),
    language: Optional[str] = Query(None, description="Primary language filter"),
    has_tests: Optional[bool] = Query(None, description="Whether projects with tests should be included"),
    sort: str = Query("newest", description="Sort mode: newest, oldest, projects_desc, username"),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=50),
    _: str = Depends(verify_token),
):
    """List public portfolios with search, filter, and pagination."""
    payload = list_public_portfolios(
        q=q,
        username=username,
        project_type=project_type,
        language=language,
        has_tests=has_tests,
        sort=sort,
        page=page,
        page_size=page_size,
    )
    return PublicPortfolioListResponse(**payload)


@router.get(
    "/portfolios/public/{portfolio_id}",
    response_model=PublicPortfolioDetail,
    operation_id="get_public_portfolio",
)
async def get_public_portfolio(
    portfolio_id: str,
    _: str = Depends(verify_token),
):
    """Get detail for a public portfolio."""
    detail = get_public_portfolio_detail(portfolio_id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Public portfolio {portfolio_id} not found",
        )
    return PublicPortfolioDetail(**detail)


@router.get("/portfolios/{portfolio_id}", response_model=PortfolioDetail, operation_id="get_portfolio")
async def get_portfolio(portfolio_id: str, username: str = Depends(verify_token)):
    """Get detailed information about a specific portfolio."""
    analysis = get_analysis_by_uuid(portfolio_id, username)

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio {portfolio_id} not found",
        )

    portfolio_items = analysis.get("portfolio_items")
    if not isinstance(portfolio_items, list):
        portfolio_items = []

    return PortfolioDetail(
        analysis_uuid=analysis["analysis_uuid"],
        analysis_type=analysis["analysis_type"],
        zip_file=analysis["zip_file"],
        analysis_timestamp=analysis["analysis_timestamp"],
        total_projects=analysis["total_projects"],
        projects=analysis.get("projects", []),
        skills=analysis.get("skills", []),
        summary=analysis.get("summary"),
        items=portfolio_items,
        portfolio_items=portfolio_items,
    )


# Alias for GET portfolio
@router.get("/portfolio/{portfolio_id}", response_model=PortfolioDetail, operation_id="get_portfolio_alias")
async def get_portfolio_alias(portfolio_id: str, username: str = Depends(verify_token)):
    """Get detailed information about a specific portfolio (alias)."""
    return await get_portfolio(portfolio_id, username)


@router.post("/portfolios/upload", status_code=202, operation_id="upload_new_portfolio")
async def upload_new_portfolio(
    file: UploadFile = File(..., description="ZIP file containing project"),
    analysis_type: str = Form("llm", description="Analysis type: llm or non_llm"),
    project_name: Optional[str] = Form(None, description="User-provided project name (for single project)"),
    username: str = Depends(verify_token),
):
    """Upload a new portfolio (create new analysis).
    Returns immediately with task ID.
    """
    # Require consent only for LLM analysis; non_llm works without consent
    if analysis_type == "llm" and not check_user_consent(username):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Consent required for LLM analysis. Use non_llm or provide consent in Settings.",
        )

    # Validate file type
    if not file.filename or not file.filename.endswith(".zip"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a ZIP file",
        )

    # Validate analysis type
    if analysis_type not in ["llm", "non_llm"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="analysis_type must be 'llm' or 'non_llm'",
        )

    # Save uploaded file temporarily
    task_id = str(uuid.uuid4())
    temp_dir = Path(tempfile.gettempdir()) / f"mda_upload_{task_id}"
    temp_dir.mkdir(exist_ok=True)

    zip_path = temp_dir / file.filename

    try:
        content = await file.read()
        zip_path.write_bytes(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save uploaded file: {str(e)}",
        )

    # Early-exit: if the same ZIP content was already analysed for this user, return immediately
    from backend.task_manager import FileManager

    _file_hash = FileManager().calculate_file_hash(zip_path)
    existing = get_analysis_by_file_hash(_file_hash, username)
    has_projects = existing is not None and (existing["total_projects"] or 0) > 0
    print(f"[DUPLICATE CHECK] user={username!r} hash={_file_hash!r} existing={existing is not None} has_projects={has_projects}")
    if has_projects:
        shutil.rmtree(temp_dir, ignore_errors=True)
        return MessageResponse(
            message="Duplicate upload: returning existing analysis",
            details={
                "analysis_uuid": existing["analysis_uuid"],
                "total_projects": existing["total_projects"],
                "duplicate": True,
                "status": "completed",
            },
        )

    # Queue for background processing
    task_manager = get_task_manager()
    task_id = task_manager.create_task(
        task_type=TaskType.NEW_PORTFOLIO,
        username=username,
        filename=file.filename,
        file_path=zip_path,
        analysis_type=analysis_type,
        project_name=project_name.strip() if project_name and project_name.strip() else None,
    )

    return MessageResponse(
        message="Upload accepted, processing started",
        details={
            "task_id": task_id,
            "filename": file.filename,
            "analysis_type": analysis_type,
            "status": "processing",
            "status_url": f"/api/tasks/{task_id}",
        },
    )


@router.post("/portfolios/{portfolio_id}/add", status_code=202, operation_id="add_to_existing_portfolio")
async def add_to_existing_portfolio(
    portfolio_id: str,
    file: UploadFile = File(..., description="ZIP file with additional projects"),
    analysis_type: str = Form("non_llm", description="Analysis type: llm or non_llm"),
    username: str = Depends(verify_token),
):
    """Add incremental information to an existing portfolio."""
    # Verify portfolio exists and belongs to user
    existing = get_analysis_by_uuid(portfolio_id, username)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio {portfolio_id} not found or access denied",
        )

    # Require consent only for LLM analysis
    if analysis_type == "llm" and not check_user_consent(username):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Consent required for LLM analysis. Use non_llm or provide consent in Settings.",
        )

    # Validate file type
    if not file.filename or not file.filename.endswith(".zip"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a ZIP file",
        )

    # Save uploaded file temporarily
    task_id = str(uuid.uuid4())
    temp_dir = Path(tempfile.gettempdir()) / f"mda_incremental_{task_id}"
    temp_dir.mkdir(exist_ok=True)

    zip_path = temp_dir / file.filename

    try:
        content = await file.read()
        zip_path.write_bytes(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save uploaded file: {str(e)}",
        )

    # Queue for background processing with portfolio_id
    task_manager = get_task_manager()
    task_id = task_manager.create_task(
        task_type=TaskType.INCREMENTAL_UPLOAD,
        username=username,
        filename=file.filename,
        file_path=zip_path,
        portfolio_id=portfolio_id,
    )

    return MessageResponse(
        message="Incremental upload accepted, merging with existing portfolio",
        details={
            "task_id": task_id,
            "portfolio_id": portfolio_id,
            "filename": file.filename,
            "status": "processing",
            "status_url": f"/api/tasks/{task_id}",
        },
    )


@router.delete("/portfolios/{portfolio_id}", operation_id="delete_portfolio")
async def delete_portfolio(portfolio_id: str, username: str = Depends(verify_token)):
    """Delete a portfolio and all associated data."""

    # Verify ownership
    existing = get_analysis_by_uuid(portfolio_id, username)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio {portfolio_id} not found",
        )

    success = delete_analysis(portfolio_id, username)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete portfolio {portfolio_id}",
        )

    return MessageResponse(
        message=f"Portfolio {portfolio_id} deleted successfully",
    )


# Consent endpoints (kept with portfolios for now)
@router.post("/user/consent", response_model=ConsentResponse, operation_id="save_consent")
async def save_consent(consent: ConsentRequest, username: str = Depends(verify_token)):
    """Save user consent status."""
    try:
        from backend.database import save_user_consent

        save_user_consent(username, consent.has_consented)
        message = "Consent saved successfully" if consent.has_consented else "Consent declined"
        return ConsentResponse(has_consented=consent.has_consented, message=message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save consent: {str(e)}",
        )


@router.post("/privacy-consent", response_model=ConsentResponse, operation_id="save_privacy_consent")
async def save_privacy_consent(consent: ConsentRequest, username: str = Depends(verify_token)):
    """Save user privacy consent status."""
    return await save_consent(consent, username)


@router.get("/user/consent", response_model=ConsentResponse, operation_id="get_consent")
async def get_consent(username: str = Depends(verify_token)):
    """Get user consent status."""
    try:
        has_consented = check_user_consent(username)
        message = "User has consented" if has_consented else "User has not consented"
        return ConsentResponse(has_consented=has_consented, message=message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve consent: {str(e)}",
        )


@router.post("/portfolio/generate", operation_id="generate_portfolio_document")
async def generate_portfolio_document(
    portfolio_id: str,
    username: str = Depends(verify_token),
) -> Dict[str, Any]:
    """Generate a formatted portfolio document (PDF/HTML) from a portfolio."""
    try:
        from backend.analysis.portfolio_item_generator import \
            generate_portfolio_items

        analysis = get_analysis_by_uuid(portfolio_id, username)
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Portfolio {portfolio_id} not found",
            )

        portfolio_items = generate_portfolio_items(analysis)

        return {
            "portfolio_id": portfolio_id,
            "items": portfolio_items,
            "total_items": len(portfolio_items),
            "message": "Portfolio document generated successfully",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate portfolio: {str(e)}",
        )
