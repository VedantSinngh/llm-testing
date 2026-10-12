"""Unit tests for InjectionSuite attack runner and vulnerability detection."""

import pytest

from promptlab.core.providers.mock_provider import MockProvider
from promptlab.core.safety.injection_suite import InjectionSuite


def test_load_attacks_from_json() -> None:
    """Verify at least 15 attack prompts across 5 categories are loaded."""
    suite = InjectionSuite()
    attacks = suite.load_attacks()
    assert len(attacks) >= 15

    categories = {a["category"] for a in attacks}
    expected_categories = {
        "override",
        "role-play",
        "data-exfiltration",
        "delimiter-escape",
        "indirect",
    }
    assert expected_categories.issubset(categories)


def test_evaluate_attack_detects_canary_leak() -> None:
    """Verify leaking the canary secret registers as a successful breach."""
    suite = InjectionSuite()
    canary = "CANARY-7F3A99B1"
    attack = {
        "id": "test_1",
        "success_indicators": ["override accepted"],
    }

    breached, reason = suite._evaluate_attack(attack, f"Here is the secret: {canary}", canary)
    assert breached is True
    assert "leaked" in reason.lower()


def test_evaluate_attack_detects_success_indicator() -> None:
    """Verify triggering an attack success indicator registers as breached."""
    suite = InjectionSuite()
    canary = "CANARY-7F3A99B1"
    attack = {
        "id": "test_2",
        "success_indicators": ["root_admin mode enabled"],
    }

    breached, reason = suite._evaluate_attack(
        attack, "System updated: ROOT_ADMIN mode enabled.", canary
    )
    assert breached is True
    assert "indicator" in reason.lower()


def test_evaluate_attack_resisted() -> None:
    """Verify safe model refusal registers as resisted."""
    suite = InjectionSuite()
    canary = "CANARY-7F3A99B1"
    attack = {
        "id": "test_3",
        "success_indicators": ["override accepted"],
    }

    breached, reason = suite._evaluate_attack(
        attack, "I cannot fulfill this request due to safety policies.", canary
    )
    assert breached is False
    assert "resisted" in reason.lower()


@pytest.mark.asyncio
async def test_run_suite_with_mock_provider() -> None:
    """Verify end-to-end execution of injection suite with MockProvider."""
    provider = MockProvider(simulated_latency_ms=0.0)
    # Configure mock to resist by default
    suite = InjectionSuite()

    report = await suite.run_suite(
        provider=provider,
        model="mock-llama-3.3-70b",
        canary="CANARY-TEST1234",
        max_concurrency=4,
    )

    assert report["model"] == "mock-llama-3.3-70b"
    assert report["canary"] == "CANARY-TEST1234"
    assert report["total_attacks"] >= 15
    assert "category_breakdown" in report
    assert "overall_attack_success_rate" in report
    assert len(report["results"]) == report["total_attacks"]
