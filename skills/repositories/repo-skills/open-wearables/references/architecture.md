# Architecture Map

## Purpose

Read this for cross-package orientation before changing data flow, provider behavior, portal callers, or MCP tools. Use the focused sub-skills for implementation details.

## Monorepo surfaces

| Surface | Role | Primary sub-skill |
| --- | --- | --- |
| Backend FastAPI app | Public/internal/system REST API, auth, developers/applications/API keys, users, connections, summaries/events/timeseries, sync orchestration, outgoing webhooks, seed/admin setup, migrations, raw payload storage | `backend-core` |
| Provider integrations | Strategy/factory/enum registration, OAuth, workout/event normalization, 24/7 data handlers, incoming provider webhooks, coverage declarations, provider sync/backfill behavior | `provider-integrations` |
| React portal | Developer/admin dashboard, user management/detail, provider connections/coverage, sync monitor, settings, outgoing webhooks, runtime API config, API hooks/query state | `frontend-portal` |
| MCP server | FastMCP tools and prompts for assistant access to backend REST data through API keys | `mcp-server` |
| Docs | Public quickstart, architecture, provider guides, API Reference navigation, MCP setup | root + owning sub-skill |

## Backend request flow

1. `app.main` creates the FastAPI app, configures logging, CORS, access logs, static provider icons, Celery, Sentry, raw payload storage, and exception handlers.
2. `app.api` includes the v1 router under the configured API version prefix.
3. Route modules validate input, apply dependencies such as `ApiKeyDep` or `DeveloperDep`, and call service-layer singletons.
4. Services hold business logic and use repositories for database access. Repositories stay database/model-only.
5. SQLAlchemy models define persistent entities; Pydantic schemas define route input/output and internal create/update shapes.
6. Background tasks use Celery/Redis for sync and webhook fan-out. Outgoing webhooks use Svix when enabled.

Keep route handlers thin. Do not move provider parsing or database decisions into frontend/MCP callers.

## Unified data model

Open Wearables normalizes heterogeneous provider payloads into:

- Users and personal records.
- User connections with provider tokens/status.
- External device mappings to associate user/device/provider sources.
- Event records plus detail tables for workouts, sleep, menstrual cycles, and other event-like data.
- `DataPointSeries` for time-series samples keyed by series type definitions.
- Health scores and summaries built from stored records/series.
- Developer, application, API-key, invitation, and webhook endpoint models for API access and delivery.

When a task introduces a new data type, check the backend data model, provider coverage declarations, series type seeding, API schema, frontend/MCP consumers, documentation, and native tests together.

## Provider delivery models

Provider strategies declare capability flags and wire optional components. Verified inventory at skill creation included 12 providers:

- SDK/file import: Apple Health, Samsung Health.
- Cloud REST pull: Google, Polar, Suunto, Whoop, Strava, Oura, Fitbit, Ultrahuman, SensorBio.
- Webhook stream: Garmin and Suunto send full payloads in webhook-style flows.
- Webhook ping/registration: Google, Polar, Whoop, Strava, Oura use notify or registration patterns.
- Garmin historical sync uses a webhook backfill style rather than ordinary pull.

Provider coverage powers `/api/v1/meta/coverage`, coverage docs, and the frontend coverage matrix. Route coverage changes to `provider-integrations` even when symptoms appear in backend OpenAPI or frontend UI.

## Frontend data flow

1. TanStack Router file routes define public, authenticated, settings, user-detail, pairing, sync, webhooks, and coverage pages.
2. Protected routes use auth/session state and route constants rather than ad hoc path strings.
3. API constants and service modules centralize backend paths and call the shared API client.
4. TanStack Query hooks define query keys, conditional fetching, mutation invalidation, and optimistic updates.
5. Runtime API base URL is resolved by `resolveApiUrl()` and `API_CONFIG.baseUrl`, allowing a prebuilt server-rendered frontend image to target different backend hosts.

When a backend endpoint changes, update endpoint constants, service functions, query keys/hooks, route/component usage, tests, and docs navigation consistently.

## MCP data flow

1. `app.main` creates a `FastMCP` server and mounts tool routers plus the presentation prompt router.
2. MCP tools call `OpenWearablesClient`, which builds REST requests to backend `/api/v1/...` endpoints with `X-Open-Wearables-API-Key`.
3. The client maps key backend errors: missing config, HTTP 401 authentication, HTTP 404 not found, and generic HTTP failures.
4. MCP tools should not import backend database models or access PostgreSQL/Redis directly.
5. Use mocked HTTP tests for MCP behavior. Live assistant calls require a real API URL and API key.

## Cross-skill change examples

| Task | Route |
| --- | --- |
| Add a provider and show it in coverage UI | Implement provider strategy/coverage in `provider-integrations`; verify backend coverage endpoint in `backend-core`; update portal coverage rendering in `frontend-portal` if the response shape changes. |
| Add a new user summary endpoint | Implement API/service/schema/tests in `backend-core`; update API Reference navigation; update frontend service/hook/page in `frontend-portal`; update MCP client/tool only if assistants need the new summary. |
| Diagnose MCP `Invalid API key` | Start in `mcp-server`; if the backend key issuance or auth dependency is wrong, route that part to `backend-core`. |
| Fix frontend wrong backend URL in production | Start in `frontend-portal`; keep backend service config separate unless the API host itself is misdeployed. |
| Change provider webhook verification | Start in `provider-integrations`; route generic webhook route security/logging to `backend-core`. |

## Documentation ownership

- External API endpoints tagged `External: *`: update API Reference navigation in docs metadata.
- Provider additions or coverage changes: update provider docs and coverage-generated content through `provider-integrations` guidance.
- MCP setup or tool changes: update MCP docs through `mcp-server` guidance.
- Frontend-only UI behavior: update relevant portal docs when a public feature or setup contract changes.
