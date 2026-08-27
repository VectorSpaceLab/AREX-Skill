---
name: "runtime-architecture"
description: "Covers MaxKB service startup, settings, Celery, static assets,
  migrations, and runtime configuration."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# runtime-architecture

Use this sub-skill for tasks about starting, configuring, or troubleshooting the MaxKB backend runtime.

## Owns
- `main.py` and `apps/manage.py` entrypoints.
- `apps/maxkb/conf.py`, settings selection, and route-prefix configuration.
- Celery bootstrap, queues, static collection, and migration flow.
- Runtime startup docs and safe static inspection of service commands.

## Do not own
- Workflow execution and MCP runtime -> `workflow-chat-mcp`.
- Knowledge retrieval and model catalogs -> `knowledge-models`.
- Vue/Vite build and routing -> `frontend-integration`.
- Users, permissions, folders, tools, triggers, and admin pages -> `admin-access`.

## Key files
- `references/service-entrypoints.md`
- `references/troubleshooting.md`
- `scripts/runtime_command_check.py`

## Guidance
- Prefer repo-relative commands and static checks.
- Mention when a check needs DB, Redis, Celery, or a built `ui/dist`.
- Keep advice tied to the canonical config source instead of hard-coded prefixes.
