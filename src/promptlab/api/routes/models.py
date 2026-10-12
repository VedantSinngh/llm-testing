"""Models route exposing available LLM catalogs for active providers.

This module queries registered provider engines to return supported model identifiers
for prompt evaluations and playground experimentation.
"""

from fastapi import APIRouter, Depends, Query

from promptlab.api.schemas import ModelsResponse
from promptlab.config import Settings, get_settings
from promptlab.core.providers.factory import ProviderFactory

router = APIRouter(tags=["Models"])


@router.get("/models", response_model=ModelsResponse)
async def list_models(
    provider: str | None = Query(default=None, description="Optional provider identifier override."),
    settings: Settings = Depends(get_settings),
) -> ModelsResponse:
    """Return catalog of model IDs supported by the active or requested provider."""
    target_provider = provider or ("mock" if settings.demo_mode else "groq")
    provider_instance = ProviderFactory.create(target_provider)
    models = await provider_instance.list_models()

    return ModelsResponse(
        provider=target_provider,
        models=models,
    )
