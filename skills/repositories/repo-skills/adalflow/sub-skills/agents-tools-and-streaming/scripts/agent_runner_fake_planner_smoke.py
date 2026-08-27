#!/usr/bin/env python3
"""Service-free smoke check for AdalFlow Agent + Runner mechanics.

Run after installing adalflow:
    python scripts/agent_runner_fake_planner_smoke.py

This script injects a fake planner, so it performs no model-provider calls,
network access, file mutation, or MCP access.
"""

from __future__ import annotations

import asyncio
from typing import Iterable

from adalflow.apps.permission_manager import ApprovalOutcome, PermissionManager
from adalflow.components.agent import Agent, Runner
from adalflow.core.func_tool import FunctionTool
from adalflow.core.tool_manager import ToolManager
from adalflow.core.types import (
    Function,
    GeneratorOutput,
    RawResponsesStreamEvent,
    RunItemStreamEvent,
    RunnerResult,
    ToolCallActivityRunItem,
    ToolOutput,
)


class FakePlanner:
    """Small planner stub that returns a fixed sequence of Function actions."""

    def __init__(self, actions: Iterable[Function], *, raw_prefix: str | None = None):
        self._actions = list(actions)
        self._idx = 0
        self.raw_prefix = raw_prefix

    def _next_output(self) -> GeneratorOutput:
        if self._idx >= len(self._actions):
            return GeneratorOutput(
                data=Function(
                    name="finish",
                    _is_answer_final=True,
                    _answer="planner exhausted",
                )
            )
        action = self._actions[self._idx]
        self._idx += 1

        if self.raw_prefix is None:
            return GeneratorOutput(data=action)

        async def raw_events():
            yield f"{self.raw_prefix}:step-{self._idx}"

        return GeneratorOutput(data=action, raw_response=raw_events())

    def call(self, *, prompt_kwargs, model_kwargs=None, use_cache=None, id=None):
        return self._next_output()

    async def acall(self, *, prompt_kwargs, model_kwargs=None, use_cache=None, id=None):
        await asyncio.sleep(0)
        return self._next_output()

    def get_prompt(self, **kwargs):
        return "fake planner prompt"


def lookup_fact(topic: str) -> ToolOutput:
    """Return a deterministic local fact for a topic."""
    return ToolOutput(
        output={"topic": topic, "fact": f"{topic} is available"},
        observation=f"Found fact for {topic}",
        display=f"{topic}: available",
    )


def staged_lookup(topic: str):
    """Yield progress events and then a deterministic lookup result."""
    yield ToolCallActivityRunItem(data=f"starting lookup for {topic}")
    yield ToolCallActivityRunItem(data="checked local cache")
    yield ToolOutput(
        output={"topic": topic, "fact": "streamed fact"},
        observation=f"Streamed fact for {topic}",
        display="streamed lookup complete",
    )


def dry_run_delete(target: str) -> ToolOutput:
    """Describe a delete operation without performing it."""
    return ToolOutput(
        output={"target": target, "would_delete": True},
        observation=f"Dry-run delete prepared for {target}",
        display=f"Would delete {target}",
    )


def make_runner(actions: Iterable[Function], *, raw_prefix: str | None = None, permission_manager=None) -> Runner:
    tools = [
        FunctionTool(lookup_fact),
        FunctionTool(staged_lookup),
        FunctionTool(dry_run_delete, require_approval=True),
    ]
    tool_manager = ToolManager(tools=tools)
    agent = Agent(
        name="fake-planner-agent",
        tool_manager=tool_manager,
        planner=FakePlanner(actions, raw_prefix=raw_prefix),
        max_steps=4,
        answer_data_type=str,
    )
    return Runner(agent=agent, permission_manager=permission_manager)


def final_answer(text: str) -> Function:
    return Function(name="finish", _is_answer_final=True, _answer=text)


def run_sync_case() -> None:
    runner = make_runner(
        [
            Function(name="lookup_fact", kwargs={"topic": "adalflow"}),
            final_answer("Found fact for adalflow"),
        ]
    )
    result = runner.call(prompt_kwargs={"input_str": "lookup adalflow"})
    assert isinstance(result, RunnerResult)
    assert result.answer == "Found fact for adalflow"
    assert len(result.step_history) == 1
    assert result.step_history[0].observation == "Found fact for adalflow"


def run_permission_denial_case() -> None:
    async def deny_all(request):
        assert request.tool_name == "dry_run_delete"
        return ApprovalOutcome.CANCEL

    permission_manager = PermissionManager(
        approval_callback=deny_all,
        approval_mode="default",
    )
    runner = make_runner(
        [
            Function(name="dry_run_delete", kwargs={"target": "example.txt"}),
            final_answer("permission handled"),
        ],
        permission_manager=permission_manager,
    )
    result = runner.call(prompt_kwargs={"input_str": "try delete"})
    assert result.answer == "permission handled"
    assert len(result.step_history) == 1
    assert result.step_history[0].observation == "Tool execution cancelled by user"


async def run_async_case() -> None:
    runner = make_runner(
        [
            Function(name="lookup_fact", kwargs={"topic": "async"}),
            final_answer("async complete"),
        ]
    )
    result = await runner.acall(prompt_kwargs={"input_str": "lookup async"})
    assert isinstance(result, RunnerResult)
    assert result.answer == "async complete"
    assert len(result.step_history) == 1
    assert result.step_history[0].observation == "Found fact for async"


async def run_streaming_case() -> None:
    runner = make_runner(
        [
            Function(name="staged_lookup", kwargs={"topic": "streaming"}),
            final_answer("streaming complete"),
        ],
        raw_prefix="planner",
    )
    streaming = runner.astream(prompt_kwargs={"input_str": "stream lookup"})

    events = []
    async for event in streaming.stream_events():
        events.append(event)

    raw_events = [event for event in events if isinstance(event, RawResponsesStreamEvent)]
    run_events = [event for event in events if isinstance(event, RunItemStreamEvent)]
    event_names = [event.name for event in run_events]

    assert raw_events, "expected at least one raw planner event"
    assert "agent.tool_call_start" in event_names
    assert "agent.tool_call_activity" in event_names
    assert "agent.tool_call_complete" in event_names
    assert "agent.step_complete" in event_names
    assert "agent.execution_complete" in event_names
    assert streaming.answer == "streaming complete"
    assert streaming.is_complete


async def async_main() -> None:
    await run_async_case()
    await run_streaming_case()


def main() -> None:
    run_sync_case()
    run_permission_denial_case()
    asyncio.run(async_main())
    print("Agent/Runner fake-planner smoke passed")


if __name__ == "__main__":
    main()
