---
name: backend-platform
description: "Onyx backend platform guidance for FastAPI routes, auth/RBAC,
  SQLAlchemy, Alembic, Celery, file store, tracing, and backend tests."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Backend Platform

Use this sub-skill when you are editing or reasoning about the Python backend surface: FastAPI app wiring, auth/RBAC, SQLAlchemy data access, migrations, Celery workers, file store settings, tracing, or backend test selection.

Stay inside this scope. Route connector and indexing implementation to `rag-indexing-connectors`, chat/Craft/MCP/tool orchestration to `agents-craft-and-tools`, and web, mobile, or CLI work to the sibling client skills.

Read [references/backend-architecture.md](references/backend-architecture.md) when you need app startup, middleware order, tenant/session boundaries, settings, tracing, or file store behavior.

Read [references/api-and-migrations.md](references/api-and-migrations.md) when you are adding or changing API routes, DB helper placement, error handling, migrations, or OpenAPI generation.

Read [references/celery-and-background-jobs.md](references/celery-and-background-jobs.md) when you are touching Celery workers, queues, beat schedules, task expirations, or tenant propagation.

Read [references/testing.md](references/testing.md) when you are choosing unit, external-dependency, integration, or Playwright coverage, or when you need secrets and logs guidance.

Read [references/troubleshooting.md](references/troubleshooting.md) when imports, environments, services, auth, database access, or file store setup is unclear.

Run [scripts/list_api_routes.py](scripts/list_api_routes.py) with `uv run --frozen --no-default-groups --group backend` and `--repo-root` when you need a read-only inventory of the current FastAPI route surface.
