#!/usr/bin/env python3
"""Smoke-check LangGraph in-memory checkpoint persistence.

This script uses only public package APIs and an in-memory checkpoint saver. It is
safe for local validation because it requires no credentials, network, database,
or writes outside the Python process.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import TypedDict


class CounterState(TypedDict):
    count: int


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a tiny LangGraph checkpoint smoke check with InMemorySaver.",
    )
    parser.add_argument(
        "--thread-id",
        default="skill-smoke-thread",
        help="Thread id to use for both graph invocations.",
    )
    parser.add_argument(
        "--initial-count",
        type=int,
        default=0,
        help="Initial counter value for the first invocation.",
    )
    return parser


def run_smoke(thread_id: str, initial_count: int) -> dict[str, object]:
    try:
        from langgraph.checkpoint.memory import InMemorySaver
        from langgraph.graph import END, START, StateGraph
    except Exception as exc:  # pragma: no cover - intentionally broad for CLI help
        raise RuntimeError(
            "Could not import LangGraph checkpoint APIs. Install langgraph and "
            "langgraph-checkpoint in the active Python environment."
        ) from exc

    def increment(state: CounterState) -> CounterState:
        return {"count": state.get("count", 0) + 1}

    builder = StateGraph(CounterState)
    builder.add_node("increment", increment)
    builder.add_edge(START, "increment")
    builder.add_edge("increment", END)

    checkpointer = InMemorySaver()
    graph = builder.compile(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": thread_id}}

    first = graph.invoke({"count": initial_count}, config)
    second = graph.invoke({}, config)
    checkpoints = list(checkpointer.list(config))

    ok = (
        first.get("count") == initial_count + 1
        and second.get("count") == initial_count + 2
        and len(checkpoints) >= 2
    )

    return {
        "ok": ok,
        "thread_id": thread_id,
        "first_result": first,
        "second_result": second,
        "checkpoint_count": len(checkpoints),
        "latest_checkpoint_id": checkpoints[0].config["configurable"].get(
            "checkpoint_id"
        )
        if checkpoints
        else None,
    }


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        payload = run_smoke(args.thread_id, args.initial_count)
    except RuntimeError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2), file=sys.stderr)
        return 2

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
