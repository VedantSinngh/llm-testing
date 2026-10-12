"""Unit tests for ChainOfThought technique and answer extraction parser."""

from promptlab.core.techniques.chain_of_thought import ChainOfThought


def test_chain_of_thought_prompt_application() -> None:
    """Verify CoT technique formats reasoning and answer delimiter instructions."""
    technique = ChainOfThought()
    sys_add, user_prompt = technique.apply("How many wheels on 3 cars?", {})

    assert sys_add is not None
    assert "step-by-step" in sys_add
    assert "Answer: <your final answer>" in sys_add
    assert "Answer: <final answer>" in user_prompt
    assert "How many wheels on 3 cars?" in user_prompt


def test_chain_of_thought_answer_extraction() -> None:
    """Verify extract_answer correctly isolates final token after delimiter."""
    sample_cot = (
        "Let's think step by step:\n1 car has 4 wheels.\n3 cars have 3 * 4 = 12 wheels.\nAnswer: 12"
    )
    answer = ChainOfThought.extract_answer(sample_cot)
    assert answer == "12"


def test_chain_of_thought_answer_extraction_fallback() -> None:
    """Verify fallback when 'Answer:' token is omitted by model."""
    sample_text = "The calculated result is forty-two."
    answer = ChainOfThought.extract_answer(sample_text)
    assert answer == "The calculated result is forty-two."
