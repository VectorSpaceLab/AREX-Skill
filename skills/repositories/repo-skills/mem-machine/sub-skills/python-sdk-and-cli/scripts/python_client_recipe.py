#!/usr/bin/env python3
"""Print or run a minimal MemMachine Python SDK recipe.

Default mode prints a safe recipe. `--live-health` contacts only the health
endpoint. `--live-demo` writes a supplied memory and should be used only with an
explicit test project and user approval.
"""

from __future__ import annotations

import argparse
import os
from typing import Iterable

RECIPE = '''from memmachine_client import MemMachineClient

client = MemMachineClient(base_url="http://localhost:8080", api_key=None)
try:
    project = client.get_or_create_project(org_id="my-org", project_id="my-project")
    memory = project.memory(metadata={"user_id": "alice", "agent_id": "assistant"})
    memory.add("Alice prefers aisle seats.", metadata={"category": "travel"})
    result = memory.search("What seating does Alice prefer?", limit=5)
    print(result)
finally:
    client.close()
'''


def build_client(base_url: str, api_key: str | None):
    from memmachine_client import MemMachineClient

    return MemMachineClient(base_url=base_url, api_key=api_key)


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Show or run a minimal MemMachine Python SDK recipe.")
    parser.add_argument("--base-url", default=os.environ.get("MEMORY_BACKEND_URL"), help="MemMachine server URL for live modes.")
    parser.add_argument("--api-key", default=os.environ.get("MEMMACHINE_API_KEY"), help="API key for live modes; not printed.")
    parser.add_argument("--org-id", default="demo-org")
    parser.add_argument("--project-id", default="demo-project")
    parser.add_argument("--user-id", default="demo-user")
    parser.add_argument("--agent-id", default="demo-agent")
    parser.add_argument("--content", default="This is a MemMachine SDK smoke-test memory.")
    parser.add_argument("--query", default="What memory was added by the smoke test?")
    parser.add_argument("--live-health", action="store_true", help="Contact the server health endpoint only.")
    parser.add_argument("--live-demo", action="store_true", help="Create/get a project, add one memory, and search it. Requires approval.")
    args = parser.parse_args(argv)

    if not args.live_health and not args.live_demo:
        print(RECIPE)
        return 0
    if not args.base_url:
        raise SystemExit("--base-url or MEMORY_BACKEND_URL is required for live modes")

    client = build_client(args.base_url, args.api_key)
    try:
        print("health:", client.health_check())
        if args.live_demo:
            project = client.get_or_create_project(args.org_id, args.project_id)
            memory = project.memory(metadata={"user_id": args.user_id, "agent_id": args.agent_id})
            print("add:", memory.add(args.content, metadata={"source": "sdk-smoke"}))
            print("search:", memory.search(args.query, limit=3))
    finally:
        client.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
