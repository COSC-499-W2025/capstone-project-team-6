"""Main FastAPI application with modular API routers."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.analysis_database import init_db as init_analysis_db
from backend.database import init_db as init_user_db

# Import routers from modular API structure
from backend.api.analysis import router as analysis_router
from backend.api.auth import router as auth_router
from backend.api.health import router as health_router
from backend.api.portfolios import router as portfolios_router
from backend.api.projects import router as projects_router
from backend.api.resume import router as resume_router
from backend.api.tasks import router as tasks_router

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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
