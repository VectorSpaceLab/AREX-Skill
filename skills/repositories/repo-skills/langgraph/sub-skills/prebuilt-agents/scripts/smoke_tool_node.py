#!/usr/bin/env python3
"""Smoke-check LangGraph prebuilt ToolNode and ValidationNode behavior.

The script uses tiny local fixtures only. It requires the public `langgraph`,
`langchain-core`, and `pydantic` packages for the smoke run, but `--help` works
without importing those optional runtime dependencies.
"""

from __future__ import annotations

import argparse
import json
from types import SimpleNamespace
from typing import Any


def _message_summary(message: Any) -> dict[str, Any]:
    return {
        "type": getattr(message, "type", None),
        "name": getattr(message, "name", None),
        "content": getattr(message, "content", None),
        "tool_call_id": getattr(message, "tool_call_id", None),
        "status": getattr(message, "status", None),
        "is_error": bool(getattr(message, "additional_kwargs", {}).get("is_error")),
    }


def run_smoke() -> dict[str, Any]:
    try:
        from langchain_core.messages import AIMessage
        from langgraph.prebuilt import ToolNode, ValidationNode
        from langgraph.runtime import ExecutionInfo
        from pydantic import BaseModel, field_validator
    except ModuleNotFoundError as error:
        return {
            "ok": False,
            "error": "missing_dependency",
            "missing_module": error.name,
            "install_hint": "Install the public langgraph package in this Python environment.",
        }

    class SelectNumber(BaseModel):
        """Validation schema used by the smoke check."""

        a: int

        @field_validator("a")
        @classmethod
        def must_be_37(cls, value: int) -> int:
            if value != 37:
                raise ValueError("Only 37 is allowed")
            return value

    def add(a: int, b: int) -> int:
        """Add two integers."""
        return a + b

    def explode(kind: str) -> str:
        """Raise a deterministic error for smoke-checking error ToolMessages."""
        raise ValueError(f"boom:{kind}")

    runtime = SimpleNamespace(
        store=None,
        context=None,
        stream_writer=lambda *args, **kwargs: None,
        execution_info=ExecutionInfo(
            checkpoint_id="smoke-checkpoint",
            checkpoint_ns="",
            task_id="smoke-task",
        ),
        server_info=None,
    )
    config = {"configurable": {"__pregel_runtime": runtime}}

    tool_node = ToolNode([add, explode], handle_tool_errors=True)
    tool_result = tool_node.invoke(
        {
            "messages": [
                AIMessage(
                    content="",
                    tool_calls=[
                        {"name": "add", "args": {"a": 2, "b": 3}, "id": "call-add"},
                        {"name": "explode", "args": {"kind": "fixture"}, "id": "call-error"},
                    ],
                )
            ]
        },
        config=config,
    )

    validation_result = ValidationNode([SelectNumber]).invoke(
        {
            "messages": [
                AIMessage(
                    content="",
                    tool_calls=[
                        {"name": "SelectNumber", "args": {"a": 42}, "id": "call-validate"}
                    ],
                )
            ]
        }
    )

    tool_messages = tool_result["messages"]
    validation_messages = validation_result["messages"]

    checks = {
        "add_result_is_5": tool_messages[0].content == "5",
        "error_status_returned": getattr(tool_messages[1], "status", None) == "error",
        "validation_error_flagged": bool(validation_messages[0].additional_kwargs.get("is_error")),
        "tool_ids_preserved": [m.tool_call_id for m in tool_messages] == ["call-add", "call-error"],
        "validation_id_preserved": validation_messages[0].tool_call_id == "call-validate",
    }

    return {
        "ok": all(checks.values()),
        "checks": checks,
        "tool_messages": [_message_summary(message) for message in tool_messages],
        "validation_messages": [_message_summary(message) for message in validation_messages],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run a tiny LangGraph prebuilt ToolNode/ValidationNode smoke check."
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output with indentation.",
    )
    args = parser.parse_args()

    result = run_smoke()
    print(json.dumps(result, indent=2 if args.pretty else None, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
