# Server API Reference

## Server Dependency Boundary

ZenML server code is optional for many client installations. Keep server-only imports inside the server package or local helper bodies that already protect optional dependencies.

- Code inside `zenml.zen_server` may import FastAPI, server utilities, RBAC helpers, and store internals.
- Code outside `zenml.zen_server` must not import routers, auth helpers, server config, or other server modules.
- Shared contracts belong in `zenml.models`, enums, constants, and public client/store abstractions, not in router modules.
- If client-side behavior needs a server capability, expose it through REST store methods and the Python `Client`, then route CLI work to `../cli-and-client/SKILL.md`.

## Optional Extras

Server work may require optional dependencies that are absent in a base client install.

- `zenml[server]` pulls in the local DB stack plus FastAPI, Uvicorn, multipart support, and FastAPI utilities.
- `zenml[server-streaming]` adds Redis support for live event streaming.
- OpenTelemetry server instrumentation lives behind the telemetry/server optional dependency set; do not make it mandatory for base imports.
- Keep imports for FastAPI, Uvicorn, Redis, server instrumentation, and SQL-only dependencies away from modules that import during CLI startup unless the existing code already defers them.

## Router Shape

A normal CRUD router follows this shape:

1. Create an `APIRouter` with an API/version prefix, tags, and shared `error_response` entries.
2. Use typed request, update, response, page, and filter models from `zenml.models`.
3. For list endpoints, depend on `make_dependable(FilterModel)` so query validation returns a 422 instead of an internal error.
4. Require authentication with `Security(authorize)` even when the returned value is unused.
5. Check entitlement or feature gates before mutations for gated features.
6. Use RBAC helper wrappers for CRUD when possible.
7. Call `zen_store()` for store operations.
8. Decorate endpoint functions with `@async_fastapi_endpoint_wrapper` so sync business logic runs through request management and errors are translated consistently.

## Auth, RBAC, and Feature Gates

Prefer the high-level RBAC helpers for standard entities:

- `verify_permissions_and_create_entity` sets user-scoped ownership to the authenticated user, checks create permissions, checks/report entitlements for reportable resources, calls the create store method, and dehydrates the response.
- `verify_permissions_and_list_entities` applies project scope for project-scoped filters, constrains IDs through RBAC, calls the list method, and dehydrates the page.
- `verify_permissions_and_get_entity`, `verify_permissions_and_update_entity`, and `verify_permissions_and_delete_entity` load the target, verify the action, call the store method, and dehydrate/delete resources consistently.
- Use `verify_permission_for_model`, `verify_permission`, or batch variants for non-CRUD actions that touch multiple resources, such as attaching a trigger to a snapshot.
- Call feature-gate checks such as schedule or resource-pool entitlements before operations that expose gated capabilities.

For source-linked requests, validate permission on every referenced resource, not only on the object being created. Platform-event triggers, for example, need update permission on the referenced pipeline, pipeline run, or snapshot before creation/update proceeds.

## HTTP Exceptions and Error Translation

Use existing error translation instead of hand-built catch-all responses.

- `async_fastapi_endpoint_wrapper` converts ordinary exceptions through the ZenML REST exception mapping, preserves explicit FastAPI `HTTPException`, and executes sync endpoint logic via request management.
- `handle_endpoint_errors` and its async variant are for endpoints that do not use the wrapper, such as streaming paths.
- Raise `HTTPException` only for expected HTTP-specific failures. For domain failures, raise the existing ZenML exception type so the wrapper can map it consistently.
- Keep user-facing error details safe: never include secret values, bearer tokens, database passwords, or full private connection URLs.

## Endpoint Add/Change Checklist

- Add or update the shared request/update/response/filter model first if the API contract changes.
- Add or update the store interface and REST/SQL store implementations before wiring the router.
- Add router dependencies with `Security(authorize)`, `Depends(make_dependable(...))`, RBAC helper calls, and feature-gate checks.
- Add the route to router registration if the router file is new.
- Add server tests for status codes, validation, auth/RBAC behavior, hydration defaults, and non-happy-path errors.
- If the endpoint is user-facing through CLI or `Client`, coordinate with `../cli-and-client/SKILL.md` so method signatures, CLI options, and docs stay aligned.

## Deployment and Operations Notes

- Production deployments should use an external MySQL-compatible database when scaling server replicas; embedded SQLite is appropriate only for local or evaluation deployments.
- Match server thread pool sizing with database pool and overflow settings so request workers do not block on database connections under load.
- Back up databases before server upgrades or schema migrations, and make secrets-store migrations deliberate when changing secret backends or locations.
- For Helm deployments, preserve chart compatibility expectations around the server configuration key, database settings, ingress/TLS, and persistent volume permissions.
- Server activation/initial admin setup happens before clients can authenticate; connection failures immediately after deploy may be initialization rather than API breakage.
