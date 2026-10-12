"""API routes module aggregating all sub-routers.

This module provides the central APIRouter containing health, models, suites,
runs, and safety sub-routers.
"""

from fastapi import APIRouter

from promptlab.api.routes.health import router as health_router
from promptlab.api.routes.models import router as models_router
from promptlab.api.routes.runs import router as runs_router
from promptlab.api.routes.safety import router as safety_router
from promptlab.api.routes.suites import router as suites_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(models_router)
api_router.include_router(suites_router)
api_router.include_router(runs_router)
api_router.include_router(safety_router)

__all__ = [
    "api_router",
    "health_router",
    "models_router",
    "suites_router",
    "runs_router",
    "safety_router",
]
