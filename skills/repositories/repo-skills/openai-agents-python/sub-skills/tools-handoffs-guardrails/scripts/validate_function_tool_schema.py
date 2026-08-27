#!/usr/bin/env python3
"""Inspect openai-agents function tool schema behavior without API calls."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from typing import Any


TOOL_NAMES = ["lookup_customer", "loose_optional_note", "approval_gated_action"]


def build_tools() -> tuple[list[Any], type[Exception], type[Any]]:
    from typing import Annotated

    from pydantic import BaseModel, Field

    from agents import (
        ModelBehaviorError,
        RunContextWrapper,
        ToolGuardrailFunctionOutput,
        function_tool,
        tool_input_guardrail,
        tool_output_guardrail,
    )
    from agents.tool_context import ToolContext

    globals()["Annotated"] = Annotated
    globals()["Field"] = Field
    globals()["RunContextWrapper"] = RunContextWrapper
    globals()["ToolGuardrailFunctionOutput"] = ToolGuardrailFunctionOutput

    class CustomerLookup(BaseModel):
        """Nested object used to demonstrate Pydantic model schema generation."""

        customer_id: str = Field(description="Stable customer identifier.", min_length=3)
        include_orders: bool = Field(default=False, description="Whether to include open orders.")

    globals()["CustomerLookup"] = CustomerLookup

    @tool_input_guardrail
    def reject_secret_arguments(data: Any) -> ToolGuardrailFunctionOutput:
        """Reject sample inputs containing obvious secret markers."""

        raw_arguments = data.context.tool_arguments or ""
        if "sk-" in raw_arguments or "password=" in raw_arguments:
            return ToolGuardrailFunctionOutput.reject_content(
                "Remove secrets before calling this tool.",
                output_info={"guardrail": "reject_secret_arguments"},
            )
        return ToolGuardrailFunctionOutput.allow(
            output_info={"guardrail": "reject_secret_arguments"}
        )

    @tool_output_guardrail
    def redact_secret_outputs(data: Any) -> ToolGuardrailFunctionOutput:
        """Reject sample outputs containing obvious secret markers."""

        output_text = str(data.output or "")
        if "sk-" in output_text or "password=" in output_text:
            return ToolGuardrailFunctionOutput.reject_content(
                "The tool output contained sensitive data and was withheld.",
                output_info={"guardrail": "redact_secret_outputs"},
            )
        return ToolGuardrailFunctionOutput.allow(output_info={"guardrail": "redact_secret_outputs"})

    @function_tool(
        name_override="lookup_customer",
        strict_mode=True,
        tool_input_guardrails=[reject_secret_arguments],
        tool_output_guardrails=[redact_secret_outputs],
    )
    def lookup_customer_profile(
        ctx: RunContextWrapper[dict[str, Any]],
        lookup: CustomerLookup,
        priority: Annotated[int, Field(ge=1, le=5, description="Priority from 1 to 5.")] = 3,
    ) -> str:
        """Look up a customer profile for a support workflow.

        Args:
            lookup: Customer lookup options.
            priority: Priority from 1 to 5.
        """

        _ = ctx
        return json.dumps(
            {
                "customer_id": lookup.customer_id,
                "include_orders": lookup.include_orders,
                "priority": priority,
            }
        )

    @function_tool(strict_mode=False, use_docstring_info=False)
    def loose_optional_note(note: str | None = None) -> str:
        return note or "no note"

    @function_tool(needs_approval=True)
    async def approval_gated_action(action_id: str, reason: str) -> str:
        """Demonstrate an approval-gated async tool schema."""

        return f"queued:{action_id}:{reason}"

    return (
        [lookup_customer_profile, loose_optional_note, approval_gated_action],
        ModelBehaviorError,
        ToolContext,
    )


def print_tool_summary(tool: Any) -> None:
    print(f"## {tool.name}")
    print(f"description: {tool.description!r}")
    print(f"strict_json_schema: {tool.strict_json_schema}")
    print(f"needs_approval: {bool(tool.needs_approval)}")
    print(f"input_guardrails: {len(tool.tool_input_guardrails or [])}")
    print(f"output_guardrails: {len(tool.tool_output_guardrails or [])}")
    print("schema:")
    print(json.dumps(tool.params_json_schema, indent=2, sort_keys=True))
    print()


async def invoke_tool(
    tool: Any,
    tool_context_type: type[Any],
    payload: dict[str, Any],
    context: Any = None,
) -> Any:
    raw_payload = json.dumps(payload)
    tool_context = tool_context_type(
        context=context,
        tool_name=tool.name,
        tool_call_id="schema-check",
        tool_arguments=raw_payload,
    )
    return await tool.on_invoke_tool(tool_context, raw_payload)


async def run_validation_examples(
    lookup_customer_profile: Any,
    model_behavior_error_type: type[Exception],
    tool_context_type: type[Any],
) -> int:
    valid_payload = {
        "lookup": {"customer_id": "cus_123", "include_orders": True},
        "priority": 4,
    }
    print("# Invocation checks")
    valid_result = await invoke_tool(
        lookup_customer_profile,
        tool_context_type,
        valid_payload,
        context={},
    )
    print("valid lookup_customer result:", valid_result)

    invalid_payload = {
        "lookup": {"customer_id": "x", "include_orders": True},
        "priority": 99,
    }
    try:
        await invoke_tool(lookup_customer_profile, tool_context_type, invalid_payload, context={})
    except model_behavior_error_type as exc:
        print("caught expected ModelBehaviorError for invalid payload:")
        print(str(exc).splitlines()[0])
    else:
        print("expected invalid payload to raise ModelBehaviorError", file=sys.stderr)
        return 1

    try:
        await invoke_tool(
            lookup_customer_profile,
            tool_context_type,
            {"lookup": {"customer_id": "sk-secret"}},
            context={},
        )
    except Exception as exc:  # The tool invoker should still parse; guardrails run in Runner.
        print("direct invocation exception:", type(exc).__name__, str(exc).splitlines()[0])
    print("note: direct FunctionTool.on_invoke_tool checks schema only; Runner executes guardrails.")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print and sanity-check sample openai-agents function tool schemas without API calls.",
    )
    parser.add_argument(
        "--tool",
        choices=TOOL_NAMES + ["all"],
        default="all",
        help="Tool schema to print. Defaults to all sample tools.",
    )
    parser.add_argument(
        "--skip-invoke",
        action="store_true",
        help="Only print schemas; skip local schema invocation checks.",
    )
    return parser.parse_args()


async def main() -> int:
    args = parse_args()
    try:
        tools, model_behavior_error_type, tool_context_type = build_tools()
    except ModuleNotFoundError as exc:
        missing_name = exc.name or "required dependency"
        print(
            f"Cannot import {missing_name!r}. Install openai-agents in this Python environment "
            "or run this helper from a prepared repository development environment.",
            file=sys.stderr,
        )
        return 2

    selected_tools = tools if args.tool == "all" else [tool for tool in tools if tool.name == args.tool]

    print("# Function tool schema facts")
    for tool in selected_tools:
        print_tool_summary(tool)

    if args.skip_invoke:
        return 0
    lookup_customer_profile = next(tool for tool in tools if tool.name == "lookup_customer")
    return await run_validation_examples(
        lookup_customer_profile,
        model_behavior_error_type,
        tool_context_type,
    )


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
