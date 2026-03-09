from __future__ import annotations

import os
import tempfile
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import bcrypt
from fastapi import (Depends, FastAPI, File, Form, HTTPException, Security,
                     UploadFile, status)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.analysis_database import (delete_all_projects_for_user,
                                       delete_analysis,
                                       delete_project_for_user,
                                       get_all_analyses_for_user,
                                       get_analysis_by_uuid,
                                       get_portfolio_item_for_project,
                                       get_projects_for_user,
                                       get_resume_items_for_project_id)
from backend.analysis_database import init_db as init_analysis_db
from backend.analysis_database import record_analysis
# Import routers from modular API structure
from backend.api.analysis import router as analysis_router
from backend.api.auth import router as auth_router
from backend.api.curation import router as curation_router
from backend.api.health import router as health_router
from backend.api.portfolios import router as portfolios_router
from backend.api.projects import router as projects_router
from backend.api.resume import router as resume_router
from backend.api.tasks import router as tasks_router
from backend.curation import init_curation_tables
from backend.database import (authenticate_user, check_user_consent, create_user,
                              delete_user_account, save_user_consent,
                              seed_default_users)
from backend.database import init_db as init_user_db
from backend.task_manager import (TaskType, cleanup_background_tasks,
                                  get_task_manager)
from backend.token_storage import active_tokens

# Initialize databases
init_user_db()
init_analysis_db()
init_curation_tables()

app = FastAPI(
    title="Portfolio & Resume Generation API",
    description="API for Portfolio and Resume generation with incremental uploads",
    version="2.0.0",
)

# Configure CORS
cors_origins = os.environ.get("CORS_ORIGINS", "http://localhost:5173,http://localhost:8000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()


class UserCredentials(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    username: str


class PortfolioListItem(BaseModel):
    analysis_uuid: str
    zip_file: str
    analysis_timestamp: str
    total_projects: int
    analysis_type: str
    project_names: List[str] = Field(default_factory=list)


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


class IncrementalUploadRequest(BaseModel):
    portfolio_id: str = Field(..., description="UUID of existing portfolio to add to")


class MessageResponse(BaseModel):
    message: str
    details: Optional[Dict[str, Any]] = None


class ConsentRequest(BaseModel):
    has_consented: bool


class ConsentResponse(BaseModel):
    has_consented: bool
    message: str


def create_access_token(username: str) -> str:
    """Create a new access token for a user."""
    token = str(uuid.uuid4())
    active_tokens[token] = {
        "username": username,
        "created_at": datetime.now(),
        "expires_at": datetime.now() + timedelta(hours=24),
    }
    return token


def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    """Verify token and return username."""
    token = credentials.credentials

    if token not in active_tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    token_data = active_tokens[token]

    if datetime.now() > token_data["expires_at"]:
        del active_tokens[token]
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        )

    return token_data["username"]


@app.post("/api/auth/signup", response_model=TokenResponse, status_code=201)
async def signup(credentials: UserCredentials):
    """Register a new user and return access token."""
    try:
        from backend.database import UserAlreadyExistsError

        create_user(credentials.username, credentials.password)
        save_user_consent(credentials.username, False)  # Initial consent = false
        token = create_access_token(credentials.username)

        return TokenResponse(
            access_token=token,
            username=credentials.username,
        )
    except UserAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        )


@app.post("/api/auth/login", response_model=TokenResponse)
async def login(credentials: UserCredentials):
    """Login and return access token."""
    if authenticate_user(credentials.username, credentials.password):
        token = create_access_token(credentials.username)
        return TokenResponse(
            access_token=token,
            username=credentials.username,
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )


@app.post("/api/auth/logout")
async def logout(username: str = Depends(verify_token)):
    """Logout and invalidate token."""
    # Remove all tokens for this user
    tokens_to_remove = [token for token, data in active_tokens.items() if data["username"] == username]
    for token in tokens_to_remove:
        del active_tokens[token]

    return MessageResponse(message="Successfully logged out")

@app.delete("/api/user/account")
async def delete_account(username: str = Depends(verify_token)):
    """Delete the authenticated user's account and all associated data."""
    try:
        deleted = delete_user_account(username)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User account not found",
            )

        # Invalidate all active tokens for this user
        tokens_to_remove = [
            token for token, data in active_tokens.items()
            if data["username"] == username
        ]
        for token in tokens_to_remove:
            del active_tokens[token]

        return MessageResponse(message="Account deleted successfully")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete account: {str(e)}",
        )

@app.post("/api/user/consent", response_model=ConsentResponse)
async def save_consent(consent: ConsentRequest, username: str = Depends(verify_token)):
    """Save user consent status."""
    try:
        save_user_consent(username, consent.has_consented)
        message = "Consent saved successfully" if consent.has_consented else "Consent declined"
        return ConsentResponse(has_consented=consent.has_consented, message=message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save consent: {str(e)}",
        )


@app.get("/api/user/consent", response_model=ConsentResponse)
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


@app.get("/api/portfolios", response_model=List[PortfolioListItem])
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
        )
        for a in analyses
    ]


@app.get("/api/portfolios/{portfolio_id}", response_model=PortfolioDetail)
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


@app.post("/api/portfolios/upload", status_code=202)
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


@app.post("/api/portfolios/{portfolio_id}/add", status_code=202)
async def add_to_existing_portfolio(
    portfolio_id: str,
    file: UploadFile = File(..., description="ZIP file with additional projects"),
    analysis_type: str = Form("non_llm", description="Analysis type: llm or non_llm"),
    username: str = Depends(verify_token),
):
    """Add incremental data to an existing portfolio"""
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


@app.delete("/api/portfolios/{portfolio_id}")
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


@app.post("/api/admin/cleanup")
async def cleanup_system(username: str = Depends(verify_token)):
    """Clean up old tasks and temporary files. Admin endpoint."""
    # Simple admin check - in production, implement proper role-based access
    if username != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    cleanup_background_tasks()

    return MessageResponse(
        message="System cleanup completed",
        details={
            "timestamp": datetime.now().isoformat(),
            "cleaned_by": username,
        },
    )


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/api/info")
async def api_info():
    """API information endpoint."""
    return {
        "name": "MDA Portfolio API",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/api/health",
    }


# NOTE: /api/projects endpoint moved to backend/api/projects.py
# Uses get_user_projects() which includes composite_id for thumbnail API


@app.get("/api/projects/{project_id}/resume-items")
async def get_project_resume_items(
    project_id: int,
    username: str = Depends(verify_token),
) -> List[Dict[str, Any]]:
    try:
        # verify project belongs to this user (prevents data leakage)
        user_projects = get_projects_for_user(username)
        if not any(p["id"] == project_id for p in user_projects):
            raise HTTPException(status_code=404, detail="Project not found")

        rows = get_resume_items_for_project_id(project_id)
        return [dict(r) for r in rows]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve resume items: {str(e)}",
        )


@app.get("/api/projects/{project_id}/portfolio")
async def get_project_portfolio(
    project_id: int,
    username: str = Depends(verify_token),
) -> Dict[str, Any]:
    try:
        user_projects = get_projects_for_user(username)
        if not any(p["id"] == project_id for p in user_projects):
            raise HTTPException(status_code=404, detail="Project not found")

        item = get_portfolio_item_for_project(project_id)
        return item or {}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve portfolio item: {str(e)}",
        )


# Register all modular API routers (at the end to override old duplicate endpoints)
app.include_router(auth_router)
app.include_router(health_router)
app.include_router(portfolios_router)
app.include_router(projects_router)
app.include_router(analysis_router)
app.include_router(resume_router)
app.include_router(tasks_router)
app.include_router(curation_router)

# Mount static files for frontend (unified deployment)
frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

    # Serve index.html for all non-API routes (client-side routing)
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # Don't interfere with API routes
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API endpoint not found")

        # Try to serve the requested file
        file_path = frontend_dist / full_path
        if file_path.is_file():
            return FileResponse(file_path)

        # Otherwise serve index.html for client-side routing
        index_path = frontend_dist / "index.html"
        if index_path.exists():
            return FileResponse(index_path)

        raise HTTPException(status_code=404, detail="Frontend not built")


@app.delete("/api/projects/{project_id}")
async def delete_project(
    project_id: int,
    username: str = Depends(verify_token),
):
    try:
        ok = delete_project_for_user(project_id, username)
        if not ok:
            raise HTTPException(status_code=404, detail="Project not found")

        return MessageResponse(message=f"Project {project_id} deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete project: {str(e)}",
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


@app.delete("/api/projects")
async def delete_all_projects(username: str = Depends(verify_token)):
    """Delete all projects for the currently authenticated user."""
    try:
        deleted = delete_all_projects_for_user(username)
        return {
            "message": "All projects deleted successfully",
            "deleted_projects": deleted,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete all projects: {str(e)}",
        )
