#!/usr/bin/env python3
"""Offline smoke checks for Haystack tool schemas, Toolset, ToolInvoker, and state mappings."""

from __future__ import annotations

import json
from typing import Annotated, Literal

from haystack.components.agents import State
from haystack.components.tools import ToolInvoker
from haystack.dataclasses import ChatMessage, ToolCall
from haystack.tools import Tool, Toolset, create_tool_from_function


def convert_temperature(
    value: Annotated[float, "Temperature value"],
    unit: Annotated[Literal["celsius", "fahrenheit"], "Input unit"],
) -> dict[str, float | str]:
    """Convert a temperature to the other unit."""
    if unit == "celsius":
        return {"unit": "fahrenheit", "value": round(value * 9 / 5 + 32, 2)}
    return {"unit": "celsius", "value": round((value - 32) * 5 / 9, 2)}


def remember_fact(
    fact: Annotated[str, "A short fact to store"],
    state: State | None = None,
) -> dict[str, list[str]]:
    """Store a fact and return the accumulated fact list."""
    prior_facts = [] if state is None else list(state.get("facts", []))
    return {"facts": prior_facts + [fact]}


def require_context(
    question: Annotated[str, "Question to answer"],
    facts: list[str],
) -> str:
    """Answer a question using facts injected from state."""
    return f"Question: {question}\nFacts: {'; '.join(facts)}"


def main() -> None:
    convert_tool = create_tool_from_function(
        convert_temperature,
        outputs_to_string={"source": "value", "handler": str},
    )
    remember_tool = create_tool_from_function(
        remember_fact,
        outputs_to_state={"facts": {"source": "facts"}},
    )
    context_tool = create_tool_from_function(
        require_context,
        inputs_from_state={"facts": "facts"},
    )

    assert isinstance(convert_tool, Tool)
    assert convert_tool.name == "convert_temperature"
    assert convert_tool.tool_spec["parameters"]["properties"]["unit"]["enum"] == ["celsius", "fahrenheit"]
    assert "facts" not in context_tool.tool_spec["parameters"].get("properties", {})

    toolset = Toolset([convert_tool, remember_tool, context_tool])
    assert len(toolset) == 3
    assert "convert_temperature" in toolset

    invoker = ToolInvoker(tools=toolset, raise_on_failure=True, convert_result_to_json_string=True)
    message = ChatMessage.from_assistant(
        tool_calls=[ToolCall(tool_name="convert_temperature", arguments={"value": 100.0, "unit": "celsius"})]
    )
    result = invoker.run(messages=[message])
    tool_messages = result["tool_messages"]
    assert len(tool_messages) == 1

    payload = json.loads(tool_messages[0].tool_call_result.result)
    assert payload == 212.0

    print("OK: Haystack tool schema, Toolset, ToolInvoker, and state mappings validated.")


if __name__ == "__main__":
    main()
