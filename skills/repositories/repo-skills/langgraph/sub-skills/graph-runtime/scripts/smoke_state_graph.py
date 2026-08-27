#!/usr/bin/env python3
"""Smoke-check LangGraph StateGraph compile, invoke, routing, reducers, and streaming."""

from __future__ import annotations

import argparse
import json
from typing import Any

from typing_extensions import Annotated, Literal, TypedDict


def append_history(left: list[str], right: list[str] | None) -> list[str]:
    return left + (right or [])


class CounterState(TypedDict):
    value: int
    limit: int
    history: Annotated[list[str], append_history]


def increment(state: CounterState) -> dict[str, Any]:
    next_value = state["value"] + 1
    return {"value": next_value, "history": [f"increment:{next_value}"]}


def route(state: CounterState) -> Literal["again", "done"]:
    return "done" if state["value"] >= state["limit"] else "again"


def finish(state: CounterState) -> dict[str, Any]:
    return {"history": ["finish"]}


def build_graph():
    try:
        from langgraph.graph import END, START, StateGraph
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "LangGraph is not installed in this Python environment. "
            "Install the `langgraph` package, then rerun this smoke check."
        ) from exc

    builder = StateGraph(CounterState)
    builder.add_node("increment", increment)
    builder.add_node("finish", finish)
    builder.add_edge(START, "increment")
    builder.add_conditional_edges(
        "increment",
        route,
        {"again": "increment", "done": "finish"},
    )
    builder.add_edge("finish", END)
    return builder.compile()


def run_smoke(start: int, limit: int) -> dict[str, Any]:
    if limit < start:
        raise ValueError("--limit must be greater than or equal to --start")

    graph = build_graph()
    input_state: CounterState = {"value": start, "limit": limit, "history": []}
    final = graph.invoke(input_state)
    updates = list(graph.stream(input_state, stream_mode="updates"))

    expected_value = limit if start < limit else start + 1
    if final["value"] != expected_value:
        raise AssertionError(f"expected value {expected_value}, got {final['value']}")
    if not final["history"] or final["history"][-1] != "finish":
        raise AssertionError(f"expected final history to end with finish, got {final['history']!r}")
    if not updates:
        raise AssertionError("expected at least one streamed update")

    return {"final": final, "update_count": len(updates), "updates": updates}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build and run a tiny LangGraph StateGraph with reducer state and conditional routing."
    )
    parser.add_argument("--start", type=int, default=0, help="Initial counter value. Default: 0")
    parser.add_argument("--limit", type=int, default=3, help="Route to finish once value reaches this limit. Default: 3")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = run_smoke(args.start, args.limit)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        final = result["final"]
        print("LangGraph StateGraph smoke check passed")
        print(f"final value: {final['value']}")
        print(f"history: {', '.join(final['history'])}")
        print(f"streamed updates: {result['update_count']}")


if __name__ == "__main__":
    main()
