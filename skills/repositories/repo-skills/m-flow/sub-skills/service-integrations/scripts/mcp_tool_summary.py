#!/usr/bin/env python3
"""Static MCP tool summary for the M-flow service-integrations sub-skill.

This script is read-only and deterministic. It does not start the MCP server,
contact remote services, or inspect the local environment beyond its own
arguments.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ToolSpec:
    name: str
    arguments: str
    transport_notes: str
    api_mode_notes: str


TOOLS: list[ToolSpec] = [
    ToolSpec(
        name="memorize",
        arguments="data, dataset_name='main_dataset', wait=False",
        transport_notes="returns task_id; wait=True blocks for completion",
        api_mode_notes="remote mode supported",
    ),
    ToolSpec(
        name="save_interaction",
        arguments="data, wait=False",
        transport_notes="returns task_id; uses same registry as memorize",
        api_mode_notes="remote mode supported",
    ),
    ToolSpec(
        name="search",
        arguments="search_query, recall_mode, top_k, datasets, system_prompt, enable_hybrid_search",
        transport_notes="raw MCP search surface",
        api_mode_notes="remote mode supported",
    ),
    ToolSpec(
        name="list_data",
        arguments="dataset_id=None",
        transport_notes="lists datasets or visible data items",
        api_mode_notes="dataset-detail lookup is limited remotely",
    ),
    ToolSpec(
        name="delete",
        arguments="data_id, dataset_id, mode='soft'",
        transport_notes="soft/hard delete",
        api_mode_notes="remote mode supported",
    ),
    ToolSpec(
        name="prune",
        arguments="graph=True, vector=True, metadata=False, cache=True",
        transport_notes="guarded cleanup; do not treat as routine",
        api_mode_notes="admin-gated remotely",
    ),
    ToolSpec(
        name="memorize_status",
        arguments="task_id=None",
        transport_notes="task registry lookup or pipeline status fallback",
        api_mode_notes="remote mode supported",
    ),
    ToolSpec(
        name="learn",
        arguments="datasets=None, episode_ids=None, run_in_background=False",
        transport_notes="procedural extraction",
        api_mode_notes="episode_ids not supported remotely",
    ),
    ToolSpec(
        name="update_data",
        arguments="data_id, data, dataset_id",
        transport_notes="replace existing content",
        api_mode_notes="remote mode supported",
    ),
    ToolSpec(
        name="ingest",
        arguments="data, dataset_name='main_dataset', skip_memorize=False",
        transport_notes="one-step ingestion",
        api_mode_notes="remote mode supported",
    ),
    ToolSpec(
        name="query",
        arguments="question, datasets=None, mode='episodic', top_k=10",
        transport_notes="simplified natural-language query",
        api_mode_notes="remote mode supported",
    ),
]

TRANSPORTS = [
    {
        "name": "stdio",
        "use": "local IDEs and direct CLI runs",
        "flags": "default transport; no HTTP port",
    },
    {
        "name": "sse",
        "use": "Docker and browser-facing integrations",
        "flags": "--transport sse --port 8000",
    },
    {
        "name": "http",
        "use": "streamable HTTP clients",
        "flags": "--transport http --path /mcp",
    },
]

API_MODE = [
    {"feature": "backend switch", "detail": "--api-url points the MCP client at a remote M-flow backend"},
    {"feature": "auth token", "detail": "--api-token adds bearer auth for protected endpoints"},
    {"feature": "query", "detail": "POST /api/v1/search/query"},
    {"feature": "learn", "detail": "POST /api/v1/procedural/extract-from-episodic"},
    {"feature": "update", "detail": "PATCH /api/v1/update"},
    {"feature": "ingest", "detail": "POST /api/v1/ingest"},
    {"feature": "prune data", "detail": "POST /api/v1/prune/data"},
    {"feature": "prune system", "detail": "POST /api/v1/prune/system"},
]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Print the static M-flow MCP tool summary.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    parser.add_argument(
        "--tool",
        action="append",
        choices=[tool.name for tool in TOOLS],
        help="Limit output to selected tools; repeatable.",
    )
    return parser.parse_args()


def _selected_tools(names: list[str] | None) -> list[ToolSpec]:
    if not names:
        return TOOLS
    wanted = set(names)
    return [tool for tool in TOOLS if tool.name in wanted]


def _print_text(tools: list[ToolSpec]) -> None:
    print(f"MCP tools: {len(tools)} selected / {len(TOOLS)} total")
    for tool in tools:
        print(f"- {tool.name}")
        print(f"  args: {tool.arguments}")
        print(f"  transport: {tool.transport_notes}")
        print(f"  api mode: {tool.api_mode_notes}")
    print("")
    print("Transports")
    for item in TRANSPORTS:
        print(f"- {item['name']}: {item['use']} ({item['flags']})")
    print("")
    print("API mode")
    for item in API_MODE:
        print(f"- {item['feature']}: {item['detail']}")


def main() -> int:
    args = _parse_args()
    tools = _selected_tools(args.tool)
    if args.json:
        payload: dict[str, Any] = {
            "tools": [asdict(tool) for tool in tools],
            "transports": TRANSPORTS,
            "api_mode": API_MODE,
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        _print_text(tools)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
