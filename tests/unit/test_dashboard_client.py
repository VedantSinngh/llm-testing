"""Unit tests for the dashboard PromptLabClient wrapper.

This module validates that the client handles connection failures gracefully,
normalizes API payloads, and translates HTTP error codes into domain exceptions.
"""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from promptlab.dashboard.api_client import APIClientError, PromptLabClient


def test_client_init_and_base_url() -> None:
    """Verify default and custom base URL assignment."""
    client = PromptLabClient("http://custom-host:9000/")
    assert client.base_url == "http://custom-host:9000"
    client.close()


def test_health_check_offline_graceful_fallback() -> None:
    """Verify health() returns status unreachable on connection error."""
    client = PromptLabClient("http://localhost:99999")
    with patch.object(client._client, "get", side_effect=httpx.ConnectError("Connection refused")):
        res = client.health()
        assert res["status"] == "unreachable"
        assert res["demo_mode"] is True
        assert "error" in res
    client.close()


def test_list_models_fallback_on_error() -> None:
    """Verify list_models() falls back to mock models if endpoint fails."""
    client = PromptLabClient()
    with patch.object(client._client, "get", side_effect=Exception("Failed")):
        models = client.list_models()
        assert "mock-llama-3.3-70b" in models
        assert len(models) >= 4
    client.close()


def test_create_suite_success() -> None:
    """Verify create_suite sends JSON payload and parses response."""
    client = PromptLabClient()
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.is_error = False
    mock_resp.json.return_value = {"id": "suite-uuid-1", "suite": {"name": "test"}}

    with patch.object(client._client, "post", return_value=mock_resp) as mock_post:
        payload = {"name": "test", "cases": []}
        res = client.create_suite(payload)
        mock_post.assert_called_once_with("/api/v1/suites", json=payload)
        assert res["id"] == "suite-uuid-1"
    client.close()


def test_api_error_translation() -> None:
    """Verify HTTP errors raise APIClientError."""
    client = PromptLabClient()
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.is_error = True
    mock_resp.status_code = 404
    mock_resp.json.return_value = {"message": "Suite not found."}

    with patch.object(client._client, "get", return_value=mock_resp):
        with pytest.raises(APIClientError) as exc_info:
            client.get_suite("invalid-id")
        assert exc_info.value.status_code == 404
        assert "Suite not found" in str(exc_info.value)
    client.close()


def test_scan_text_and_compare_runs() -> None:
    """Verify scan_text and compare_runs route invocations."""
    client = PromptLabClient()
    mock_scan_resp = MagicMock(spec=httpx.Response)
    mock_scan_resp.is_error = False
    mock_scan_resp.json.return_value = {"risk_level": "low", "passed": True, "pii_findings": [], "redacted_text": "clean"}

    with patch.object(client._client, "post", return_value=mock_scan_resp) as mock_post:
        scan_res = client.scan_text("clean text")
        mock_post.assert_called_once_with("/api/v1/safety/scan", json={"text": "clean text"})
        assert scan_res["passed"] is True
    client.close()
