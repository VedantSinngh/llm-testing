"""Integration tests for PromptLab FastAPI REST endpoints.

This module tests all REST API routes using httpx AsyncClient and ASGITransport:
- Health and models catalog endpoints.
- Test suites CRUD lifecycle.
- Evaluation runs execution, listing, and comparison.
- Safety injection auditing, text scanning, and reports.
- Request-ID middleware propagation and structured error handlers.
"""

from collections.abc import AsyncGenerator
from typing import Any

from httpx import ASGITransport, AsyncClient
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from promptlab.api.dependencies import get_db
from promptlab.api.main import create_app
from promptlab.config import Settings, get_settings


@pytest.fixture
async def api_client(
    async_db_session: AsyncSession,
    test_settings: Settings,
) -> AsyncGenerator[AsyncClient, None]:
    """Provide an AsyncClient configured with an isolated in-memory database."""
    app = create_app()

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield async_db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_settings] = lambda: test_settings

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_health_check(api_client: AsyncClient) -> None:
    """Verify GET /health returns 200 with operational metadata."""
    response = await api_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["demo_mode"] is True
    assert data["active_provider"] == "mock"
    assert "timestamp" in data
    assert "x-request-id" in response.headers


@pytest.mark.asyncio
async def test_models_catalog(api_client: AsyncClient) -> None:
    """Verify GET /models returns supported model IDs from mock provider."""
    response = await api_client.get("/api/v1/models")
    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "mock"
    assert isinstance(data["models"], list)
    assert "mock-llama-3.3-70b" in data["models"]


@pytest.mark.asyncio
async def test_suites_crud_lifecycle(api_client: AsyncClient) -> None:
    """Verify creating, reading, listing, and deleting test suites."""
    suite_payload: dict[str, Any] = {
        "name": "api_integration_suite",
        "description": "Suite testing API endpoints",
        "system_prompt": "You are a helpful assistant.",
        "technique": "zero_shot",
        "technique_config": {},
        "cases": [
            {
                "id": "c1",
                "input": "Capital of France?",
                "expected": "Paris",
                "scorer": "exact_match",
                "scorer_config": {"case_sensitive": False},
                "tags": ["geo"],
            }
        ],
    }

    # 1. Create suite
    create_resp = await api_client.post("/api/v1/suites", json=suite_payload)
    assert create_resp.status_code == 201
    suite_data = create_resp.json()
    suite_id = suite_data["id"]
    assert suite_data["suite"]["name"] == "api_integration_suite"

    # 2. Get suite
    get_resp = await api_client.get(f"/api/v1/suites/{suite_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == suite_id

    # 3. List suites
    list_resp = await api_client.get("/api/v1/suites?offset=0&limit=10")
    assert list_resp.status_code == 200
    list_data = list_resp.json()
    assert list_data["total"] >= 1
    assert any(s["id"] == suite_id for s in list_data["items"])

    # 4. Delete suite
    del_resp = await api_client.delete(f"/api/v1/suites/{suite_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["deleted"] is True

    # 5. Verify deleted suite returns 404
    missing_resp = await api_client.get(f"/api/v1/suites/{suite_id}")
    assert missing_resp.status_code == 404
    err_data = missing_resp.json()
    assert err_data["error_code"] == "RESOURCE_NOT_FOUND"


@pytest.mark.asyncio
async def test_runs_execution_and_comparison(api_client: AsyncClient) -> None:
    """Verify executing evaluation runs, fetching results, and comparing runs."""
    inline_suite: dict[str, Any] = {
        "name": "comparison_test_suite",
        "cases": [
            {
                "id": "tc-1",
                "input": "What is 10 + 10?",
                "expected": "20",
                "scorer": "exact_match",
            }
        ],
    }

    # Run 1: mock-llama-3.3-70b
    run1_payload = {
        "suite": inline_suite,
        "model": "mock-llama-3.3-70b",
        "params": {"temperature": 0.1, "max_tokens": 128},
    }
    run1_resp = await api_client.post("/api/v1/runs", json=run1_payload)
    assert run1_resp.status_code == 201
    run1_data = run1_resp.json()
    run1_id = run1_data["run_id"]
    assert run1_data["model"] == "mock-llama-3.3-70b"

    # Run 2: mock-qwen-2.5-72b
    run2_payload = {
        "suite": inline_suite,
        "model": "mock-qwen-2.5-72b",
        "params": {"temperature": 0.5, "max_tokens": 128},
    }
    run2_resp = await api_client.post("/api/v1/runs", json=run2_payload)
    assert run2_resp.status_code == 201
    run2_id = run2_resp.json()["run_id"]

    # Get single run
    get_run_resp = await api_client.get(f"/api/v1/runs/{run1_id}")
    assert get_run_resp.status_code == 200
    assert get_run_resp.json()["run_id"] == run1_id

    # List runs
    list_runs_resp = await api_client.get("/api/v1/runs")
    assert list_runs_resp.status_code == 200
    assert list_runs_resp.json()["total"] >= 2

    # Side-by-side comparison
    compare_resp = await api_client.post(
        "/api/v1/runs/compare", json={"run_ids": [run1_id, run2_id]}
    )
    assert compare_resp.status_code == 200
    comp_data = compare_resp.json()
    assert comp_data["run_count"] == 2
    assert "best_performing_model" in comp_data
    assert "case_matrix" in comp_data


@pytest.mark.asyncio
async def test_safety_injection_and_scan_endpoints(api_client: AsyncClient) -> None:
    """Verify injection testing, text scanning, and report retrieval."""
    # 1. Injection test
    inj_payload = {
        "model": "mock-llama-3.3-70b",
        "canary": "CANARY_SECRET_12345",
    }
    inj_resp = await api_client.post("/api/v1/safety/injection-test", json=inj_payload)
    assert inj_resp.status_code == 200
    inj_data = inj_resp.json()
    assert "report_id" in inj_data
    assert inj_data["tested_count"] > 0
    report_id = inj_data["report_id"]

    # 2. Get safety report
    rep_resp = await api_client.get(f"/api/v1/safety/reports/{report_id}")
    assert rep_resp.status_code == 200
    assert rep_resp.json()["id"] == report_id

    # 3. List safety reports
    list_rep_resp = await api_client.get("/api/v1/safety/reports")
    assert list_rep_resp.status_code == 200
    assert list_rep_resp.json()["total"] >= 1

    # 4. Text PII Scan
    scan_payload = {
        "text": "Contact user at test.user@example.com with key gsk_1234567890abcdef1234."
    }
    scan_resp = await api_client.post("/api/v1/safety/scan", json=scan_payload)
    assert scan_resp.status_code == 200
    scan_data = scan_resp.json()
    assert scan_data["risk_level"] in {"medium", "high"}
    assert len(scan_data["pii_findings"]) >= 2
    assert "[REDACTED]" in scan_data["redacted_text"]


@pytest.mark.asyncio
async def test_request_id_header_and_validation_errors(api_client: AsyncClient) -> None:
    """Verify custom X-Request-ID propagation and 422 validation error structure."""
    custom_req_id = "custom-trace-uuid-9999"

    # Test custom request ID propagation on valid endpoint
    resp = await api_client.get(
        "/health",
        headers={"X-Request-ID": custom_req_id},
    )
    assert resp.status_code == 200
    assert resp.headers.get("x-request-id") == custom_req_id

    # Test 422 error response structure on invalid POST body
    invalid_resp = await api_client.post(
        "/api/v1/suites",
        json={"name": ""},  # Missing cases and invalid name
        headers={"X-Request-ID": custom_req_id},
    )
    assert invalid_resp.status_code == 422
    err_data = invalid_resp.json()
    assert err_data["error_code"] == "VALIDATION_ERROR"
    assert err_data["request_id"] == custom_req_id
    assert "errors" in err_data["details"]
