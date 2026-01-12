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
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from . import authenticate_user, create_user
# from .analysis_database import (
#     get_all_analyses_for_user,
#     get_analysis_by_uuid,
#     init_db as init_analysis_db,
# )
from .database import check_user_consent
from .database import init_db as init_user_db

# Initialize databases
init_user_db()
# init_analysis_db()

app = FastAPI(
    description="API for Portfolio and Resume generation with incremental uploads",
    version="2.0.0",
)

security = HTTPBearer()

active_tokens: Dict[str, Dict[str, Any]] = {}


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


class PortfolioDetail(BaseModel):
    analysis_uuid: str
    analysis_type: str
    zip_file: str
    analysis_timestamp: str
    total_projects: int
    projects: List[Dict[str, Any]]
    skills: List[Dict[str, Any]]
    summary: Optional[Dict[str, Any]] = None


class IncrementalUploadRequest(BaseModel):
    portfolio_id: str = Field(..., description="UUID of existing portfolio to add to")


class MessageResponse(BaseModel):
    message: str
    details: Optional[Dict[str, Any]] = None


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
        from .database import UserAlreadyExistsError

        create_user(credentials.username, credentials.password)
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

    return PortfolioDetail(
        analysis_uuid=analysis["analysis_uuid"],
        analysis_type=analysis["analysis_type"],
        zip_file=analysis["zip_file"],
        analysis_timestamp=analysis["analysis_timestamp"],
        total_projects=analysis["total_projects"],
        projects=analysis.get("projects", []),
        skills=analysis.get("skills", []),
        summary=analysis.get("summary"),
    )


@app.post("/api/portfolios/upload", status_code=202)
async def upload_new_portfolio(
    file: UploadFile = File(..., description="ZIP file containing project"),
    analysis_type: str = Form("llm", description="Analysis type: llm or non_llm"),
    username: str = Depends(verify_token),
):
    """Upload a new portfolio (create new analysis).
    Returns immediately with task ID.
    """
    # Verify user consent
    if not check_user_consent(username):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User consent required. Please provide consent before uploading.",
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

    # TODO: Queue for background processing
    # For now, return task ID

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
    username: str = Depends(verify_token),
):
    """Add incremental data to an existing portfolio"""
    # Verify portfolio exists and belongs to user
    existing = get_analysis_by_uuid(portfolio_id, username)  # to be implemented
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio {portfolio_id} not found or access denied",
        )

    # Verify user consent
    if not check_user_consent(username):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User consent required",
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

    # TODO: Queue for background processing with portfolio_id

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
    from .analysis_database import delete_analysis

    # Verify ownership
    existing = get_analysis_by_uuid(portfolio_id, username)  # to be implemented
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio {portfolio_id} not found",
        )

    delete_analysis(portfolio_id, username)

    return MessageResponse(
        message=f"Portfolio {portfolio_id} deleted successfully",
    )


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "MDA Portfolio API",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/api/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
