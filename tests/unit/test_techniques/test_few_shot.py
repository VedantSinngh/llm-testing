"""Unit tests for FewShot prompt technique."""

from promptlab.core.techniques.few_shot import FewShot


def test_few_shot_with_examples() -> None:
    """Verify FewShot formats demonstration examples into the user prompt."""
    technique = FewShot()
    examples = [
        {"input": "happy", "output": "positive"},
        {"input": "sad", "output": "negative"},
    ]
    sys_add, user_prompt = technique.apply("neutral", {"examples": examples})

    assert sys_add is not None
    assert "demonstration examples" in sys_add
    assert "Example 1:" in user_prompt
    assert "Input: happy\nOutput: positive" in user_prompt
    assert "Example 2:" in user_prompt
    assert "Input: neutral\nOutput:" in user_prompt


def test_few_shot_empty_examples() -> None:
    """Verify FewShot handles missing or empty examples gracefully."""
    technique = FewShot()
    sys_add, user_prompt = technique.apply("neutral", {})

    assert sys_add is not None
    assert user_prompt == "neutral"
