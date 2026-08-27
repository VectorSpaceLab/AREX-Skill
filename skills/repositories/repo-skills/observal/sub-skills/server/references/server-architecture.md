# Observal server architecture

This reference distills backend source evidence into runtime guidance. Source-evidence labels are relative module or test names only; do not depend on the original docs or scripts being present.

## Evidence labels distilled

- Application assembly: `observal-server/app_factory.py`, `observal-server/startup.py`, `observal-server/routes.py`, `observal-server/middleware.py`, `observal-server/health.py`, `observal-server/worker.py`.
- Routes: `observal-server/api/routes/**`, especially `auth.py`, `ingest.py`, `insights.py`, `registry.py`, `component_versions.py`, `agent_versions.py`, `admin/**`, `agent/**`, `sso_saml.py`, `scim.py`.
- Data: `observal-server/models/**`, `schemas/**`, `services/**`, `jobs/**`.
- Storage migrations: `observal-server/alembic/versions/*.py`, `observal-server/clickhouse/migrations/*.sql`, `services/clickhouse/migrations.py`.
- Tests: `tests/test_*routes*.py`, `tests/test_clickhouse_*.py`, `tests/test_migration*.py`, `tests/test_insights*.py`.

## Application assembly

- `app_factory.create_app()` builds the FastAPI app, reads `observability.enable_openapi` through `services.dynamic_settings.get_sync_bool`, applies middleware, registers routes, and adds health/metrics.
- The FastAPI lifespan is `startup.lifespan`. Startup initializes PostgreSQL metadata/legacy column guards when DDL-on-startup is not skipped, initializes ClickHouse runtime settings, loads dynamic settings, imports legacy SSO env values once, initializes JWT keys, seeds demo accounts, registers audit handlers, and configures insights.
- `routes.configure_routes(app)` registers `/api/v1/graphql` with Strawberry and includes every router in `REST_ROUTERS`. The route module also registers the SAML health probe.
- `worker.WorkerSettings` registers arq jobs and cron jobs for component-source sync, alerts, ClickHouse maintenance, insights generation, retention, migration jobs, user-profile refresh, and inbox cleanup.

## Server package topology

| Area | Main modules | Runtime role |
| --- | --- | --- |
| FastAPI assembly | `app_factory.py`, `routes.py`, `startup.py`, `middleware.py`, `health.py` | App creation, startup/shutdown, route inclusion, health/metrics, middleware. |
| Dependencies | `api/deps.py`, `api/ratelimit.py`, `api/middleware/**` | DB session, bearer auth, role gates, visibility helpers, rate limiting, audit/request/content-type middleware. |
| Route handlers | `api/routes/**` | HTTP input validation, auth/permission gates, response models, DB transaction boundaries, service calls. |
| Models | `models/*.py`, `models/__init__.py` | SQLAlchemy ORM, PostgreSQL tables, enums, relationships, indexes. |
| Schemas | `schemas/*.py` | Pydantic request/response contracts. Use `model_config = {"from_attributes": True}` for ORM responses. |
| Services | `services/*.py`, `services/clickhouse/**`, `services/insights/**`, `services/audit/**` | Business logic, external IO, ClickHouse read/write helpers, insights generation, audit/security events, validators. |
| Jobs | `jobs/*.py`, `worker.py` | arq background work and cron scheduling. |
| Migrations | `alembic/versions/*.py`, `clickhouse/migrations/*.sql` | PostgreSQL and ClickHouse schema sources of truth. |

## Route graph and registration rules

`routes.REST_ROUTERS` currently registers 37 REST routers, plus GraphQL at `/api/v1/graphql`. Use the bundled route helper to confirm the count in the target checkout.

| Router/module | Prefix | Notes |
| --- | --- | --- |
| `api.routes.auth` | `/api/v1/auth` | Password login, OAuth/OIDC flow, bootstrap, token refresh/revocation, profile/password endpoints. |
| `api.routes.device_auth` | `/api/v1/auth/device` | Device authorization flow for CLI login. |
| `api.routes.jwks` | `/api/v1/auth` | JWKS publication for JWT public keys. |
| `api.routes.mcp` | `/api/v1/mcps` | MCP listing CRUD, install, validation, metrics; includes component version router. |
| `api.routes.skill` | `/api/v1/skills` | Skill listing CRUD/install; includes component version router. |
| `api.routes.hook` | `/api/v1/hooks` | Hook listing CRUD/install; includes component version router. |
| `api.routes.prompt` | `/api/v1/prompts` | Prompt listing CRUD/render; includes component version router. |
| `api.routes.sandbox` | `/api/v1/sandboxes` | Sandbox listing CRUD; includes component version router. |
| `api.routes.agent` package | `/api/v1/agents` | Agent CRUD, draft, install/pull, agent-scoped insights; package imports submodules into shared router. |
| `api.routes.preview` | `/api/v1/agents` | Agent preview-related endpoints sharing the agent prefix. |
| `api.routes.agent_versions` | relative to `/api/v1/agents` | Version list/get/create/review/harness/diff endpoints included into the agent router. |
| `api.routes.component_versions` | relative to component routers | Factory for `{listing_id}/versions` endpoints on mcps, skills, hooks, prompts, sandboxes. |
| `api.routes.registry` | `/api/v1/registry` | Canonical `namespace/slug` resolution, visibility changes, reconcile. |
| `api.routes.review` | `/api/v1/review` | Review queue approve/reject workflows. |
| `api.routes.component_source` | `/api/v1/component-sources` | Component source tracking and sync metadata. |
| `api.routes.bulk` | `/api/v1/bulk` | Mixed component bulk submission. |
| `api.routes.co_authors` | `/api/v1` | Shared co-author routes across registry item types. |
| `api.routes.feedback` | `/api/v1/feedback` | Ratings, comments, summaries. |
| `api.routes.config` | `/api/v1/config` | Public config, endpoints, SSO health, harness list, server version. |
| `api.routes.admin` package | `/api/v1/admin` | Diagnostics, settings, users, policy, migration, retention, insights model admin. |
| `api.routes.admin_sso` | `/api/v1/admin` | Admin SSO diagnostics/config surface. |
| `api.routes.logs_stream` | `/api/v1/admin/logs` | Admin log stream endpoints. |
| `api.routes.audit_log` | `/api/v1/admin/audit-log` | Admin audit-log query endpoints. |
| `api.routes.users` | `/api/v1/users` | User-facing user/profile APIs. |
| `api.routes.audit` | `/api/v1/audit` | Audit APIs outside the admin audit-log prefix. |
| `api.routes.sso_saml` | `/api/v1/sso/saml` | SAML login, ACS, metadata, logout, health probe internals. |
| `api.routes.scim` | `/api/v1/scim` | SCIM 2.0 provisioning with its own bearer-token verifier and SCIM JSON media type. |
| `api.routes.telemetry` | `/api/v1/telemetry` | Telemetry status/readiness for JSONL session ingestion. |
| `api.routes.ingest` | `/api/v1/ingest` | Authenticated session JSONL ingest and checkpoint APIs. |
| `api.routes.insights` | `/api/v1/insights` | Insights status, report generation, listing, HTML export, suggestions. |
| `api.routes.sessions` | `/api/v1/sessions` | Session list/detail style APIs backed by ClickHouse. |
| `api.routes.dashboard` | `/api/v1` | Dashboard summary endpoints. |
| `api.routes.layer_snapshot` | `/api/v1/layer-snapshots` | Harness config/layer snapshot storage and reads. |
| `api.routes.alert` | `/api/v1/alerts` | Alert rules and alert history. |
| `api.routes.support` | `/api/v1/support` | Diagnostic/support bundle endpoints. |
| `api.routes.teams` | `/api/v1/teams` | Teamspaces, membership, invites. |
| `api.routes.inbox` | `/api/v1/inbox` | Publication/review/user workflow inbox. |
| `api.routes.exec_dashboard` | `/api/v1/exec` | Executive dashboard APIs. |
| `api.routes.recommendations` | `/api/v1/recommendations` | Registry/user recommendation APIs. |

Registration patterns:

- New top-level single-file route: create `api/routes/<name>.py` with `router = APIRouter(prefix="/api/v1/...", tags=[...])`, import it in `routes.py`, and append to `REST_ROUTERS` in a deliberate order.
- New route under a route package: put it in `api/routes/agent/` or `api/routes/admin/`, import the module in that package's `__init__.py`, and attach decorators to the shared `._router.router`.
- New version behavior for existing component types usually belongs in `component_versions.py` or `agent_versions.py`, not duplicated in each component route.
- GraphQL is separate: `include_graphql_routes` mounts Strawberry at `/api/v1/graphql`; do not mix REST router inclusion with GraphQL registration.

## Models, schemas, services, and transactions

- ORM classes inherit `models.base.Base`. Add new model modules to `models/__init__.py` so Alembic metadata sees them.
- Request/response schemas live in `schemas/`. Use Pydantic validators for input normalization and `Field` constraints for public API bounds.
- Route handlers should be thin: parse/validate request, resolve auth/permissions, call services, manage transaction boundaries, and return schema-backed responses.
- Use `api.deps.get_db` for `AsyncSession`, `get_current_user` for any authenticated user, `optional_current_user` for public reads that become richer when authenticated, and `require_role(UserRole.<role>)` for role gates.
- For registry objects, use existing visibility and ownership helpers (`resolve_visible_listing`, `resolve_listing`, `get_effective_component_permission`, `get_effective_agent_permission`, `may_view_unapproved`, teamspace helpers) rather than inventing a new visibility query.
- Commit once per coherent mutation. On uniqueness conflicts, use the existing conflict handling patterns (`commit_or_name_conflict`, explicit `IntegrityError` rollback, or route-specific 409 detail).

## Auth, audit, and security invariants

- HTTP auth is Bearer-token based. `api.deps.get_current_user` rejects missing or invalid `Authorization: Bearer ...` headers, blocks deactivated users, and fails closed when Redis revocation checks are unavailable.
- `services.jwt_service` creates access and refresh JWTs. `services.crypto` signs/verifies with ES256 or RS256 and exposes JWKS. Keep JWT key material out of logs and responses.
- SSO is configured through dynamic settings and initialized at startup. OAuth/OIDC clients are built in `auth.configure_oauth_client`; SAML has route-level dynamic config and health probes.
- SCIM uses its own hashed bearer token model and constant-time token comparison; SCIM responses use SCIM JSON shapes rather than normal Pydantic response models.
- Privileged mutations should emit `services.security_events.SecurityEvent` where existing adjacent routes do. Audit middleware also records HTTP-level events to ClickHouse.
- Server logging uses Loguru as `optic` with positional placeholders: `optic.info("thing={} count={}", thing, count)`. Do not add f-string logs for runtime values, structlog-style keyword-only logs, or `exc_info=` with Loguru.
- For server-initiated outbound URLs, use the existing SSRF guard patterns before git clone, webhook, metadata, or MCP analysis calls.
