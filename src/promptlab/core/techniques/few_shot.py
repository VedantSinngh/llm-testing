"""Few-shot in-context learning prompt technique.

This module prepends demonstration input-output pairs to the user prompt,
leveraging in-context learning to guide model response style, format, and reasoning.
"""

from typing import Any

from promptlab.core.techniques.base import PromptTechnique


# Design Pattern: Strategy implementation for few-shot prompt formulation.
class FewShot(PromptTechnique):
    """Few-shot prompting injecting demonstration examples into the prompt."""

    name: str = "few_shot"

    def apply(
        self, case_input: str, config: dict[str, Any]
    ) -> tuple[str | None, str]:
        """Format demonstration examples and append the current case query.

        Args:
            case_input: Current test case input text.
            config: Configuration containing 'examples' list.

        Returns:
            Tuple of (system_prompt_addition, user_prompt_with_examples).
        """
        examples: list[dict[str, Any]] = config.get("examples", [])
        system_addition = (
            "You are provided with demonstration examples to illustrate "
            "the desired format and response pattern. Follow these patterns closely."
        )

        if not examples:
            return (system_addition, case_input)

        formatted_blocks: list[str] = []
        for idx, ex in enumerate(examples, start=1):
            ex_in = ex.get("input", "")
            ex_out = ex.get("output", "")
            formatted_blocks.append(f"Example {idx}:\nInput: {ex_in}\nOutput: {ex_out}")

        examples_text = "\n\n".join(formatted_blocks)
        user_prompt = f"{examples_text}\n\nInput: {case_input}\nOutput:"
        return (system_addition, user_prompt)
