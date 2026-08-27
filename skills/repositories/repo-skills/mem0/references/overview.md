# Mem0 Repository Overview

Mem0 is a memory layer for AI agents and assistants. The repository is a polyglot monorepo containing hosted Platform clients, local OSS memory implementations, CLIs, self-hosted services, editor/agent plugins, integrations, examples, docs, and tests.

## Package Boundaries

| Area | Package/surface | Primary role |
| --- | --- | --- |
| `mem0/` | Python distribution `mem0ai` | Hosted `MemoryClient`/`AsyncMemoryClient`, OSS `Memory`/`AsyncMemory`, providers, configs, vector stores, rerankers, utilities. |
| `mem0-ts/` | npm package `mem0ai` | Hosted TypeScript client and OSS `Memory` from `mem0ai/oss`. |
| `cli/python/` | Python package `mem0-cli` | Typer/Rich CLI with `mem0` entry point. |
| `cli/node/` | npm package `@mem0/cli` | Commander CLI with the same command contract and `mem0` binary. |
| `server/` | Self-hosted server | FastAPI REST API, dashboard, auth, API keys, request logs, Postgres/pgvector deployment. |
| `openmemory/` | Self-hosted memory platform | API, UI, Qdrant-backed local memory app, MCP server. |
| `integrations/vercel-ai-sdk/` | npm package `@mem0/vercel-ai-provider` | Vercel AI SDK provider wrapper and standalone memory utilities. |
| `integrations/mem0-plugin/` | editor/agent plugin | MCP configuration, lifecycle hooks, slash-command skills for Claude, Cursor, Codex, OpenCode, Antigravity. |
| `integrations/openclaw/`, `integrations/pi-agent-plugin/` | agent plugins | Memory integration for OpenClaw and Pi Agent. |
| `docs/`, `examples/`, `tests/` | evidence and validation | Public workflows, edge cases, fixtures, and intended behavior. |

## Primary Workflows

- Add/retrieve/update/delete memories in Python or TypeScript applications.
- Configure local OSS memory components for LLMs, embeddings, vector stores, rerankers, and retrieval behavior.
- Operate memories from terminal commands with machine-readable JSON for agents.
- Deploy self-hosted Mem0 or OpenMemory when users need local infrastructure, dashboards, API keys, audit logs, or local MCP.
- Integrate Mem0 into agent/editor and framework ecosystems.

## Version-sensitive Facts

- Python SDK in this checkout: `mem0ai 2.0.7`, Python `>=3.10,<4.0`.
- TypeScript SDK in this checkout: `mem0ai 3.0.9`, Node `>=18`.
- Current SDK docs and tests emphasize v3-style Platform endpoints and filters for scoped search.
- Python OSS `Memory` defaults include OpenAI components and local Qdrant/SQLite paths unless configured differently.
- TypeScript OSS `Memory` defaults are local-friendly and support custom history stores.
- CLI command behavior is specified centrally by `cli/cli-spec.json` and implemented by both Python and Node packages.

## Evidence Used

This skill distilled repository evidence from source, docs, examples, tests, and existing repo-local skills. Original repo files are not runtime dependencies. When a future agent needs executable checks, use the bundled scripts under this skill tree or package-installed commands rather than paths in the source checkout.
