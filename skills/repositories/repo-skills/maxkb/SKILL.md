---
name: "maxkb"
description: "Routes MaxKB repo work to focused sub-skills for runtime,
  workflows, knowledge/models, frontend, and admin surfaces."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# MaxKB

Use this skill for repo-specific work in MaxKB.

## Start here
1. Read `references/repo-provenance.md`.
2. Read `references/repo-overview.md`.
3. Pick the narrowest sub-skill that matches the task.

## Sub-skills
- `runtime-architecture` — service entrypoints, settings, config, Celery, static assets, migration/startup commands, and runtime troubleshooting.
- `workflow-chat-mcp` — application workflow engine, chat runtime, streaming responses, and MCP JSON-RPC execution.
- `knowledge-models` — knowledge/document/vector-search flows plus model-provider and local-model integration.
- `frontend-integration` — Vue/Vite admin/chat SPA, router/proxy/build contract, workflow canvas UI, and static asset integration.
- `admin-access` — users, permissions, folders, homepage, system settings, OSS/file access, tools, and triggers.

## Working rules
- Keep diffs small and preserve existing formatting.
- Prefer repository evidence over guesswork.
- If a check depends on DB, Redis, Node, or live services, say that explicitly.
- If a path prefix or setting can change, point to the canonical config source.
- Use the bundled root doctor script for a quick static snapshot when needed.

## Good handoff shape
- What you changed or learned.
- What evidence you used.
- What you verified.
- What remains uncertain.
