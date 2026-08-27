#!/usr/bin/env python3
"""Deterministic smoke checks for Langroid agent/task/tool flows.

This script avoids provider keys by using MockLMConfig. It also delays importing
Langroid until after argument parsing so `--help` works even in minimal
installations.
"""

from __future__ import annotations

import argparse
import json
import inspect
import sys
import types
from dataclasses import dataclass
from typing import Any


def _ensure_optional_logging_stub() -> None:
    """Provide a tiny colorlog fallback when the optional package is absent."""
    try:
        import colorlog  # noqa: F401

        return
    except Exception:
        pass

    class _PlainColoredFormatter:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            import logging

            log_format = args[0] if args else "%(levelname)s %(message)s"
            datefmt = kwargs.get("datefmt")
            self._formatter = logging.Formatter(log_format, datefmt=datefmt)

        def format(self, record: Any) -> str:
            return self._formatter.format(record)

    stub = types.ModuleType("colorlog")
    stub.ColoredFormatter = _PlainColoredFormatter
    sys.modules["colorlog"] = stub


@dataclass(frozen=True)
class Summary:
    prompt: str
    number: int
    result: str
    tool_request: str
    enable_message_signature: list[str]
    mocklm_fields: list[str]
    task_done_sequences_default: Any
    parsed_done_sequence: dict[str, Any]
    config_use_tools: bool
    config_use_functions_api: bool


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Smoke-test a custom ToolMessage, a ChatAgent handler, MockLMConfig, "
            "and done_sequences parsing without provider keys."
        )
    )
    parser.add_argument(
        "--number",
        type=int,
        default=7,
        help="Integer to square in the demo task.",
    )
    parser.add_argument(
        "--prompt",
        default="",
        help="Prompt text to map to the mock tool call. Defaults to 'square N'.",
    )
    return parser


def _serialize_done_sequence(sequence: Any) -> dict[str, Any]:
    events = []
    for event in sequence.events:
        events.append(
            {
                "event_type": getattr(event.event_type, "value", str(event.event_type)),
                "tool_name": event.tool_name,
                "tool_class": getattr(event.tool_class, "__name__", None),
                "responder": event.responder,
                "sender": event.sender,
                "content_pattern": event.content_pattern,
            }
        )
    return {"name": sequence.name, "events": events}


def run(number: int, prompt: str) -> Summary:
    _ensure_optional_logging_stub()

    from pydantic import Field

    from langroid.agent.chat_agent import ChatAgent, ChatAgentConfig
    from langroid.agent.done_sequence_parser import parse_done_sequences
    from langroid.agent.task import Task, TaskConfig
    from langroid.agent.tool_message import ToolMessage
    from langroid.language_models.mock_lm import MockLMConfig

    class SquareTool(ToolMessage):
        request: str = "square"
        purpose: str = "Square an integer and return the exact result."
        number: int = Field(..., description="Integer to square")

    class DemoAgent(ChatAgent):
        def square(self, msg: SquareTool) -> str:
            return str(msg.number * msg.number)

    prompt_text = prompt or f"square {number}"
    square_json = SquareTool(number=number).model_dump_json()

    # Installed-fact checks that should stay true for this workflow.
    assert ChatAgentConfig().use_tools is True
    assert TaskConfig().done_sequences is None
    assert "response" not in MockLMConfig.model_fields
    assert "response_dict" in MockLMConfig.model_fields
    assert "default_response" in MockLMConfig.model_fields

    config = ChatAgentConfig(
        name="agents-tasks-tools-smoke",
        llm=MockLMConfig(
            response_dict={prompt_text: square_json},
            default_response=square_json,
        ),
        system_message="You are a deterministic math assistant.",
        use_tools=True,
        use_functions_api=False,
        handle_llm_no_tool="done",
    )
    agent = DemoAgent(config)
    agent.enable_message(SquareTool)

    enable_message_signature = [
        param.name for param in inspect.signature(agent.enable_message).parameters.values()
    ]
    expected_signature = [
        "message_class",
        "use",
        "handle",
        "force",
        "require_recipient",
        "include_defaults",
    ]
    assert enable_message_signature[: len(expected_signature)] == expected_signature

    task_config = TaskConfig(
        done_sequences=["T[SquareTool], A"],
        enable_loggers=False,
        enable_html_logging=False,
    )
    parsed = parse_done_sequences(task_config.done_sequences, agent.llm_tools_map)
    assert len(parsed) == 1
    assert parsed[0].events[0].tool_class is SquareTool
    assert parsed[0].events[1].event_type.value == "agent_response"

    task = Task(agent, config=task_config, interactive=False)
    parsed_from_task = getattr(task, "_parsed_done_sequences", None)
    assert parsed_from_task and parsed_from_task[0].events[0].tool_class is SquareTool

    result = task.run(prompt_text, turns=4)
    if result is None:
        raise RuntimeError("Task returned no result")

    assert result.content == str(number * number)
    # The returned result is the handled agent response, not the original tool
    # payload. The exact handler was proven by the done-sequence class match and
    # by the squared numeric result.
    return Summary(
        prompt=prompt_text,
        number=number,
        result=result.content,
        tool_request=SquareTool.name(),
        enable_message_signature=enable_message_signature,
        mocklm_fields=sorted(
            name
            for name in (
                "response_dict",
                "response_fn",
                "response_fn_async",
                "default_response",
            )
            if name in MockLMConfig.model_fields
        ),
        task_done_sequences_default=TaskConfig().done_sequences,
        parsed_done_sequence=_serialize_done_sequence(parsed[0]),
        config_use_tools=agent.config.use_tools,
        config_use_functions_api=agent.config.use_functions_api,
    )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        summary = run(args.number, args.prompt)
    except Exception as exc:  # pragma: no cover - runtime smoke reporting
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": type(exc).__name__,
                    "message": str(exc),
                },
                indent=2,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2

    print(
        json.dumps(
            {
                "ok": True,
                "prompt": summary.prompt,
                "number": summary.number,
                "result": summary.result,
                "tool_request": summary.tool_request,
                "enable_message_signature": summary.enable_message_signature,
                "mocklm_fields": summary.mocklm_fields,
                "task_done_sequences_default": summary.task_done_sequences_default,
                "parsed_done_sequence": summary.parsed_done_sequence,
                "config_use_tools": summary.config_use_tools,
                "config_use_functions_api": summary.config_use_functions_api,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
