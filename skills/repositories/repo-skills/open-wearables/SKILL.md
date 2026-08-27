---
name: open-wearables
description: "Operating router for the Open Wearables FastAPI backend, wearable
  provider integrations, React portal, and FastMCP server."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Open Wearables

Use this repo skill for Open Wearables, a monorepo that aggregates wearable and health data through a Python/FastAPI backend, React/TanStack Start portal, and FastMCP server for AI assistants.

## Route the task

- Backend API, auth/developer credentials, users, connections, summaries, events, timeseries, sync status, seed data, outgoing webhooks, service/repository/model/schema work, migrations, DB/Redis/Celery/Svix/AWS config, and backend tests → [backend-core](sub-skills/backend-core/SKILL.md).
- Wearable provider strategies, provider enum/factory registration, OAuth handlers, workout/24-7 data handlers, incoming provider webhooks, coverage declarations, coverage docs, provider sync/backfill, and provider-specific tests → [provider-integrations](sub-skills/provider-integrations/SKILL.md).
- React portal routes, protected auth layout, dashboard/users/settings/coverage/sync/webhooks pages, API hooks/services/query keys, runtime `VITE_API_URL`, TanStack Router/Query, components, styling, and frontend test/lint/build work → [frontend-portal](sub-skills/frontend-portal/SKILL.md).
- FastMCP server startup, assistant configuration, MCP tools, REST client behavior, prompts, mocked MCP tests, and MCP API-key/backend failure handling → [mcp-server](sub-skills/mcp-server/SKILL.md).

## Read shared references

- [setup.md](references/setup.md) — prerequisites, install commands, service topology, and safe validation commands.
- [architecture.md](references/architecture.md) — monorepo package map, backend/provider/frontend/MCP data flow, and cross-skill ownership.
- [troubleshooting.md](references/troubleshooting.md) — shared install/import/service/config/credential failures and where to route deeper debugging.
- [repo-provenance.md](references/repo-provenance.md) — source snapshot for staleness checks before refreshing this skill.

Run the safe root checker when a checkout is available:

```bash
python skills/disco/open-wearables/scripts/check_open_wearables_install.py --repo-root .
```

This checker is read-only. It verifies package metadata, expected directories, docs navigation presence, and local tool availability; it does not start services, install packages, call provider APIs, or read real secrets.

## Package and service baseline

- Backend package: `open-wearables==0.7.0`, Python `>=3.13`, FastAPI, SQLAlchemy 2.0, PostgreSQL, Redis, Celery, Svix, AWS/S3 optional storage, Ruff, Ty, Pytest.
- Frontend package: `frontend-app==0.7.0`, Node `>=22`, pnpm `>=10`, React 19, TanStack Start/Router/Query, Tailwind CSS 4, shadcn/ui, Vitest, oxlint, Prettier.
- MCP package: `open-wearables-mcp==0.1.0`, Python `>=3.13`, FastMCP, httpx, Pydantic settings, `start = app.main:main`.
- Local stack: Docker Compose starts backend, frontend, PostgreSQL, Redis, Celery workers/beat/Flower, and Svix services. Use a disposable dev/test stack for seed/reset/replay utilities.

## Boundary rules

- Do not commit real provider credentials, API keys, JWTs, OAuth tokens, Svix secrets, AWS keys, master encryption keys, or `.env` files.
- Keep backend endpoint changes synchronized with frontend/MCP callers and docs. External API endpoints tagged `External: *` require API Reference navigation updates.
- Provider coverage is the source of truth for `/api/v1/meta/coverage` and the portal coverage matrix; changes belong in `provider-integrations` even when surfaced in backend routes or frontend UI.
- MCP is REST-client-driven. Do not bypass the backend by importing backend database models or direct DB access into the MCP package.
- Runtime frontend API URL must go through `resolveApiUrl()` / `API_CONFIG.baseUrl`; do not inline `import.meta.env.VITE_API_URL` in application code.
- Prefer focused native checks after edits: backend targeted pytest, provider coverage/import tests, frontend Vitest/lint/build when dependencies are installed, and MCP mocked pytest.

## Staleness check

Before relying on this skill for a different checkout, read [repo-provenance.md](references/repo-provenance.md). If the commit, package versions, route/plugin entry points, provider inventory, frontend scripts, or MCP tool names changed, use `refresh-repo-skill` rather than patching this skill by hand.
