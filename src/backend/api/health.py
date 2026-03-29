"""Health check and root endpoints."""

from datetime import datetime

from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/", operation_id="root")
async def root():
    """Root endpoint returning API information."""
    return {
        "name": "MDA Portfolio API",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/api/health",
    }


@router.get("/api/health", operation_id="health_check")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
    }
