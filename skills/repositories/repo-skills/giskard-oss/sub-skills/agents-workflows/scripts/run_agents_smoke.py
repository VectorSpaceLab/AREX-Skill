#!/usr/bin/env python3
"""Deterministic smoke check for giskard.agents tools and workflows.

Prerequisites: Python 3.12+ with ``giskard-agents`` installed.
Example: ``python sub-skills/agents-workflows/scripts/run_agents_smoke.py``

The script intentionally avoids live providers, network calls, credentials, and
source-checkout assumptions. It creates a local ``BaseGenerator`` that requests a
registered ``@tool``, verifies ``Tool.run`` argument coercion and JSON-safe
serialization, and runs a structured-output ``ChatWorkflow`` through ``run_many``.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from collections.abc import Sequence
from typing import Any, override

# Avoid optional telemetry side effects during diagnostics; callers may override
# these in their own process if they want telemetry enabled.
os.environ.setdefault("DO_NOT_TRACK", "1")
os.environ.setdefault("GISKARD_TELEMETRY_DISABLED", "1")

try:
    import giskard.agents as agents
    from giskard.agents.generators import GenerationParams
    from giskard.llm.types import (
        AssistantMessage,
        ChatMessage,
        Choice,
        CompletionResponse,
        ToolCall,
        ToolCallFunction,
    )
    from pydantic import BaseModel, Field
except Exception as exc:  # pragma: no cover - diagnostic path
    print(
        "ERROR: failed to import giskard.agents. Install giskard-agents "
        "or the root giskard distribution in this Python environment.",
        file=sys.stderr,
    )
    print(f"Import detail: {type(exc).__name__}: {exc}", file=sys.stderr)
    raise SystemExit(2) from exc


class WeatherRequest(BaseModel):
    """Typed input model used to prove Tool.run coercion."""

    city: str
    units: str = "celsius"


class WeatherReading(BaseModel):
    """Typed tool output used to prove JSON-safe serialization."""

    city: str
    summary: str
    temperature_c: int
    calls_seen: int = Field(ge=1)


class WeatherAnswer(BaseModel):
    """Structured assistant output returned by the local generator."""

    city: str
    summary: str
    tool_calls: int


@agents.tool
def local_weather(request: WeatherRequest, context: agents.RunContext) -> WeatherReading:
    """Return deterministic weather for a city.

    Parameters
    ----------
    request : WeatherRequest
        City and units requested by the workflow.
    context : RunContext
        Per-run state used to count tool calls.
    """

    calls_seen = int(context.get("tool_calls", 0)) + 1
    context.set("tool_calls", calls_seen)
    return WeatherReading(
        city=request.city,
        summary=f"deterministic {request.units} forecast",
        temperature_c=21,
        calls_seen=calls_seen,
    )


class LocalToolCallingGenerator(agents.BaseGenerator):
    """No-provider generator that drives one tool call then returns JSON."""

    async def _call_model(
        self,
        messages: Sequence[ChatMessage],
        params: GenerationParams,
        metadata: dict[str, Any] | None = None,
    ) -> CompletionResponse:
        del metadata
        last = messages[-1] if messages else None

        if params.tools and getattr(last, "role", None) != "tool":
            return CompletionResponse(
                choices=[
                    Choice(
                        message=AssistantMessage(
                            tool_calls=[
                                ToolCall(
                                    id="call_local_weather",
                                    function=ToolCallFunction(
                                        name=params.tools[0].name,
                                        arguments={
                                            "request": {
                                                "city": "Paris",
                                                "units": "celsius",
                                            }
                                        },
                                    ),
                                )
                            ]
                        ),
                        finish_reason="tool_calls",
                        index=0,
                    )
                ],
                model="local-tool-calling-generator",
            )

        if getattr(last, "role", None) != "tool":
            raise RuntimeError("expected a tool message before final completion")

        reading = WeatherReading.model_validate_json(last.content or "{}")
        answer = WeatherAnswer(
            city=reading.city,
            summary=reading.summary,
            tool_calls=reading.calls_seen,
        )
        return CompletionResponse(
            choices=[
                Choice(
                    message=AssistantMessage(content=answer.model_dump_json()),
                    finish_reason="stop",
                    index=0,
                )
            ],
            model="local-tool-calling-generator",
        )


async def _run() -> int:
    print(f"giskard.agents version: {getattr(agents, '__version__', 'unknown')}")
    print(f"tool name: {local_weather.name}")
    print(f"tool schema fields: {sorted(local_weather.parameters_schema['properties'])}")

    # Direct Tool.run smoke: verifies nested BaseModel coercion, RunContext
    # injection, and JSON-safe serialization before any workflow runs.
    direct_context = agents.RunContext()
    raw_tool_result = await local_weather.run(
        {"request": {"city": "Paris", "units": "celsius"}}, ctx=direct_context
    )
    parsed_tool_result = json.loads(raw_tool_result)
    assert parsed_tool_result["city"] == "Paris", parsed_tool_result
    assert parsed_tool_result["calls_seen"] == 1, parsed_tool_result
    assert direct_context.get("tool_calls") == 1, direct_context
    print(f"direct Tool.run result: {raw_tool_result}")

    generator = LocalToolCallingGenerator()
    workflow = (
        agents.ChatWorkflow(generator=generator)
        .chat("Use the local_weather tool for {{ city }}.", as_template=True)
        .with_inputs(city="Paris")
        .with_tools(local_weather)
        .with_output(WeatherAnswer, strict=True, num_retries=0)
    )

    chats = await workflow.run_many(n=2, max_steps=3)
    assert len(chats) == 2, len(chats)

    for idx, chat in enumerate(chats, start=1):
        assert not chat.failed, chat.error
        assert chat.context.inputs["city"] == "Paris", chat.context.inputs
        assert chat.context.get("tool_calls") == 1, chat.context.data
        assert chat.output == WeatherAnswer(
            city="Paris",
            summary="deterministic celsius forecast",
            tool_calls=1,
        ), chat.output
        print(
            f"workflow chat {idx}: last_role={chat.last.role} "
            f"output={chat.output.model_dump_json()}"
        )

    print("OK: deterministic agents workflow/tool smoke passed without provider calls")
    return 0


def main() -> int:
    try:
        return asyncio.run(_run())
    except AssertionError as exc:
        print(f"ERROR: smoke assertion failed: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # pragma: no cover - diagnostic path
        print(f"ERROR: smoke failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
