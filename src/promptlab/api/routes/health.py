"""Health check route verifying application configuration and operational status.

This endpoint provides a lightweight liveness and readiness check suitable for
container orchestrators, load balancers, and playground UI diagnostics.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from promptlab.api.schemas import HealthResponse
from promptlab.config import Settings, get_settings

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def check_health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """Return application operational status, demo mode flag, and active provider."""
    provider_name = "mock" if settings.demo_mode else "groq"
    return HealthResponse(
        status="ok",
        demo_mode=settings.demo_mode,
        active_provider=provider_name,
        timestamp=datetime.now(timezone.utc),
    )
