"""FastAPI application factory, middleware, and global error handling.

This module initializes the PromptLab REST API:
- Application factory pattern for isolated testing and configuration.
- Request-ID tracking middleware correlating logs across async tasks.
- CORS policy configuration.
- Global exception translation from domain `PromptLabError` to JSON responses.
- Database auto-migration lifespan handler.
"""

from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
import logging
from typing import Any
import uuid

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from promptlab.api.routes import api_router
from promptlab.db.base import init_db
from promptlab.exceptions import PromptLabError
from promptlab.logging_config import get_request_id, set_request_id

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown lifecycle events."""
    logger.info("Initializing PromptLab database schema...")
    await init_db()
    yield
    logger.info("PromptLab API shutdown complete.")


# Design Pattern: Factory pattern creating configured FastAPI application instance.
def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    app = FastAPI(
        title="PromptLab API",
        version="0.1.0",
        description="Product-grade LLM Evaluation & Guardrails Playground REST API",
        lifespan=lifespan,
    )

    # Configure Cross-Origin Resource Sharing (CORS)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Middleware: Request-ID tracking and async context propagation
    @app.middleware("http")
    async def request_id_middleware(
        request: Request,
        call_next: Callable[[Request], Any],
    ) -> Response:
        header_req_id = request.headers.get("X-Request-ID")
        active_req_id = header_req_id if header_req_id else str(uuid.uuid4())
        set_request_id(active_req_id)

        try:
            response: Response = await call_next(request)
        finally:
            pass

        response.headers["X-Request-ID"] = active_req_id
        return response

    # Exception Handler: Domain exceptions mapped to standard structured responses
    @app.exception_handler(PromptLabError)
    async def promptlab_error_handler(
        request: Request,
        exc: PromptLabError,
    ) -> JSONResponse:
        active_id = get_request_id()
        return JSONResponse(
            status_code=exc.status_code,
            headers={"X-Request-ID": active_id},
            content={
                "error_code": exc.error_code,
                "message": exc.message,
                "request_id": active_id,
                "details": exc.details,
            },
        )

    # Exception Handler: Pydantic request validation errors
    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        active_id = get_request_id()
        return JSONResponse(
            status_code=422,
            headers={"X-Request-ID": active_id},
            content={
                "error_code": "VALIDATION_ERROR",
                "message": "Input validation failed.",
                "request_id": active_id,
                "details": {"errors": exc.errors()},
            },
        )

    # Exception Handler: Uncaught fatal server errors
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        logger.exception("Unhandled server exception: %s", str(exc))
        active_id = get_request_id()
        return JSONResponse(
            status_code=500,
            headers={"X-Request-ID": active_id},
            content={
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected internal server error occurred.",
                "request_id": active_id,
                "details": {},
            },
        )

    # Mount routes at /api/v1 as well as root for ergonomic access
    app.include_router(api_router, prefix="/api/v1")
    app.include_router(api_router)

    return app


app = create_app()
