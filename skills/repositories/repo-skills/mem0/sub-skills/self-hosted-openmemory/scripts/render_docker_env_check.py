#!/usr/bin/env python3
"""Print a safe Mem0 self-hosted/OpenMemory Docker readiness checklist."""

from __future__ import annotations

import argparse

SERVER_ITEMS = [
    "Docker and Docker Compose are installed and can start services.",
    "Required server env file exists and secrets are set without being printed.",
    "POSTGRES_PASSWORD and JWT_SECRET are set for current self-hosted server versions.",
    "Provider credentials match the configured LLM/embedder before memory writes.",
    "Ports 3000 and 8888 are free or intentionally remapped.",
    "Auth mode is explicit: dashboard/API keys, legacy ADMIN_API_KEY, or local-only AUTH_DISABLED=true.",
    "Upgrade path is known before reusing or wiping Postgres volumes.",
    "Destructive operations such as down -v, reset password, or prune logs have explicit approval.",
]

OPENMEMORY_ITEMS = [
    "OpenMemory API, UI, and Qdrant service definitions are present in the deployment plan.",
    "API environment contains provider credentials and database/vector-store settings.",
    "UI points at the intended local API URL, not hosted Platform unless explicitly desired.",
    "MCP client config uses the local OpenMemory MCP URL and a distinct server name if hosted MCP also exists.",
    "Qdrant/API/UI health is checked before writing test memories.",
    "Backup/export paths are treated as sensitive because they may contain user memories.",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a safe Docker readiness checklist for Mem0 self-hosted deployments.")
    parser.add_argument("--target", choices=("server", "openmemory"), default="server")
    args = parser.parse_args()

    items = SERVER_ITEMS if args.target == "server" else OPENMEMORY_ITEMS
    print(f"# Mem0 {args.target} readiness checklist")
    for index, item in enumerate(items, start=1):
        print(f"{index}. [ ] {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
