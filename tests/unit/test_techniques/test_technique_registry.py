"""Unit tests for TechniqueRegistry and technique discovery."""

import pytest

from promptlab.core.techniques.base import PromptTechnique
from promptlab.core.techniques.chain_of_thought import ChainOfThought
from promptlab.core.techniques.few_shot import FewShot
from promptlab.core.techniques.registry import TechniqueRegistry
from promptlab.core.techniques.structured_output import StructuredOutput
from promptlab.core.techniques.zero_shot import ZeroShot
from promptlab.exceptions import TechniqueNotFoundError


def test_registry_get_built_in_techniques() -> None:
    """Verify built-in techniques are retrievable by name."""
    assert isinstance(TechniqueRegistry.get("zero_shot"), ZeroShot)
    assert isinstance(TechniqueRegistry.get("few_shot"), FewShot)
    assert isinstance(TechniqueRegistry.get("chain_of_thought"), ChainOfThought)
    assert isinstance(TechniqueRegistry.get("structured_output"), StructuredOutput)


def test_registry_case_insensitivity() -> None:
    """Verify lookup is case-insensitive."""
    assert isinstance(TechniqueRegistry.get("ZERO_SHOT"), ZeroShot)
    assert isinstance(TechniqueRegistry.get("Chain_Of_Thought"), ChainOfThought)


def test_registry_unregistered_technique_raises_error() -> None:
    """Verify TechniqueNotFoundError is raised for unknown technique name."""
    with pytest.raises(TechniqueNotFoundError) as exc_info:
        TechniqueRegistry.get("non_existent_strategy")
    assert exc_info.value.status_code == 404
    assert "non_existent_strategy" in str(exc_info.value)


def test_registry_decorator_custom_technique() -> None:
    """Verify custom technique can be added via @TechniqueRegistry.register."""

    @TechniqueRegistry.register("custom_scaffold")
    class CustomScaffold(PromptTechnique):
        name: str = "custom_scaffold"

        def apply(self, case_input: str, config: dict) -> tuple[str | None, str]:
            return ("Custom System", f"Custom: {case_input}")

    assert "custom_scaffold" in TechniqueRegistry.list_techniques()
    inst = TechniqueRegistry.get("custom_scaffold")
    assert isinstance(inst, CustomScaffold)
    sys_add, usr = inst.apply("test", {})
    assert sys_add == "Custom System"
    assert usr == "Custom: test"


def test_list_techniques() -> None:
    """Verify list_techniques returns all registered strategies."""
    techniques = TechniqueRegistry.list_techniques()
    assert "zero_shot" in techniques
    assert "few_shot" in techniques
    assert "chain_of_thought" in techniques
    assert "structured_output" in techniques
