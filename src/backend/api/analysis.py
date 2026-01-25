"""Analysis pipeline API endpoints."""

import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import (APIRouter, Depends, File, Form, HTTPException, UploadFile,
                     status)
from pydantic import BaseModel

from backend.analysis_database import get_analysis_by_uuid
from backend.api.auth import verify_token
from backend.database import check_user_consent
from backend.task_manager import TaskType, get_task_manager, TaskType

router = APIRouter(prefix="/api/analysis", tags=["Analysis"])


class AnalysisRequest(BaseModel):
    """Request to trigger analysis on an existing portfolio."""

    portfolio_id: str
    analysis_type: str = "llm"  # llm or non_llm
    force_reanalysis: bool = False


class QuickAnalysisRequest(BaseModel):
    """Request for quick analysis (without storing as portfolio)."""

    analysis_type: str = "llm"


class AnalysisResponse(BaseModel):
    """Response from analysis request."""

    task_id: str
    portfolio_id: Optional[str] = None
    status: str
    message: str
    status_url: str


@router.post("/portfolios/{portfolio_id}/reanalyze", status_code=202, response_model=AnalysisResponse)
async def reanalyze_portfolio(
    portfolio_id: str,
    analysis_type: str = Form("llm", description="Analysis type: llm or non_llm"),
    username: str = Depends(verify_token),
):
    """Re-run analysis on an existing portfolio.

    Useful when:
    - Analysis failed previously
    - New analysis features are available
    - Want to switch between llm and non_llm analysis types
    """
    # Verify portfolio exists and belongs to user
    analysis = get_analysis_by_uuid(portfolio_id, username)
    if not analysis:
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

    # Validate analysis type
    if analysis_type not in ["llm", "non_llm"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="analysis_type must be 'llm' or 'non_llm'",
        )

    # Get the original file path from analysis metadata
    zip_file = analysis.get("zip_file", "")

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Portfolio reanalysis not yet implemented. Original files are not retained. "
        "Please upload the ZIP file again as a new portfolio or use incremental upload.",
    )


@router.post("/quick", status_code=200)
async def quick_analysis(
    file: UploadFile = File(..., description="ZIP file to analyze (not stored as portfolio)"),
    analysis_type: str = Form("non_llm", description="Analysis type: llm or non_llm"),
    username: str = Depends(verify_token),
):
    """Perform quick analysis on uploaded file without creating a portfolio.

    Useful for:
    - Preview analysis before creating portfolio
    - One-time analysis without storage
    - Testing analysis pipeline

    Results are returned immediately (not stored in database).
    """
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

    # Validate analysis type
    if analysis_type not in ["llm", "non_llm"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="analysis_type must be 'llm' or 'non_llm'",
        )

    # Save file temporarily
    temp_id = str(uuid.uuid4())
    temp_dir = Path(tempfile.gettempdir()) / f"mda_quick_{temp_id}"
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

    # Run analysis directly (synchronously)
    try:
        from backend.cli import analyze_folder

        # Use quick_mode=True for faster analysis
        results = analyze_folder(zip_path, target_user_email=None, quick_mode=True)

        # Clean up temp file
        import shutil

        shutil.rmtree(temp_dir)

        return {
            "status": "completed",
            "analysis_type": analysis_type,
            "results": results,
            "message": "Quick analysis completed. Results are not stored.",
        }
    except Exception as e:
        # Clean up on error
        import shutil

        if temp_dir.exists():
            shutil.rmtree(temp_dir)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}",
        )


@router.get("/status")
async def get_analysis_status(username: str = Depends(verify_token)):
    """Get overall analysis pipeline status and statistics."""
    from backend.task_manager import get_task_manager

    task_manager = get_task_manager()
    user_tasks = task_manager.get_user_tasks(username)

    # Calculate statistics
    total_tasks = len(user_tasks)
    completed = sum(1 for t in user_tasks if t.status.value == "completed")
    failed = sum(1 for t in user_tasks if t.status.value == "failed")
    running = sum(1 for t in user_tasks if t.status.value == "running")
    pending = sum(1 for t in user_tasks if t.status.value == "pending")

    return {
        "status": "operational",
        "statistics": {
            "total_analyses": total_tasks,
            "completed": completed,
            "failed": failed,
            "running": running,
            "pending": pending,
        },
        "message": "Analysis pipeline is operational",
    }


@router.post("/portfolios/{portfolio_id}/start")
async def start_portfolio_analysis(
    portfolio_id: str,
    username: str = Depends(verify_token),
):
    """
    Starts background analysis for an existing portfolio.

    For now, we use a FIXED zip path.
    Later, replace FIXED_ZIP_PATH with a DB lookup:
      - fetch stored zip path by (portfolio_id, username)
    """
    # 1) Validate portfolio exists for this user
    existing = get_analysis_by_uuid(portfolio_id, username)
    if not existing:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    # 2) TEMP: fixed path (replace with DB lookup later)
    FIXED_ZIP_PATH = Path(r"C:/path/to/your/project.zip")  # Update this path accordingly
    if not FIXED_ZIP_PATH.exists():
        raise HTTPException(
            status_code=400,
            detail=f"Zip file not found on server: {FIXED_ZIP_PATH}",
        )

    # 3) Create background task
    task_manager = get_task_manager()

    task_id = task_manager.create_task(
        task_type=TaskType.INCREMENTAL_UPLOAD,
        username=username,
        filename=FIXED_ZIP_PATH.name,
        file_path=FIXED_ZIP_PATH,
        analysis_type="non_llm",          # keep consistent with your pipeline defaults
        portfolio_id=portfolio_id,        # required for INCREMENTAL_UPLOAD
    )

    # 4) Return task_id so frontend can poll /api/tasks/{task_id}
    return {
        "task_id": task_id,
        "portfolio_id": portfolio_id,
        "status_url": f"/api/tasks/{task_id}",
    }


@router.post("/start")
async def start_new_analysis(
    username: str = Depends(verify_token),
):
    """
    Starts background analysis as a NEW portfolio.

    For now: uses a fixed zip path on the SERVER.
    Later: replace FIXED_ZIP_PATH with a DB lookup of the uploaded file for this user.
    """
    FIXED_ZIP_PATH = Path(r"C:/Users/aakas/uni/cosc499/Project13_FreeCodeCamp.zip")

    if not FIXED_ZIP_PATH.exists():
        raise HTTPException(
            status_code=400,
            detail=f"Zip file not found on server: {FIXED_ZIP_PATH}",
        )

    task_manager = get_task_manager()

    task_id = task_manager.create_task(
        task_type=TaskType.NEW_PORTFOLIO,
        username=username,
        filename=FIXED_ZIP_PATH.name,
        file_path=FIXED_ZIP_PATH,
        analysis_type="non_llm",
    )

    return {
        "task_id": task_id,
        "status_url": f"/api/tasks/{task_id}",
    }
