"""PromptLab API package exposing FastAPI application factory.

This package encapsulates REST endpoints, schemas, dependency injection, and middleware.
"""

from promptlab.api.main import create_app

__all__ = ["create_app"]
