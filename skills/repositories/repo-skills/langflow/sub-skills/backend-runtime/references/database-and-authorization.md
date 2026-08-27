# Database, Migrations, and Authorization

This reference covers Langflow's guarded-route pattern, authorization request shape, share-aware fetch behavior, database session rules, migration safety, and focused verification.

## Authorization Model

Langflow separates authentication from authorization:

- Authentication identifies the current user through session cookies, API keys, or route-specific helpers.
- Authorization is controlled by `LANGFLOW_AUTHZ_ENABLED` and a registered authorization service plugin.
- The OSS authorization service is pass-through/no-op when no real plugin is registered; route guards still exist and audit calls can still be wired.
- Resource owners get an owner-override allow in the guard helpers before plugin enforcement.
- Superuser behavior is handled by caller context and route-specific floors; do not assume every route can skip explicit checks for superusers.

The enforcement request shape is:

```text
subject: user:{uuid}
domain:  project:{uuid} -> workspace:{uuid} -> *
object:  flow:{uuid}, deployment:{uuid}, project:{uuid}, file:{uuid}, share:{uuid}, or resource:*
action:  read, write, create, delete, execute, deploy, or share-specific actions
```

The Python guard call takes the authenticated user object plus resource-specific ids and owner ids. For a flow execute route:

```python
await ensure_flow_permission(
    current_user,
    FlowAction.EXECUTE,
    flow_id=flow.id,
    flow_user_id=flow.user_id,
    workspace_id=flow.workspace_id,
    folder_id=flow.folder_id,
)
```

The guard resolves the domain from the most specific scope available: project/folder first, then workspace, then `*`.

## Guard Helpers

Use the typed guard matching the resource:

- `ensure_flow_permission(user, FlowAction.*, flow_id=..., flow_user_id=..., workspace_id=..., folder_id=...)`
- `ensure_deployment_permission(user, DeploymentAction.*, deployment_id=..., deployment_user_id=..., workspace_id=..., project_id=...)`
- `ensure_project_permission(user, ProjectAction.*, project_id=..., project_user_id=..., workspace_id=...)`
- `ensure_knowledge_base_permission(user, KnowledgeBaseAction.*, kb_id=..., kb_user_id=..., kb_name=..., workspace_id=..., project_id=...)`
- `ensure_variable_permission(user, VariableAction.*, variable_id=..., variable_user_id=..., workspace_id=...)`
- `ensure_file_permission(user, FileAction.*, file_id=..., file_user_id=..., workspace_id=...)`
- `ensure_share_permission(user, ShareAction.*, share_id=..., share_user_id=...)`

Guard behavior:

- If `AUTHZ_ENABLED` is false, `ensure_permission` returns without plugin enforcement.
- If the current user owns the resource, the typed guard records an owner-override audit decision and returns.
- If plugin `enforce()` raises, the route fails closed with `403` and records a deny audit decision.
- Default deny details are intentionally generic (`Permission denied`) to avoid UUID leakage.
- Richer details are opt-in only after the caller has already established the requester may know about the resource.

## Share-Aware Fetch Pattern

Default resource fetches should be owner-scoped. Cross-user loading is allowed only for routes that immediately enforce a permission decision.

Use this pattern for a guarded flow route that supports plugin-granted shared access:

1. Resolve the current user from auth.
2. Load by owner scope in OSS/default mode.
3. If and only if both `supports_cross_user_fetch()` and `is_enabled()` are true, allow the query to load by id without owner scoping.
4. Immediately call the matching `ensure_*_permission(...)` before returning data, streaming events, or executing actions.
5. For routes that preserve UUID privacy, convert a plugin deny from `403` to `404` with a deny-to-404 pattern.

Do not widen a fetch for code that reads `flow.data`, project config, files, variables, or event streams before a guard has run.

### Guarded Route Example

```python
flow = await get_flow_by_id_or_endpoint_name(flow_id_or_name, current_user.id, widen_for_shares=True)
await ensure_flow_permission(
    current_user,
    FlowAction.READ,
    flow_id=flow.id,
    flow_user_id=flow.user_id,
    workspace_id=flow.workspace_id,
    folder_id=flow.folder_id,
)
return flow
```

This is safe only because the fetch and guard are adjacent. If a helper returns graph data or event subscriptions before the guard, keep the fetch owner-scoped.

## Share CRUD Floor

Share administration has a special OSS floor:

- In OSS/pass-through mode, only the resource owner or a superuser may create, update, or delete share rows for a resource.
- When a real authorization plugin is active and supports cross-user fetch, the OSS floor is skipped and `ensure_share_permission` becomes authoritative.
- For plugin mode, pass the resource owner as `share_user_id` when checking share administration. Passing the share row creator can accidentally trigger owner override and bypass plugin policy.
- Missing resources return `404` to preserve UUID privacy.
- Non-owner attempts blocked by the OSS floor return `403` before any database write.
- USER-scope share invalidation targets that user; PUBLIC, TEAM, and PRIVATE scope changes invalidate all cached policy.

Focused verification: `uv run pytest src/backend/tests/unit/api/v1/test_authz_share_routes.py -q`.

## Database Session Rules

Langflow database access is async and SQLModel-based.

- Use `session_scope()` for transactional work; it delegates to the service-managed session scope.
- Use SQLModel's async session methods such as `session.exec(select(...))`, `session.get(...)`, `session.add(...)`, `session.flush()`, `session.commit()`, and `session.rollback()` according to route/test patterns.
- Do not use the deprecated `get_session()` helper; it intentionally raises.
- `NoopSession` exists for no-database/stateless modes and returns empty/no-op results. Code that requires persistence must fail clearly or avoid claiming persistence when no-op DB is enabled.
- For route tests, a small fake async session can be enough when testing route guard/floor logic without a real database.

When a route writes data:

1. Validate current user and resource ownership/permission before mutation.
2. Add or modify the model object.
3. `flush()` when an id/default must be visible before response construction.
4. `refresh()` when the response depends on database-populated fields.
5. Roll back on caught write exceptions before re-raising an HTTP error.
6. Invalidate authz/cache state after share or role mutations.

## Database Service Behavior

The database service owns engine creation, connection diagnostics, schema setup, and migrations.

Important runtime behavior:

- `sqlite://` URLs are normalized to `sqlite+aiosqlite://`.
- `postgres://` is accepted with a warning and normalized to PostgreSQL driver usage.
- PostgreSQL connections set timezone to UTC.
- PostgreSQL must be major version 15 or newer because Langflow schema relies on features not supported by older versions.
- SQLite database URLs should point to an existing parent directory; SQLite does not create intermediate directories.
- Relative SQLite paths are resolved by SQLAlchemy against the current working directory. Prefer absolute SQLite URLs in operational configs.
- `LANGFLOW_MIGRATION_LOCK_TIMEOUT_S` controls the bounded wait for PostgreSQL migration advisory locks.
- Alembic log output should not crash startup if the configured log path is unwritable; it falls back to stdout with a warning.
- Concurrent PostgreSQL schema creation and migration paths are serialized with the same advisory lock to avoid type/table races across workers.

## Migration Safety

Langflow migrations follow an expand/migrate/contract pattern for N-1 compatibility and zero-downtime deployments.

Use these phase rules:

- `EXPAND`: add nullable columns or columns with `server_default`; check existence before adding columns; do not drop columns.
- `MIGRATE`: backfill or transition data while both old and new schema paths remain compatible.
- `CONTRACT`: remove old columns only after application code has stopped using them and data migration is verified.

Every migration should include phase documentation such as `Phase: EXPAND`, an `upgrade()` function, and a safe `downgrade()` strategy or explicit non-rollback stance for contract phases.

Avoid these anti-patterns:

- Adding non-nullable columns without a default.
- Direct column rename instead of add/backfill/switch/drop.
- Direct type alteration outside a contract-safe plan.
- Dropping columns outside a `CONTRACT` phase.
- Migration operations without existence checks.
- Downgrades that silently lose data.

## Migration Validator

Langflow includes a migration validator that statically checks Alembic files. It detects:

- Missing phase markers.
- Missing `upgrade()` or required `downgrade()` functions.
- Non-nullable added columns without defaults.
- Direct renames.
- Direct type changes in unsafe phases.
- Immediate drops outside contract phase.
- Missing existence checks.
- Contract phase drops without data-migration verification.
- Potentially unsafe downgrades.

Run it directly on new migration files when available:

```bash
uv run python -m langflow.alembic.migration_validator path/to/new_migration.py --strict
```

Or run the focused test for the validator contract:

```bash
uv run pytest src/backend/tests/unit/alembic/test_migration_validator.py -q
```

## Safe Backend Migration Workflow

1. Decide whether the change is schema-only, code-only, or a coordinated schema/code rollout.
2. For schema additions, create an `EXPAND` migration first.
3. Keep application code compatible with both old and new fields during transition.
4. Backfill data in a `MIGRATE` phase when needed.
5. Use a later `CONTRACT` phase to remove old schema only after verification.
6. Run the migration validator on the new file.
7. Run focused backend tests for the route/model using the changed schema.
8. Avoid `langflow migration --fix` against a valuable database unless backed up and explicitly approved.

## Route and Migration Native Candidates

These native candidates are good later verification anchors after the whole skill is integrated:

- Flow API behavior and path validation: `uv run pytest src/backend/tests/unit/api/v1/test_flows.py -q`.
- Share route floor and plugin behavior: `uv run pytest src/backend/tests/unit/api/v1/test_authz_share_routes.py -q`.
- Migration validator behavior: `uv run pytest src/backend/tests/unit/alembic/test_migration_validator.py -q`.

Do not run broad database or destructive migration checks on a non-disposable database. Prefer temporary SQLite or isolated PostgreSQL test databases for schema experiments.
