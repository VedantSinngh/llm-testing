"""Unit tests for ZeroShot prompt technique."""

from promptlab.core.techniques.zero_shot import ZeroShot


def test_zero_shot_application() -> None:
    """Verify ZeroShot technique leaves user input unchanged and adds no system prompt."""
    technique = ZeroShot()
    assert technique.name == "zero_shot"

    sys_add, user_prompt = technique.apply("Translate hello to French", {})
    assert sys_add is None
    assert user_prompt == "Translate hello to French"
