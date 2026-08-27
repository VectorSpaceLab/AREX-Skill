---
name: mem0
description: "Route Mem0 repository tasks across Python/TypeScript SDKs, OSS
  provider configuration, CLI workflows, self-hosted/OpenMemory deployment, and
  framework/editor integrations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Mem0 Repo Skill

Use this repo skill when a task mentions Mem0, `mem0ai`, `MemoryClient`, `Memory`, the Mem0 memory layer, hosted Platform memory, OSS memory, Mem0 CLI, self-hosted Mem0, OpenMemory, Vercel AI SDK memory, MCP/plugin setup, or Mem0 framework integrations.

This is a router for repository-specific Mem0 knowledge. Pick the nearest sub-skill first, then read the linked references or run bundled read-only helpers.

## Quick Route

| User task | Read |
| --- | --- |
| Add/search/update/delete memories from Python or TypeScript code | `sub-skills/sdk-memory/SKILL.md` |
| Use hosted Platform `MemoryClient`, OSS `Memory`, async clients, filters, metadata, categories, feedback, or exports | `sub-skills/sdk-memory/SKILL.md` |
| Configure OSS LLMs, embedders, vector stores, rerankers, Qdrant dimensions, BM25/entity retrieval, graph behavior, or optional extras | `sub-skills/provider-configuration/SKILL.md` |
| Run `mem0 init`, `mem0 add`, `mem0 search`, agent JSON mode, stdin/files, config defaults, import/export, entities, or events from a terminal | `sub-skills/cli-memory/SKILL.md` |
| Deploy or debug self-hosted Mem0 server, dashboard auth, API keys, request logs, Docker Compose, REST API, migrations, or OpenMemory MCP | `sub-skills/self-hosted-openmemory/SKILL.md` |
| Wire Mem0 into Vercel AI SDK, Claude/Cursor/Codex/OpenCode/Antigravity, OpenClaw, Pi Agent, LangChain, LangGraph, LlamaIndex, CrewAI, or other frameworks | `sub-skills/integrations-plugins/SKILL.md` |

## First Checks

1. Identify the surface: hosted Platform SDK, local OSS memory, CLI, self-hosted service, OpenMemory, plugin/MCP, or framework adapter.
2. Confirm runtime requirements: Python 3.10+ for Python packages, Node 18+ for TypeScript/CLI/integration packages, API keys only when live hosted/provider calls are intended.
3. Keep entity scope explicit. Stable `user_id`, `agent_id`, `run_id`, or app/project scope prevents cross-user memory leakage and empty searches.
4. Prefer read-only bundled helpers before live writes. The scripts in this skill inspect imports, configs, specs, or source snippets and redact secrets by default.
5. Confirm destructive operations before deletes, resets, volume wipes, hook rewrites, password resets, or request-log pruning.

## Package Facts

- Python SDK distribution: `mem0ai` version `2.0.7`, import root `mem0`, Python `>=3.10,<4.0`.
- TypeScript SDK package: `mem0ai` version `3.0.9`, exports hosted client and `mem0ai/oss`, Node `>=18`.
- Python CLI package: `mem0-cli` version `0.2.8`, entry point `mem0`, Python `>=3.10`.
- Node CLI package: `@mem0/cli` version `0.2.9`, binary `mem0`, Node `>=18`.
- Vercel provider package: `@mem0/vercel-ai-provider` version `3.0.0`, Node `>=18`.
- Integration packages include `@mem0/openclaw-mem0` and `@mem0/pi-agent-plugin` for agent/editor workflows.

## Core Concepts

- Hosted Platform clients call the Mem0 API and require a Mem0 API key.
- OSS `Memory` objects run in-process and require LLM/embedder/vector store configuration; default examples use OpenAI plus local Qdrant or in-memory/SQLite pieces depending on language.
- Search/get-all entity scoping uses filters in current SDK examples; add/delete-all may accept top-level entity options depending on SDK surface.
- CLI and plugin workflows are operational surfaces. They often manage config files or hooks, so inspect existing config before adding duplicate entries.
- Self-hosted server/OpenMemory workflows are service deployments. Treat auth, secrets, database volumes, backups, and request logs as production operations.

## Shared References and Scripts

- `references/overview.md` gives the repository capability map and package boundaries.
- `references/troubleshooting.md` covers cross-cutting install, API key, version, scoping, and routing failures.
- `references/repo-provenance.md` records the source commit, package versions, and evidence paths for refresh checks.
- `scripts/mem0_environment_check.py --help` performs safe Python package/import and environment checks with secret redaction.

## Safety Rules

- Never print or hardcode `MEM0_API_KEY`, provider keys, self-hosted API keys, `JWT_SECRET`, admin passwords, MCP bearer tokens, or personal memory contents.
- Do not run original repository tests, examples, notebooks, or scripts as runtime instructions from this skill. They were used as evidence only.
- Do not depend on the original repository checkout. Use the bundled references and scripts in this skill tree.
- Ask before mutating user/editor config, starting long-running services, making network writes, deleting memories, or wiping volumes.
