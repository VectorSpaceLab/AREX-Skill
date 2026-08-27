# Identity, Permissions, Tenancy, Gateway, and Cursor Workflows

## Auth and user identity workflow

BiSheng request identity starts from JWT, then loads user roles and tenant context:

```text
Cookie/Header/WebSocket token -> AuthJwt subject -> UserPayload/LoginUser -> roles/groups/tenant -> route/service authorization
```

Key areas:

- User auth services under `src/backend/bisheng/user/domain/services/`.
- `UserPayload` dependencies under `common/dependencies/`.
- Route-level dependencies in API endpoints.
- Frontend route/menu visibility consumes backend `web_menu` and plugin/menu-approval data.

## Permission workflow

Architecture law: PermissionService is the unified entry point for resource checks and writes. The effective short-circuit order is super admin, tenant mismatch deny, tenant admin, ReBAC/OpenFGA, then RBAC menu or legacy compatibility where still present.

Resource creation workflow:

1. Create the business row through the owning domain service.
2. Authorize the owner/relation through PermissionService.
3. If tuple writes fail, preserve retry/compensation rather than silently ignoring the missing grant.
4. Add focused tests for both authorized and denied users.

Resource read/list workflow:

- Prefer service-level authorization maps/batches instead of per-row ad hoc checks.
- For list performance, understand whether permission filtering happens before the DAO query, after the DAO query, or both.
- If cursor pagination is used, visible page fill may require a scan loop.

## Multi-tenant workflow

Tenant isolation is ContextVar-driven:

- HTTP middleware and WebSocket middleware set current tenant from JWT.
- Celery publish/prerun/postrun signals propagate tenant IDs through task headers.
- SQLAlchemy events inject tenant filters into ORM SELECTs and fill tenant IDs on INSERT.
- Storage prefixes are applied for MinIO, Milvus, Elasticsearch, and Redis for non-default tenants.

Rules:

- Do not manually add tenant filters to ordinary ORM SELECT code.
- Do explicitly design raw SQL and bulk update/delete, because ORM tenant events do not protect them.
- For cross-tenant scripts, use tenant bypass helpers and document why.

## Approval and admin-scope workflow

Approval and admin-scope features affect whether menus/resources are visible or actionable:

- Approval center code owns request/decision/outbox/notification behavior.
- Menu approval can replace normal route entries with a placeholder instead of exposing routes directly.
- Admin scope keys and tenant admin behavior affect cross-tenant visibility.

Route UI symptoms often originate in backend menu/plugin data; verify backend state before editing frontend route guards.

## Gateway and SSO workflow

Commercial deployments can insert a Java gateway before FastAPI:

- Gateway handles `/api/oauth2/*`, SSO/OAuth/LDAP callbacks, sensitive-word management, gateway-side group/resource administration, and rate/online limits.
- Gateway proxies `/api/v1/**`, `/api/v2/**`, and chat WebSockets to the backend.
- Gateway calls backend SSO sync endpoints and writes backend JWT cookies.
- Frontend dev mode can proxy to gateway (`:8180`) instead of bare FastAPI (`:7860`).

When debugging gateway behavior, distinguish backend route errors from gateway-only filters or proxy rewrites.

## Cursor pagination and permission performance workflow

Cursor interfaces use `PageInfiniteCursorData` and context-checked cursor tokens. DM8 compatibility requires expanded OR-ladder keyset predicates rather than row-value tuple comparison.

Fetch-until-enough pattern:

1. DAO fetches a batch using the current cursor.
2. Service applies fine-grained permission filtering.
3. Visible rows accumulate until `page_size + 1` or DB exhaustion.
4. Cursor advances by the last DB row fetched, not the last visible row.

Use this route for symptoms such as short pages, duplicate cursor rows, DM8 tuple syntax errors, stale `next_cursor`, and OpenFGA calls growing with page depth.

## Test selection

From `src/backend/`:

```bash
uv run pytest test/permission/test_permission_service.py -q
uv run pytest test/permission/test_permission_api_integration.py -q
uv run pytest test/tenant/test_tenant_context.py -q
uv run pytest test/tenant/test_tenant_filter.py -q
uv run pytest test/approval/test_approval_api.py -q
uv run pytest test/api/test_workflow_list_cursor.py -q
uv run pytest test/knowledge/test_knowledge_list_cursor.py -q
```

Use e2e tests under `test/e2e/` only when middleware, frontend-visible permission behavior, or integrated tenant flows changed and the required services are running.
