---
name: backend-runtime
description: "Work on Langflow FastAPI backend routes, graph execution,
  services, settings, auth/authz, database, migrations, storage, telemetry, and
  runtime errors."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Backend Runtime

Use this sub-skill for Langflow backend implementation tasks: FastAPI routes, API router wiring, flow execution internals, service dependencies, settings behavior, authorization guards, database sessions, Alembic migrations, storage boundaries, telemetry, and runtime error diagnosis.

Route elsewhere when the task is primarily:

- SDK or external client usage: use `../sdk-and-api-clients/`.
- Docker, cloud, or production deployment operations: use `../deployment-and-operations/`.
- Python component class authoring or bundles: use `../component-development/`.
- Local flow JSON authoring and validation without backend changes: use `../flow-authoring/`.

## Start Here

1. Classify the affected backend surface: route/API, flow execution, service/settings, authz, database/migration, storage, or telemetry.
2. Read [references/api-and-services.md](references/api-and-services.md) for router mounting, route dependency patterns, `simple_run_flow`, request parsing, tweaks, service access, and focused API validation.
3. Read [references/database-and-authorization.md](references/database-and-authorization.md) before changing guarded routes, share-aware fetches, database models, sessions, or Alembic migrations.
4. Use [references/troubleshooting.md](references/troubleshooting.md) when a backend run, CLI/API call, auth decision, database connection, migration, file upload, or optional dependency fails.
5. Inspect mounted routes with the bundled helper when route prefixes or hidden routes are unclear:

```bash
python scripts/inspect_routes.py --module langflow.api.router --router router --include-hidden
```

## Backend Change Checklist

- Keep route handlers explicit about authentication, authorization, response status, response models, and 403-vs-404 privacy behavior.
- Use `get_*_service()` helpers for managed services; avoid module-level settings reads for flags that may be supplied by `--env-file` or runtime environment variables.
- For flow execution endpoints, preserve JSON and multipart parsing behavior, `tweaks` semantics, telemetry logging, job-service execution, memory-base fire-and-forget behavior, and streaming error propagation.
- For authorization-aware fetches, widen cross-user loading only when an immediate `ensure_*_permission(...)` guard follows.
- For migrations, follow expand/migrate/contract safety and validate the specific migration before broad backend tests.

## Useful Validation Commands

Run the narrowest safe check that covers the change:

```bash
python -m py_compile skills/langflow/sub-skills/backend-runtime/scripts/inspect_routes.py
uv run pytest src/backend/tests/unit/api/v1/test_flows.py -q
uv run pytest src/backend/tests/unit/api/v1/test_authz_share_routes.py -q
uv run pytest src/backend/tests/unit/alembic/test_migration_validator.py -q
```

Use `uv run` for repository Python commands. Avoid credentialed provider tests, live external services, GPU/transformer execution, or destructive migration fixes unless the user explicitly asks and the environment is disposable or backed up.
