"""API routers package."""
from .auth import router as auth_router
from .health import router as health_router
from .portfolios import router as portfolios_router
from .projects import router as projects_router
from .resume import router as resume_router
from .tasks import router as tasks_router

__all__ = [
    "auth_router",
    "health_router",
    "portfolios_router",
    "projects_router",
    "resume_router",
    "tasks_router",
]
