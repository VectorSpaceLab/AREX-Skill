---
name: cli-and-cloud
description: "Routes Memori Cloud, CLI, quota/sign-up/setup, MCP, and agent API workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# CLI and Cloud

Use this sub-skill for Memori Cloud setup, the `python -m memori` command,
quota and sign-up flows, MCP wiring, and agent-memory API calls.

## Use when

- The request mentions Memori Cloud, `MEMORI_API_KEY`, `python -m memori`,
  quota, sign-up, setup, MCP, Claude Code, Hermes, OpenClaw, or agent recall.
- The user is debugging cloud auth, quota, SSL, timeout, or payload-validation
  failures.
- The task is about Cloud-facing Python or TypeScript quickstarts, not BYODB
  storage or LLM provider registration.

## Read first

- `references/cli-reference.md` for commands and flags.
- `references/cloud-agent-api.md` for cloud agent methods and parameter rules.
- `references/mcp-and-agent-integrations.md` for MCP and adjacent agent
  integrations.
- `references/troubleshooting.md` for cloud/auth/network failures.
- `scripts/check_memori_cli.py` for a safe CLI smoke.

## What this sub-skill owns

- Cloud mode vs BYODB mode selection when `conn` is omitted.
- API key and base URL handling.
- CLI command routing and `.env` loading from the current directory.
- Cloud agent recall, recall-summary, compaction, capture-turn, and feedback.
- MCP connection headers and agent integration setup notes.

## What it does not own

- Storage schema or driver setup: use `byodb-storage`.
- `llm.register(...)` provider selection: use `llm-integration`.
- Recall, embeddings, session lifecycle, or native Rust-core behavior: use
  `memory-and-search`.
- TypeScript implementation details: use `typescript-sdk`.

## Safe first check

Run the bundled CLI smoke before suggesting a live cloud call:

```bash
python scripts/check_memori_cli.py
```

That helper only exercises the installed `python -m memori` entry path from a
fresh temporary working directory.
