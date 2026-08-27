# Backend Core Troubleshooting

## Import or setup failures

### `uv sync --frozen` fails

Check:
- You are in `src/backend/`.
- Python is compatible with the lockfile and `requires-python >=3.11`.
- Network/proxy access is available for dependencies.

If the failure is specifically editable package metadata validating `project.license = "Apache 2.0"`, use the repository-supported `uv sync --frozen` path rather than a raw modern `pip install -e` for development. For read-only inspection, use `PYTHONPATH=./` from `src/backend`.

### Module import fails in a script

Symptoms:
- `ModuleNotFoundError: bisheng` when running `python scripts/foo.py`.

Fix:
- Run from `src/backend/` with `PYTHONPATH=./`, or use a shell wrapper that sets it.
- For generated skill helpers, pass `--repo-root` and let the helper scan files rather than importing application modules.

## API and router failures

### Route returns 404 after adding a module

Likely causes:
- Module router was created but not included in `bisheng/api/router.py`.
- Endpoint router prefix duplicated or missing.
- Frontend is calling the commercial gateway or Client `/workspace/api` path while backend route is bare `/api/v1`.

Recovery:
- Inspect `api/router.py` for `router.include_router(...)`.
- Confirm whether the route belongs under `/api/v1`, `/api/v2`, or a special prefix such as `/api/department-limit`.
- Use frontend request wrappers for caller changes.

### Response envelope is inconsistent

Symptoms:
- Frontend receives nested `{status_code, data}` unexpectedly or raw Pydantic data without envelope.

Recovery:
- Use `resp_200` for success.
- Use `BaseErrorCode` subclasses for branchable business failures.
- Let unexpected exceptions propagate through app exception handlers after logging if needed.
- Do not add component-level frontend parsing workarounds for a backend envelope bug.

## DDD and architecture guard failures

### Endpoint imports `database.models`

Fix:
- Move data access behind a service/repository/DAO call.
- If legacy code already violates the rule, do not expand the violation for new code.

### `common/`, `core/`, or `database/models/` imports domain services

Fix:
- Invert dependency through a service call from the domain layer.
- Shared constants and protocol types can live in `common/` only if they are not tied to a domain service.

### Permission checks query role-access tables directly

Fix:
- Route to `identity-permissions-tenancy` and use PermissionService/OpenFGA-aware services.

## Settings and context failures

### Config value appears stale

Likely cause:
- DB config is cached in Redis for roughly 100 seconds.

Recovery:
- Confirm whether the value comes from YAML, `BS_*` env, DB config, or cache.
- Avoid service restarts or code changes until the cache window is ruled out.

### Script can read DB but fails on Redis/OpenFGA/Milvus/ES

Likely cause:
- Bare scripts do not initialize the full application context.

Recovery:
- Initialize `initialize_app_context(config=settings)` and close it in `finally` for scripts that touch non-DB infrastructure.
- Database-only scripts may use `get_async_db_session()` or `get_sync_db_session()` directly.

## Data model and SQL failures

### DM8 rejects syntax that works in MySQL

Common causes:
- MySQL-only JSON functions.
- Row-value tuple comparison in keyset pagination.
- MySQL-specific timestamp defaults.

Recovery:
- Use dialect helpers and the keyset helper.
- For cursor permission lists, route to `identity-permissions-tenancy`.

### Tenant data leak or missing rows

Likely causes:
- Raw SQL or bulk update/delete bypassed tenant ContextVar injection.
- Script ran without tenant context.

Recovery:
- Use ORM SELECTs where possible.
- For maintenance scripts, consciously use tenant bypass helpers for cross-tenant reads.
- Never blanket-add `WHERE tenant_id` to ordinary ORM code without checking multi-tenant rules.

## Logging failures

### Loguru raises from inside logging

Likely cause:
- Passing `exc_info=` to loguru or using `%s` placeholders that loguru does not interpolate.

Recovery:
- Use `logger.exception("message")` for errors with traceback.
- Use `logger.opt(exception=True).warning(...)` for warning-level tracebacks.
- Use `{}` placeholders with separate arguments or f-strings.
- Run `uv run pytest test/common/test_loguru_exc_info_guard.py -q` after fixes.
