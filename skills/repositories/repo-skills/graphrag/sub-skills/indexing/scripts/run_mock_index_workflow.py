#!/usr/bin/env python3
"""Demonstrate a tiny offline GraphRAG custom indexing workflow contract."""

from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class MockCallbacks:
    """Collect workflow lifecycle events without requiring GraphRAG services."""

    events: list[str] = field(default_factory=list)

    def workflow_start(self, name: str, _details: Any = None) -> None:
        self.events.append(f"start:{name}")

    def workflow_end(self, name: str, _result: Any = None) -> None:
        self.events.append(f"end:{name}")


@dataclass
class MockContext:
    """Minimal context shape used by the mock workflow."""

    callbacks: MockCallbacks = field(default_factory=MockCallbacks)
    state: dict[str, Any] = field(default_factory=dict)
    tables: dict[str, list[dict[str, Any]]] = field(default_factory=dict)


@dataclass
class MockWorkflowFunctionOutput:
    """Small stand-in for GraphRAG's WorkflowFunctionOutput."""

    result: Any | None
    stop: bool = False


async def mock_byog_contract_workflow(_config: Any, context: MockContext) -> MockWorkflowFunctionOutput:
    """Validate a tiny BYOG graph contract and create a mock community row."""
    entities = context.tables.get("entities", [])
    relationships = context.tables.get("relationships", [])
    entity_titles = {row.get("title") for row in entities}
    orphan_edges = [
        row
        for row in relationships
        if row.get("source") not in entity_titles or row.get("target") not in entity_titles
    ]
    if orphan_edges:
        return MockWorkflowFunctionOutput(
            result={"valid": False, "orphan_relationship_count": len(orphan_edges)},
            stop=True,
        )

    context.tables["communities"] = [
        {
            "id": "community-0",
            "community": 0,
            "level": 0,
            "title": "Mock community",
            "entity_ids": [row["id"] for row in entities],
            "relationship_ids": [row["id"] for row in relationships],
        }
    ]
    return MockWorkflowFunctionOutput(
        result={
            "valid": True,
            "entity_count": len(entities),
            "relationship_count": len(relationships),
            "created_tables": ["communities"],
        }
    )


async def run_mock_pipeline(include_orphan: bool) -> dict[str, Any]:
    context = MockContext(
        state={"additional_context": {"purpose": "offline custom workflow contract demo"}},
        tables={
            "entities": [
                {"id": "e-alice", "title": "ALICE", "description": "Person"},
                {"id": "e-bob", "title": "BOB", "description": "Person"},
            ],
            "relationships": [
                {
                    "id": "r-1",
                    "source": "ALICE",
                    "target": "BOB",
                    "description": "Knows",
                    "weight": 1.0,
                }
            ],
        },
    )
    if include_orphan:
        context.tables["relationships"].append(
            {
                "id": "r-orphan",
                "source": "ALICE",
                "target": "GHOST",
                "description": "Invalid endpoint",
                "weight": 1.0,
            }
        )

    workflow_name = "mock_byog_contract"
    context.callbacks.workflow_start(workflow_name)
    output = await mock_byog_contract_workflow(None, context)
    context.callbacks.workflow_end(workflow_name, output.result)

    return {
        "workflow": workflow_name,
        "result": output.result,
        "stop": output.stop,
        "events": context.callbacks.events,
        "tables": sorted(context.tables),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run an offline mock GraphRAG indexing workflow contract. This does not call "
            "LLMs, read project config, or require credentials."
        )
    )
    parser.add_argument(
        "--include-orphan",
        action="store_true",
        help="Include an invalid relationship endpoint to demonstrate stop-on-contract-failure behavior.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = asyncio.run(run_mock_pipeline(args.include_orphan))
    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if report["stop"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
