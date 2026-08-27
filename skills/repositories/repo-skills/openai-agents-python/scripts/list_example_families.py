#!/usr/bin/env python3
"""List OpenAI Agents Python example families covered by this skill.

This helper does not execute examples. It provides a safe inventory that future
agents can use when translating a user request into the right sub-skill route.
"""

from __future__ import annotations

import argparse
import json
from typing import Any

FAMILIES: list[dict[str, Any]] = [
    {
        "family": "basic",
        "routes": ["core-runtime", "tools-handoffs-guardrails", "models-providers", "tracing-observability"],
        "covers": "Hello world, streaming text/items, previous_response_id, prompt templates, retries, tools, usage tracking, websocket transport.",
        "native_safety": "skip-credentials for real model calls; compile/import patterns only.",
    },
    {
        "family": "agent_patterns",
        "routes": ["tools-handoffs-guardrails", "core-runtime"],
        "covers": "Routing, parallelization, deterministic flows, agents-as-tools, handoffs, human-in-the-loop, guardrails, judges.",
        "native_safety": "skip-credentials for model calls; use references for patterns.",
    },
    {
        "family": "tools",
        "routes": ["tools-handoffs-guardrails", "models-providers"],
        "covers": "Hosted tools, local shell, hosted shell with skills, computer use, apply patch, web/file search, code interpreter, image generation, tool search.",
        "native_safety": "many examples require credentials, browser/UI, hosted containers, or network.",
    },
    {
        "family": "mcp",
        "routes": ["mcp-and-hosted-tools"],
        "covers": "MCP stdio, SSE, Streamable HTTP, prompt server, server manager, tool filtering, hosted MCP.",
        "native_safety": "local tiny servers may be safe after explicit selection; remote examples are skip-network/credentials.",
    },
    {
        "family": "memory",
        "routes": ["sessions-memory", "core-runtime"],
        "covers": "SQLite, OpenAI conversation sessions, compaction, SQLAlchemy, Redis, MongoDB, Dapr, encrypted sessions, HITL resume.",
        "native_safety": "SQLite/in-memory patterns are safe; external services require extras or services.",
    },
    {
        "family": "model_providers",
        "routes": ["models-providers"],
        "covers": "Custom providers, OpenAI-compatible endpoints, LiteLLM, any-llm, provider-global versus per-run setup.",
        "native_safety": "skip-credentials for live calls; inspect provider construction locally.",
    },
    {
        "family": "realtime",
        "routes": ["realtime-voice", "tools-handoffs-guardrails"],
        "covers": "Realtime app server, CLI demo, Twilio media streams, SIP, tools, handoffs, audio/image/text input.",
        "native_safety": "skip-network/audio/telephony unless explicitly configured.",
    },
    {
        "family": "voice",
        "routes": ["realtime-voice"],
        "covers": "Static and streamed voice pipeline examples with STT/agent/TTS workflow.",
        "native_safety": "requires voice extra and API/audio setup for real runs.",
    },
    {
        "family": "sandbox",
        "routes": ["sandbox-agents", "repo-development"],
        "covers": "Local and Docker sandbox clients, manifests, skills mounting, memory, shell/apply_patch, healthcare/tax/tutorial workflows.",
        "native_safety": "validate manifests safely; do not start Docker/hosted clients or mutate workspaces without explicit intent.",
    },
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a table.")
    parser.add_argument("--route", help="Filter to families owned by a sub-skill id.")
    args = parser.parse_args()
    rows = [row for row in FAMILIES if not args.route or args.route in row["routes"]]
    if args.json:
        print(json.dumps(rows, indent=2, sort_keys=True))
    else:
        for row in rows:
            print(f"{row['family']}: {', '.join(row['routes'])}")
            print(f"  covers: {row['covers']}")
            print(f"  safety: {row['native_safety']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
