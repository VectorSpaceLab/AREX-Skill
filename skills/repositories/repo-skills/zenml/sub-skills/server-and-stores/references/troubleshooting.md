# Server and Store Troubleshooting

## Missing Server Extras

Symptoms: importing a router fails, `zenml server` or local server startup cannot import FastAPI/Uvicorn, or CLI help breaks after a server change.

- Confirm the code path really belongs in server code. If a client, CLI, integration, or shared model module imports `zenml.zen_server`, move the dependency behind a public model/client abstraction.
- Install or document the server optional extra only for server execution. Do not require server extras for base CLI import or pipeline authoring.
- Defer FastAPI, Uvicorn, Redis, OpenTelemetry, and SQL-only imports inside server-only functions when the containing module is also imported by client startup code.
- For streaming/live-event failures, distinguish missing Redis/server-streaming dependencies from ordinary REST endpoint failures.

## Wrong HTTP Status or Error Body

Symptoms: validation returns 500 instead of 422, a domain exception leaks an internal message, or FastAPI `HTTPException` is swallowed.

- Ensure endpoint functions are decorated with `@async_fastapi_endpoint_wrapper` unless they intentionally use a streaming or custom async handler.
- Use `Depends(make_dependable(FilterModel))` for filter/query models so Pydantic validation errors map to 422.
- Raise existing ZenML exception classes for domain failures and let the wrapper map them.
- Re-raise explicit `HTTPException` only for HTTP-specific failures.
- Check `responses={...: error_response}` entries for expected 401/403/404/409/422 documentation but do not rely on them for runtime translation.

## Auth and RBAC Failures

Symptoms: an endpoint works as admin but fails for ordinary users, list results are empty, create assigns the wrong user, or attach/detach operations bypass permissions.

- Add `_: AuthContext = Security(authorize)` to protected routes.
- Use `verify_permissions_and_*` helpers for CRUD rather than manually calling store methods.
- For project-scoped filters, ensure the list helper can set project scope before RBAC ID filtering.
- For user-scoped requests, let the create helper overwrite user ownership with the authenticated user.
- For non-CRUD actions, explicitly verify permissions on every touched resource. Trigger snapshot attach/detach and platform-event source validation are examples.
- Check feature gates before creating/updating gated resources such as schedules and resource pools.

## Import Boundary Violations

Symptoms: `zenml --help` fails after a server change, base package import pulls FastAPI, or tests catch forbidden `zen_server`/SQL imports.

- Shared request/response/filter contracts belong in shared models, not in router modules.
- Client-facing behavior must call `Client` or REST store methods, never server routers or server utility functions.
- Code outside stores should not import SQLModel schemas or `SqlZenStore`; use shared models or `Client().zen_store` for rare lower-level access.
- Integration packages should not import server/store internals for feature detection; keep optional SDK checks inside integration-specific components.

## Model and Schema Drift

Symptoms: response properties raise missing-field errors, filter options are accepted by CLI but fail in SQL, updates silently drop fields, or hydration differs between REST and SQL stores.

- Compare the request/update/response/filter model against the SQL schema fields, `from_request`, `update`, `to_model`, and query options.
- Check whether a field belongs in body, metadata, or resources; hydrate-only relationships must be loaded in `get_query_options` and exposed via metadata/resources.
- Update REST and SQL store implementations together, including response model validation and filter serialization.
- For filter fields, update client method signatures and CLI/list wrappers through `../cli-and-client/SKILL.md`.
- Add tests for both non-hydrated and hydrated responses when metadata/resources changed.

## Migration Branch Conflicts

Symptoms: Alembic reports multiple heads, branch output is non-empty, or CI migration consistency fails after rebasing.

- Run `python sub-skills/server-and-stores/scripts/check_migration_branches.py` from a ZenML checkout or copy of this skill tree.
- If multiple heads exist, inspect the concurrent revisions and create a merge revision or rebase the migration chain according to maintainer policy.
- Do not edit old migration files already present on the primary development branch.
- Re-run the branch check after resolving the heads.
- For schema changes, also run a populated-database upgrade test when safe; the branch check only detects divergent revision graph heads.

## Trigger or Resource-Pool Layer Missed

Symptoms: trigger lists work but latest run is missing, resource pools create but scheduling ignores them, or a new field appears in one API response but not another.

- Trace the full layer map: models, registry mappings, schemas, associations, store interfaces, SQL store, REST store, routers, Client/CLI, tests, and docs.
- For triggers, verify type/flavor unions, extra-field serialization, denormalized filter columns, snapshot links, trigger execution rows, dispatch state, and latest-run query behavior.
- For resource pools, verify pool capacity validation, resource rows, queue/allocation/policy relationships, request status transitions, release cleanup, and feature gates.
- Use targeted CRUD and functional tests around trigger attach/execution/filtering and resource-pool queue/allocation behavior before broader checks.

## Rolling Deployment Breakage

Symptoms: old workers fail after server upgrade, new clients fail against old server responses, or migrations succeed but running services write incompatible payloads.

- Make database changes additive first; add nullable/defaulted columns before requiring them in request or response models.
- Keep enum values and serialized config keys stable where possible.
- Avoid removing response fields or changing REST path semantics without a compatibility plan.
- Ensure migrations backfill required data and tolerate existing rows from older versions.
- Coordinate server, client, and worker rollout order in release notes or upgrade guidance when a compatibility bridge is impossible.
