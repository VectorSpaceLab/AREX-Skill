#!/usr/bin/env python3
"""Safe AgentChat smoke checks.

This script performs import and signature inspection for high-level
`autogen_agentchat` APIs. It does not make model-provider calls and does not
execute model-generated code.
"""

from __future__ import annotations

import argparse
import inspect
import json
import sys
from typing import Any


TARGETS = [
    ("autogen_agentchat.agents", "AssistantAgent"),
    ("autogen_agentchat.agents", "UserProxyAgent"),
    ("autogen_agentchat.agents", "CodeExecutorAgent"),
    ("autogen_agentchat.teams", "RoundRobinGroupChat"),
    ("autogen_agentchat.teams", "SelectorGroupChat"),
    ("autogen_agentchat.teams", "Swarm"),
    ("autogen_agentchat.teams", "MagenticOneGroupChat"),
    ("autogen_agentchat.conditions", "TextMentionTermination"),
    ("autogen_agentchat.conditions", "MaxMessageTermination"),
    ("autogen_agentchat.conditions", "HandoffTermination"),
    ("autogen_agentchat.tools", "AgentTool"),
    ("autogen_agentchat.tools", "TeamTool"),
]


def import_object(module_name: str, object_name: str) -> Any:
    module = __import__(module_name, fromlist=[object_name])
    return getattr(module, object_name)


def collect_signatures() -> dict[str, str]:
    signatures: dict[str, str] = {}
    for module_name, object_name in TARGETS:
        obj = import_object(module_name, object_name)
        signatures[object_name] = str(inspect.signature(obj))
    return signatures


def construct_safe_primitives() -> dict[str, str]:
    from autogen_agentchat.conditions import HandoffTermination, MaxMessageTermination, TextMentionTermination
    from autogen_agentchat.agents import UserProxyAgent

    objects = {
        "TextMentionTermination": TextMentionTermination("TERMINATE"),
        "MaxMessageTermination": MaxMessageTermination(3),
        "HandoffTermination": HandoffTermination("human"),
        "UserProxyAgent": UserProxyAgent("human", input_func=lambda prompt: "ok"),
    }
    return {name: type(value).__name__ for name, value in objects.items()}


def run(mode: str) -> int:
    try:
        payload: dict[str, Any] = {"mode": mode, "signatures": collect_signatures()}
        if mode == "construct":
            payload["constructed"] = construct_safe_primitives()
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    except Exception as exc:  # pragma: no cover - diagnostic script
        print(
            json.dumps(
                {
                    "ok": False,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                    "hint": (
                        "Install compatible autogen-agentchat/autogen-core/autogen-ext packages, "
                        "or run from an environment where those packages are importable. "
                        "This script performs no provider calls."
                    ),
                },
                indent=2,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect AgentChat signatures without provider calls.")
    parser.add_argument(
        "--mode",
        choices=["signatures", "construct"],
        default="signatures",
        help="signatures prints constructor signatures; construct also builds no-provider primitives.",
    )
    args = parser.parse_args()
    return run(args.mode)


if __name__ == "__main__":
    raise SystemExit(main())
