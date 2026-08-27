# API and Migrations

This reference covers backend route shape, error handling, DB helper placement, migrations, and OpenAPI notes.

## New API rules

- Type the return value of new FastAPI routes.
- Do not add `response_model` on new endpoints.
- Validate request bodies with Pydantic models at the FastAPI boundary.
- Raise `OnyxError` for new user-facing API failures instead of introducing new direct `HTTPException` use.
- Use an error code plus optional detail for normal failures, and use a status override only when you are forwarding an upstream status.
- Prefer auth dependencies over in-handler role checks.
- Verify user, tenant, or workspace ownership before returning ID-based resources to avoid IDOR.

## Where database logic belongs

- Put all database work in the backend DB helper layer.
- Keep route handlers thin: validate, authorize, call a DB helper, and return the typed result.
- Use tenant-aware session helpers for tenant data and public-schema helpers for shared bootstrap data.
- Keep raw SQL rare, parameterized, and isolated when it is unavoidable.
- Do not scatter ad hoc queries through route handlers, background workers, or utility modules.

## Migrations

Run Alembic from the backend area with `uv` and the backend-only group flags.

| Task | Command | Notes |
| --- | --- | --- |
| Upgrade the default schema | `uv run --frozen --no-default-groups --group backend alembic upgrade head` | Standard migration path. |
| Upgrade the private schema | `uv run --frozen --no-default-groups --group backend alembic -n schema_private upgrade head` | Multi-tenant / enterprise schema path. |
| Create a migration | `uv run --frozen --no-default-groups --group backend alembic revision -m "description"` | Edit the generated file manually. |
| Create a private-schema migration | `uv run --frozen --no-default-groups --group backend alembic -n schema_private revision -m "description"` | Same manual-edit rule applies. |

- Treat generated migration stubs as starting points, not finished code.
- Keep migrations deterministic and review the SQL before shipping.

## OpenAPI and generated artifacts

- The app builder sets operation IDs from route function names after routes are loaded.
- Keep route function names stable when downstream client generation depends on them.
- Use the bundled route inventory helper before schema refresh when you want to sanity-check the surface.
- For a fresh OpenAPI schema, build the app from the assembled route surface, write the schema JSON, optionally strip tags for client generation, and then regenerate the client from that JSON.
- Schema export and generated client refresh are project workflows, so keep regenerated artifacts in the repo-owned generated output area rather than inside this skill subtree.

## Error pattern

- Prefer concise, typed API errors.
- Example shape: raise `OnyxError(error_code, detail)` with an optional status override when forwarding an upstream response.
