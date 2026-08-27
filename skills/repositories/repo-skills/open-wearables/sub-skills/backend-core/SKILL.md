---
name: backend-core
description: "FastAPI backend routes, auth credentials, data services,
  migrations, tests, and service-layer troubleshooting for Open Wearables."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Backend Core

Use this sub-skill for Open Wearables FastAPI backend work: API routes, developer auth, API keys, SDK applications, users, connections, summaries, events, health scores, timeseries, sync status, seed data, outgoing webhooks, service/repository/model/schema patterns, configuration, migrations, Celery/Redis orchestration, and backend tests.

## Route the task

- For endpoint families, auth requirements, route registration, OpenAPI/docs navigation, and API-change checklists, read [api-routes.md](references/api-routes.md).
- For data models, repositories, service layer patterns, schemas, summaries/events/timeseries flow, sync status, seed data, and outgoing webhook internals, read [data-model-and-services.md](references/data-model-and-services.md).
- For concrete backend commands, local Docker/uv workflows, migrations, seeding, targeted pytest selection, and endpoint implementation steps, read [workflows.md](references/workflows.md).
- For PostgreSQL/Redis/testcontainers, auth/API-key, Svix, AWS, Celery, OpenAPI, pagination/date, and migration failures, read [troubleshooting.md](references/troubleshooting.md).
- When a checkout is available, run the safe static checker before or after backend edits: `python skills/disco/open-wearables/sub-skills/backend-core/scripts/check_backend_core.py --repo-root .`. Add `--import-openapi` only when backend dependencies and config are ready; it still avoids network and writes.

## Boundaries

This sub-skill owns generic backend/API behavior. Route provider-specific OAuth, provider factory registration, coverage constants, vendor workout parsing, provider webhook parsing, historical backfill internals, and provider-specific import normalization to [provider-integrations](../provider-integrations/SKILL.md). Route React portal pages, API hooks, query keys, runtime frontend config, and UI presentation to [frontend-portal](../frontend-portal/SKILL.md). Route FastMCP tools, assistant configs, and MCP REST-client behavior to [mcp-server](../mcp-server/SKILL.md).

When work crosses boundaries, keep the shared endpoint contract, auth, database schema, service/repository changes, migrations, and external API docs navigation here; ask the owning sibling sub-skill to handle provider internals or frontend/MCP callers.

## Non-negotiable backend rules

- Preserve the route hierarchy: module routers are prefix-free, the v1 router attaches prefixes/tags, the head router attaches the API version prefix, and `app.main` includes the head router.
- Do not use trailing slash route roots on prefixed routers. Use `""` for a prefixed router's root endpoint; `"/"` can create 307 redirects behind reverse proxies.
- Keep route handlers thin. Validate/parse request inputs, call services, and return Pydantic response models; do not call repositories directly from routes.
- Keep repositories database-only and model-only. Pydantic schemas and business decisions belong in services or route schemas, not repository methods.
- Use SQLAlchemy 2.0 `Mapped[...]` model fields and the existing `app.mappings` aliases for IDs, FKs, constrained strings, dates, decimals, JSON, and relationships.
- Use Pydantic v2 schema style with `ConfigDict(from_attributes=True)` for ORM reads and schema defaults for generated IDs/timestamps where appropriate.
- Protect public/external data APIs with `ApiKeyDep` unless the route is intentionally token/SDK/OAuth/system-specific; protect dashboard/admin routes with `DeveloperDep`.
- If you add, remove, rename, or retag an endpoint tagged `External: *`, update the API Reference navigation in `docs/docs.json` in the same change.
- Treat credentials as secrets. Never log API keys, JWTs, application secrets, provider OAuth tokens, Svix tokens, AWS keys, or master encryption material.
- Run focused backend quality checks after changes when dependencies are available: targeted `pytest`, `ruff check`, `ruff format --check` or format, and `ty check` for type-impacting work.

## Fast start for future agents

1. Classify the task as route/API contract, data-service/model, background/sync/webhook, migration/config, test failure, or troubleshooting.
2. Read the nearest reference in this sub-skill; avoid reopening source files unless you are implementing or verifying drift.
3. For endpoint changes, update the route module, schemas, service, repository/model/migration if needed, route registration/tags, tests, and external API docs navigation together.
4. For data ingestion or sync changes, verify the affected data-source identity, event/timeseries upsert semantics, sync-status events, and outgoing webhook side effects.
5. Prefer the smallest safe test set first, then expand to the native candidate files listed in [workflows.md](references/workflows.md) when the change scope requires it.
