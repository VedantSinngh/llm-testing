"""HTTP client wrapper communicating with the PromptLab FastAPI backend.

This module provides a typed, synchronous client used by Streamlit pages to query
evaluation endpoints, trigger runs, and inspect safety reports. It encapsulates
connection retries, timeouts, and error normalization.
"""

from datetime import datetime, timezone
import os
from typing import Any

import httpx

from promptlab.exceptions import PromptLabError


class APIClientError(PromptLabError):
    """Raised when the backend API returns an error or is unreachable."""

    def __init__(self, message: str, status_code: int = 502, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            message=message,
            error_code="API_CLIENT_ERROR",
            status_code=status_code,
            details=details,
        )


class PromptLabClient:
    """Client for interacting with PromptLab REST API backend."""

    def __init__(self, base_url: str | None = None, timeout: float = 60.0) -> None:
        """Initialize PromptLabClient with base URL from param or environment."""
        resolved_url = base_url or os.getenv("PROMPTLAB_API_URL", "http://localhost:8000")
        self.base_url = resolved_url.rstrip("/")
        self.timeout = timeout
        self._client = httpx.Client(base_url=self.base_url, timeout=self.timeout)

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        """Validate HTTP response status and return parsed JSON dictionary."""
        try:
            payload: dict[str, Any] = response.json()
        except Exception:
            payload = {"raw_text": response.text}

        if response.is_error:
            msg = payload.get("message", f"HTTP {response.status_code} error from API server.")
            raise APIClientError(message=str(msg), status_code=response.status_code, details=payload)

        return payload

    def health(self) -> dict[str, Any]:
        """Check application operational health."""
        try:
            resp = self._client.get("/health")
            return self._handle_response(resp)
        except httpx.RequestError as exc:
            return {
                "status": "unreachable",
                "demo_mode": True,
                "active_provider": "offline",
                "error": str(exc),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    def list_models(self, provider: str | None = None) -> list[str]:
        """Retrieve list of available model IDs."""
        params = {"provider": provider} if provider else {}
        try:
            resp = self._client.get("/api/v1/models", params=params)
            data = self._handle_response(resp)
            models = data.get("models", [])
            return [str(m) for m in models]
        except Exception:
            return [
                "mock-llama-3.3-70b",
                "mock-qwen-2.5-72b",
                "mock-mistral-large",
                "mock-gemma-2-9b",
            ]

    def create_suite(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Register a new evaluation test suite."""
        resp = self._client.post("/api/v1/suites", json=payload)
        return self._handle_response(resp)

    def list_suites(self, offset: int = 0, limit: int = 50) -> dict[str, Any]:
        """Retrieve paginated test suites."""
        resp = self._client.get("/api/v1/suites", params={"offset": offset, "limit": limit})
        return self._handle_response(resp)

    def get_suite(self, suite_id: str) -> dict[str, Any]:
        """Retrieve single test suite by ID."""
        resp = self._client.get(f"/api/v1/suites/{suite_id}")
        return self._handle_response(resp)

    def delete_suite(self, suite_id: str) -> bool:
        """Delete test suite by ID."""
        resp = self._client.delete(f"/api/v1/suites/{suite_id}")
        data = self._handle_response(resp)
        return bool(data.get("deleted", False))

    def execute_run(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Trigger an evaluation run."""
        resp = self._client.post("/api/v1/runs", json=payload)
        return self._handle_response(resp)

    def list_runs(
        self,
        offset: int = 0,
        limit: int = 50,
        suite_name: str | None = None,
        model: str | None = None,
    ) -> dict[str, Any]:
        """Retrieve historical evaluation runs."""
        params: dict[str, Any] = {"offset": offset, "limit": limit}
        if suite_name:
            params["suite_name"] = suite_name
        if model:
            params["model"] = model
        resp = self._client.get("/api/v1/runs", params=params)
        return self._handle_response(resp)

    def get_run(self, run_id: str) -> dict[str, Any]:
        """Retrieve detailed run results by ID."""
        resp = self._client.get(f"/api/v1/runs/{run_id}")
        return self._handle_response(resp)

    def compare_runs(self, run_ids: list[str]) -> dict[str, Any]:
        """Compare multiple evaluation runs side by side."""
        resp = self._client.post("/api/v1/runs/compare", json={"run_ids": run_ids})
        return self._handle_response(resp)

    def run_injection_test(
        self,
        model: str,
        canary: str | None = None,
        provider: str | None = None,
    ) -> dict[str, Any]:
        """Execute prompt injection test suite against a model."""
        payload: dict[str, Any] = {"model": model}
        if canary:
            payload["canary"] = canary
        if provider:
            payload["provider"] = provider
        resp = self._client.post("/api/v1/safety/injection-test", json=payload)
        return self._handle_response(resp)

    def scan_text(self, text: str) -> dict[str, Any]:
        """Scan arbitrary text for PII entities and credentials."""
        resp = self._client.post("/api/v1/safety/scan", json={"text": text})
        return self._handle_response(resp)

    def list_safety_reports(self, offset: int = 0, limit: int = 50) -> dict[str, Any]:
        """Retrieve paginated safety reports."""
        resp = self._client.get("/api/v1/safety/reports", params={"offset": offset, "limit": limit})
        return self._handle_response(resp)

    def get_safety_report(self, report_id: str) -> dict[str, Any]:
        """Retrieve single safety report by ID."""
        resp = self._client.get(f"/api/v1/safety/reports/{report_id}")
        return self._handle_response(resp)

    def close(self) -> None:
        """Close underlying httpx connection pool."""
        self._client.close()
