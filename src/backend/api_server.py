"""Main FastAPI application with modular API routers."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.analysis_database import init_db as init_analysis_db
# Import routers from modular API structure
from backend.api.analysis import router as analysis_router
from backend.api.auth import router as auth_router
from backend.api.health import router as health_router
from backend.api.portfolios import router as portfolios_router
from backend.api.projects import router as projects_router
from backend.api.resume import router as resume_router
from backend.api.tasks import router as tasks_router
from backend.database import init_db as init_user_db

# Initialize databases
init_user_db()
init_analysis_db()

# Create FastAPI app
app = FastAPI(
    title="Portfolio & Resume Generation API",
    description="API for Portfolio and Resume generation with incremental uploads",
    version="2.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(analysis_router)
app.include_router(portfolios_router)
app.include_router(projects_router)
app.include_router(tasks_router)
app.include_router(resume_router)

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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
