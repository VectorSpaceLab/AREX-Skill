---
name: server
description: "Operate on Observal FastAPI backend routes, data services, auth,
  migrations, jobs, insights, and route-focused tests."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# server

Use this sub-skill when a task touches the Observal FastAPI backend: REST or GraphQL route registration, PostgreSQL models and Pydantic schemas, service-layer behavior, auth/JWT/SSO/SCIM, registry and agent/component APIs, telemetry ingest storage, ClickHouse versus PostgreSQL migrations, dynamic settings, background jobs, insights, or route-focused tests.

Do not use this sub-skill for Typer CLI command hierarchy, frontend React/TanStack Router work, harness adapter/hook-spec/session-parser additions, or repo-wide release/compliance workflow except where they call into server APIs.

## Start here

1. Identify the backend surface:
   - New or changed REST route: read `references/server-architecture.md` and `references/api-data-workflows.md`.
   - SQLAlchemy model, Alembic, ClickHouse, dynamic settings, or arq jobs: read `references/migrations-and-settings.md`.
   - Auth, SSO, SCIM, route registration, ingest, insights, or failing backend tests: read `references/troubleshooting.md` first, then the focused reference above.
2. Verify the route graph before and after route registration changes with this sub-skill's bundled helper `scripts/check_server_routes.py`.
3. Keep changes in the server-owned layers: `observal-server/api`, `models`, `schemas`, `services`, `jobs`, `alembic/versions`, and `clickhouse/migrations`.
4. Add or update focused `tests/test_*routes*.py`, `tests/test_clickhouse_*.py`, `tests/test_migration*.py`, or `tests/test_insights*.py` coverage for the exact behavior.

## Hard boundaries

- Server owns FastAPI, data models, migrations, settings, jobs, auth/admin routes, insights, and the ingest endpoint.
- Harness telemetry owns harness registry/adapters/hook specs/session parsers/session delivery. Server work may use ingest and ClickHouse storage patterns, but harness-specific parsing or hook installation belongs there.
- CLI owns Typer commands and bundled CLI skills.
- Web owns Vite/React/TanStack Router and Playwright/e2e guidance.
- Repo-development owns contributor policy, global lint/test/release workflow, and change-review process.

## Non-negotiable backend invariants

- Register new top-level routers in `routes.py`; package routers such as `api.routes.agent` and `api.routes.admin` must import submodules so decorators attach to the shared router.
- Authenticated HTTP APIs use `Authorization: Bearer <token>` and dependencies from `api.deps`; do not add an `X-API-Key` bypass without confirming a deliberate auth design change.
- PostgreSQL schema changes require Alembic migrations. ClickHouse schema changes require SQL files in `observal-server/clickhouse/migrations/`. Do not add new ClickHouse DDL to startup code.
- Runtime-tunable settings go through `services.dynamic_settings`, not direct env-var reads. Boot-time infrastructure and crypto settings stay in `config.py`.
- Use Loguru (`from loguru import logger as optic`) with positional placeholders; never log secrets, JWTs, keys, or bearer tokens.
- Outbound network from server services must pass the existing SSRF guard patterns.
