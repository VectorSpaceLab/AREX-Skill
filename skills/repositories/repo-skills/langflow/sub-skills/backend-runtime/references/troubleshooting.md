# Backend Runtime Troubleshooting

Use this reference to diagnose Langflow backend install/import problems, route failures, flow-run errors, settings surprises, auth/authz behavior, database/migration issues, storage/file validation, telemetry noise, and optional dependency boundaries.

## Install and Import Failures

Symptoms:

- `ModuleNotFoundError: No module named 'langflow'`
- `ModuleNotFoundError: No module named 'lfx'`
- `langflow --help` fails during import
- Backend starts in one shell but tests fail in another

Checks:

```bash
uv run python -c "import langflow, lfx; print('imports ok')"
uv run langflow --help
uv run python -m pip show langflow langflow-base lfx
```

Likely causes and fixes:

- The active environment does not have the workspace package installed. Run commands through `uv run` from the repository root or activate the environment where Langflow is installed.
- Dev-only test dependencies may be missing for subpackages. Sync the relevant dev group before running focused tests if imports such as test fakes or Redis fakes fail.
- The current CLI import path requires `openai`; install/runtime environments without it can fail before command handling.
- PyTorch/transformer execution is optional for this skill scope; do not treat missing torch as a backend-route failure unless the task explicitly targets model execution.
- Provider integrations may require optional packages and credentials. Keep backend route/service tests offline unless the test is marked and configured for credentials.

## CLI and Settings Surprises

Symptoms:

- A value in `.env` appears ignored.
- A feature route stays disabled after setting an env var.
- Boolean settings flip unexpectedly.
- A backend-only run still tries to serve frontend assets.

Rules:

- CLI flags override environment variables and `.env` values.
- Boolean CLI flags usually have positive and negative forms, for example `--remove-api-keys` and `--no-remove-api-keys`.
- `--env-file` values are loaded for the server run; additional CLI flags still win.
- Route modules can be imported before the env file is loaded, so request-time settings checks are safer than import-time environment reads for route gating.
- Use `--backend-only` for API-only development.

Diagnostic run:

```bash
uv run langflow run --backend-only --host localhost --port 7860 --log-level debug --env-file .env
```

If a feature flag is read at module import time, move the decision to the route handler or a dependency so the post-`--env-file` settings are visible.

## Route Not Found or Wrong Prefix

Symptoms:

- `404 Not Found` for a route that appears defined.
- OpenAPI does not show a route.
- A route works under `/api/v1` but not `/v1`.

Checks:

```bash
python scripts/inspect_routes.py --module langflow.api.router --router router --include-hidden
```

Likely causes:

- The exported API router is prefixed with `/api`, and v1/v2 routers add `/v1` or `/v2`.
- The route is hidden with `include_in_schema=False`; it may not appear in OpenAPI.
- A feature flag intentionally returns `404` to make a disabled route indistinguishable from an unmounted route.
- The wrong router object or app object is being inspected.

## Flow Run and Tweaks Failures

Symptoms:

- `tweaks` are ignored.
- A run request returns `400` for conflicting input.
- Streaming returns an `error` event instead of a normal response.
- API run succeeds but global variable defaults do not apply.

Checks:

- Confirm whether the request is `application/json` or `multipart/form-data`.
- For multipart, ensure `tweaks` is a string field containing valid JSON, not a file part.
- Confirm tweak keys match node ids or node display names.
- Confirm the target field is not a protected code execution field.
- Confirm the authenticated user is present; running flows requires auth for job ownership and global-variable defaults.
- Use `output_component` when selecting a precise output node; otherwise output selection depends on `output_type` and output vertex ids.

Common fixes:

- Send JSON tweaks as an object in JSON requests.
- Send multipart tweaks as one JSON string field: `-F 'tweaks={"NodeId":{"field":"value"}}'`.
- Do not pass both top-level chat/text `input_value` and a tweak setting the same ChatInput/TextInput `input_value`.
- For streaming diagnosis, inspect SSE events for `error` and server logs for the underlying exception.

## API Misuse and Validation Errors

Symptoms and expected statuses:

- Malformed bearer token: `401 Unauthorized`.
- Uploading a flow JSON array or scalar instead of object shape: `422 Unprocessable Entity`.
- Invalid endpoint names with unsupported characters such as dots: `422`.
- File-system path traversal, null bytes, or absolute paths outside allowed flow storage: `400`.
- Name or endpoint conflicts: `409 Conflict`.
- Attempting to update/delete deployed flows in forbidden ways: `409 Conflict`.
- Other-user flow access where existence must be private: `404 Not Found`.

When adding route validation, prefer explicit `HTTPException` status mapping over allowing Pydantic, SQLAlchemy, or domain errors to escape as generic `500` responses.

## Authorization and Share Failures

Symptoms:

- Owner can access a resource but delegated users cannot.
- A non-owner unexpectedly creates a share.
- A plugin-denied resource returns `403` where callers expect `404`.
- Share visibility differs between owner, creator, target user, public, team, and private scopes.

Checklist:

- Confirm `LANGFLOW_AUTHZ_ENABLED` and plugin registration state.
- Confirm the route uses owner-scoped fetch in OSS mode.
- If cross-user fetch is enabled, confirm the route immediately calls the matching `ensure_*_permission(...)` guard.
- Do not widen a fetch before reading sensitive data unless a guard runs first.
- For share create/update/delete, ensure OSS mode enforces the owner/superuser floor.
- In plugin mode, pass the resource owner into `ensure_share_permission`; do not pass the share creator as owner context.
- Convert plugin `403` denials to `404` where UUID privacy is required.
- Invalidate policy caches after share or role changes.

Focused check:

```bash
uv run pytest src/backend/tests/unit/api/v1/test_authz_share_routes.py -q
```

## Database Connection Failures

Symptoms:

- SQLite reports `unable to open database file`.
- PostgreSQL startup exits before serving.
- Database URLs behave differently in tests and server runs.
- No-op database mode drops persisted state.

Checks and fixes:

- For SQLite, ensure the parent directory exists; SQLite will not create intermediate directories.
- Prefer absolute SQLite URLs such as `sqlite:////absolute/path/to/langflow.db` for operational configs.
- Relative SQLite paths resolve against the current working directory at connection time.
- PostgreSQL must be version 15 or newer.
- `postgres://` is deprecated; prefer `postgresql://`.
- For PostgreSQL SSL or custom connection settings, verify the URL and driver-specific connection options are valid for SQLAlchemy.
- No-op database mode is for stateless execution; do not expect flow, user, key, job, or message persistence.

## Migration Failures

Symptoms:

- Startup hangs while multiple workers boot.
- Alembic reports schema/model mismatch.
- `langflow migration` warns about destructive changes.
- Migration validator flags a new file.

Checks:

```bash
uv run langflow migration
uv run python -m langflow.alembic.migration_validator path/to/migration.py --strict
uv run pytest src/backend/tests/unit/alembic/test_migration_validator.py -q
```

Guidance:

- Run `langflow migration` first to preview. Treat `langflow migration --fix` as destructive unless the database is disposable or backed up.
- If workers contend for PostgreSQL migrations, inspect the worker holding the migration advisory lock. Increase `LANGFLOW_MIGRATION_LOCK_TIMEOUT_S` only when a migration legitimately needs longer.
- Add nullable/defaulted columns in `EXPAND` phase; backfill in `MIGRATE`; drop or enforce non-null only in `CONTRACT` after verification.
- Add existence checks around Alembic operations for idempotency.
- Contract downgrades should explicitly raise or handle data-loss risk.

## Storage and Upload Failures

Symptoms:

- Flow create/update rejects `fs_path`.
- File upload returns `413`.
- File paths work on one OS but fail on another.

Checks and fixes:

- Use relative paths inside the allowed storage area for flow file paths.
- Reject absolute paths, parent traversal, null bytes, and Windows absolute paths outside the allowed directory.
- Upload size is capped by `max_file_size_upload` / `--max-file-size-upload` in megabytes.
- Avoid embedding machine-specific paths in persisted flow data or tests.

## Telemetry, Streaming, and Background Tasks

Symptoms:

- A run returns but telemetry logs later fail.
- Streaming clients receive no final event.
- Webhook execution returns accepted but no output is visible.

Checklist:

- Non-streaming run telemetry is scheduled as a background task after `simple_run_flow`.
- Streaming uses `text/event-stream`; client disconnect cancels the graph task.
- Stream event manager emits token/add-message/end/error events; inspect server logs for the original graph exception.
- Webhook execution starts a background asyncio task and returns `202 Accepted`; UI listeners receive progress only if webhook event subscribers are present.
- Memory-base output capture is fire-and-forget and should warn, not fail the user-facing run, on scheduling errors.

## Hardware, Network, and Credential Boundaries

Backend runtime route and service work should not require GPUs, transformer model execution, cloud services, or provider credentials unless the task explicitly targets that integration.

Safe defaults:

- Prefer offline route, schema, migration, and service tests.
- Skip credentialed provider calls unless the user supplied credentials and asked for live validation.
- Treat missing torch/transformers model execution as out of scope for backend route work.
- Do not run destructive migration fixes or cloud/network operations without explicit approval and a rollback plan.
