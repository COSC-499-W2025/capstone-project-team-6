"""Health check and root endpoints."""
from datetime import datetime

from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "MDA Portfolio API",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/api/health",
    }
