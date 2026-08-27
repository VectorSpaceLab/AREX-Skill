# Backend API Routes

This reference distills the current FastAPI API surface and the rules for changing it. It is self-contained for route planning; use the source checkout only when making or verifying edits.

## Router hierarchy and tagging

- `app.main` creates the `FastAPI` app, installs CORS/access-log middleware, mounts static provider icons when present, registers exception handlers, configures raw payload storage, creates the Celery app, initializes Sentry, and includes the API head router.
- The head router includes v1 with the configured API prefix, currently `/api/v1`.
- Each route module defines `router = APIRouter()` without its own version prefix.
- The v1 router includes route modules with the public/internal/system tags and any module prefix. Tags drive OpenAPI grouping and the public API docs navigation rule.
- Use empty-string route paths (`""`) for a prefixed router's root endpoint. Do not add `"/"` as a prefixed-router root because FastAPI will canonicalize a trailing slash and can cause 307 redirects behind HTTPS reverse proxies.

## Authentication dependencies

| Dependency | Accepted credential | Typical route families | Notes |
| --- | --- | --- | --- |
| `DeveloperDep` | Developer JWT bearer token from `POST /api/v1/auth/login` | dashboard/admin, internal config, API-key/application management, seed/archival/priorities | Rejects SDK-scoped tokens. Use for portal-only or administrative mutations. |
| `DeveloperOptionalDep` | Developer JWT if present, otherwise `None` | SDK token creation fallback paths | Allows routes to combine developer-token and API-key behavior. |
| `ApiKeyDep` | Developer JWT or `X-Open-Wearables-API-Key` | external data APIs, users, connections, summaries, events, timeseries, sync, outgoing webhook management | Returns the developer id or API-key id string. Do not expose raw API keys in logs. |
| `SDKAuthDep` | SDK-scoped bearer token or `X-Open-Wearables-API-Key` | mobile SDK upload/log endpoints | Produces an SDK auth context with token/API-key source metadata. |

## Current route families

Installed OpenAPI inspection found 96 paths. The route groups below are the practical map future agents need for backend changes.

### External API endpoints

| Family | Paths | Auth | Backend ownership notes |
| --- | --- | --- | --- |
| Users | `GET/POST /api/v1/users`; `GET/PATCH/DELETE /api/v1/users/{user_id}` | list/get/create via `ApiKeyDep`; patch/delete via `DeveloperDep` | `GET /users` returns `OldPaginatedResponse[UserRead]` with page/limit/search/sort filters. `external_user_id` is deprecated and only works as a list filter; downstream data endpoints require the OW UUID. |
| Connections | `GET /api/v1/users/{user_id}/connections`; `DELETE /api/v1/users/{user_id}/connections/{provider}`; `DELETE /api/v1/users/{user_id}/connections/{provider}/data` | `ApiKeyDep` | List enriches connections with provider capability metadata, `live_sync_mode`, icons, max historical days, and linked-account user ids. Disconnect/purge delegates revocation to the provider OAuth component; provider implementation belongs in [provider-integrations](../../provider-integrations/SKILL.md). |
| Summaries | `GET /api/v1/users/{user_id}/summaries/activity`; `/sleep`; `/recovery`; `/body`; `/data` | `ApiKeyDep` | Activity/sleep/recovery are cursor-paginated. Body returns `null` when no data exists. Data summary counts series/events by provider and optional date window. |
| Timeseries | `GET /api/v1/users/{user_id}/timeseries` | `ApiKeyDep` | Required `start_time`, `end_time`; repeated `types` query values; `resolution` accepts `raw`, `1min`, `5min`, `15min`, `1hour`, though current service returns raw samples; keyset cursor pagination. |
| Events | `GET /api/v1/users/{user_id}/events/workouts`; `/events/sleep`; `/events/menstrual-cycles`; delete individual records under those families | `ApiKeyDep` | Event responses come from unified `EventRecord` plus category-specific detail tables. Sleep list supports `filter_by_priority`. Deletes return 204 or 404. |
| Health scores | `GET /api/v1/users/{user_id}/health-scores` | `ApiKeyDep` | Supports optional start/end, category, provider, limit, offset filters. Health-score model stores score category/value/components and optional linked sleep record. |
| Data sources | `GET /api/v1/users/{user_id}/data-sources` | `ApiKeyDep` | Exposes normalized user/provider/device/source identities and priority information. |
| Provider discovery/OAuth shells | `GET /api/v1/oauth/providers`; `GET /api/v1/oauth/{provider}/authorize`; system callback/success/error routes | external/provider routes plus system callback | Generic route shell lives here; provider strategy internals and OAuth template behavior belong in [provider-integrations](../../provider-integrations/SKILL.md). |
| Data sync | `POST /api/v1/providers/{provider}/users/{user_id}/sync`; `POST /api/v1/providers/{provider}/users/{user_id}/sync/historical`; Garmin backfill status/cancel/retry paths | `ApiKeyDep` | Async mode rejects provider-specific parameters that the Celery task would ignore. Historical dispatch calls the provider strategy. Provider-specific sync/backfill internals route to [provider-integrations](../../provider-integrations/SKILL.md). |
| Sync status | `GET /api/v1/users/{user_id}/sync/stream`; `/sync/recent`; `/sync/runs`; `GET /api/v1/sync/runs` | `ApiKeyDep` | User-specific endpoints 404 if the user does not exist. Stream emits `event: sync.status` SSE messages plus heartbeat comments. History is Redis-backed. |
| Token refresh/revoke | `POST /api/v1/token/refresh`; `POST /api/v1/token/revoke` | refresh-token payload | Handles both developer and SDK refresh tokens with rotation. Revoke returns 204, not a body. |
| Mobile SDK | `POST /api/v1/sdk/users/{user_id}/sync`; `/logs`; `POST /api/v1/users/{user_id}/token`; `POST /api/v1/users/{user_id}/invitation-code`; `POST /api/v1/invitation-code/redeem` | SDK routes use `SDKAuthDep`; token/invitation routes are mixed developer or public redeem | Backend auth/token semantics live here. Mobile SDK payload internals may also involve provider-integrations when data normalization changes. |
| Meta | `GET /api/v1/meta/coverage` | public external metadata | Provider coverage truth is generated from provider strategy/coverage declarations and belongs primarily in [provider-integrations](../../provider-integrations/SKILL.md). Backend-core owns only the metadata route contract: response shape, auth/public exposure, tags/OpenAPI, and docs navigation if that contract changes. |
| Apple XML import | `POST /api/v1/users/{user_id}/import/apple/xml/s3`; `/direct`; `POST /api/v1/sns/notification` | API key for user import; SNS route is system | AWS/S3/SNS config and raw payload storage troubleshooting belong here; Apple parser/provider details route to [provider-integrations](../../provider-integrations/SKILL.md). |
| Outgoing webhooks | Endpoint CRUD, endpoint secret, event types, messages, attempts, test event under `/api/v1/webhooks/...` | `ApiKeyDep` through Svix app dependency | Requires outgoing webhooks enabled and Svix configured. Event emission helpers are service internals described in [data-model-and-services.md](data-model-and-services.md). |

### Internal/dashboard endpoints

| Family | Paths | Auth | Notes |
| --- | --- | --- | --- |
| Auth | `POST /api/v1/auth/login`; `/logout`; `/change-password`; `GET/PATCH /auth/me` | login uses form credentials; others use `DeveloperDep` | Login uses OAuth2 password form username=email, bcrypt password verification, JWT access token, and developer refresh token. Validation errors on `/auth/login` are normalized to `401 Incorrect email or password`. |
| Developers/invitations | `GET/PATCH/DELETE /api/v1/developers/{developer_id}`; invitation create/list/revoke/resend/accept | developer JWT except invitation accept | Developer service hashes password updates; invitation service handles invite workflow and Resend email config. |
| API keys | `GET/POST /api/v1/developer/api-keys`; `DELETE/PATCH /developer/api-keys/{key_id}`; `POST /rotate` | `DeveloperDep` | API keys are stored as the actual `sk-...` primary key; creation/rotation returns the key value. Treat as secret after display. |
| Applications | `GET/POST /api/v1/applications`; `DELETE /applications/{app_id}`; `POST /applications/{app_id}/rotate-secret` | `DeveloperDep` | Application ids have `app_` prefix; app secrets have `secret_` prefix and are bcrypt-hashed. Plain secret is returned only on create/rotate. |
| Dashboard/config | `GET /api/v1/dashboard/stats`; `GET /api/v1/config` | `DeveloperDep` | Dashboard data-point count is cache/estimate-friendly. Config currently exposes `outgoing_webhooks_enabled` as an additive feature flag. |
| Data lifecycle | `GET/PUT /api/v1/settings/archival`; `POST /settings/archival/run` | `DeveloperDep` | Archival settings are a singleton row. Manual run dispatches a Celery task. |
| Seed data | `POST /api/v1/settings/seed`; `GET /settings/seed/presets`; `/sleep-profiles` | `DeveloperDep` | POST dispatches a Celery task and immediately returns `task_id`, `status`, and `seed_used`. |
| Priorities | provider and device-type priority GET/PUT/bulk endpoints under `/api/v1/priorities/...` | `DeveloperDep` | Used by summaries/data-source selection to prefer high-priority providers/devices. |

### System/provider webhook endpoints

System webhooks are provider callback surfaces. The generic shell lives under `/api/v1/providers/{provider}/webhooks`; deprecated Oura/Garmin/Strava compatibility paths still exist. Provider-specific verification, signature, subscription, and payload parsing belong in [provider-integrations](../../provider-integrations/SKILL.md). Do not retag system webhooks as external API docs unless the public API Reference intentionally exposes them.

## Response and query conventions

- Date query aliases use `DateTimeQueryParam` and `parse_query_datetime`; support ISO timestamps and date-like input consistently.
- Cursor-paginated health data uses `PaginatedResponse[data, pagination, metadata]` with `next_cursor`, `previous_cursor`, `has_more`, and sometimes `total_count`.
- Legacy user listing uses `OldPaginatedResponse[UserRead]` with `items`, `total`, `page`, `limit`, `pages`, `has_next`, `has_prev`.
- Timeseries and event list limits in route decorators are intentionally stricter than some schema defaults: timeseries route max 100; events route max 100; activity summaries max 400; message/attempt Svix pages max 250.
- Use `status.HTTP_201_CREATED` for creates, `202_ACCEPTED` for background task dispatch, and `204_NO_CONTENT` for destructive no-body operations.

## Endpoint-change checklist

1. Pick or create the route module closest to the resource. Keep the handler thin and delegate to a service.
2. Add Pydantic request/response schemas first. Use `from_attributes=True` on read schemas that return ORM models.
3. Add or update the service method. Repository methods should return ORM models or primitive query rows only.
4. If schema tables change, update SQLAlchemy models and create an Alembic migration; do not rely on `BaseDbModel.metadata.create_all` outside tests.
5. Register the route in the v1 router with the correct prefix and tag. External user-facing APIs should use a tag beginning `External: ...`; dashboard/admin routes use `Internal: ...`; provider callbacks use `System: ...`.
6. If the route is tagged `External: *`, update the `API Reference` tab in `docs/docs.json`: add/remove/rename the exact `METHOD /api/v1/...` page under the matching group. Keep guide pages separate from endpoint pages.
7. Update or add backend tests that exercise auth failures, validation, not-found behavior, successful payload shape, and service/repository side effects.
8. For frontend or MCP callers, coordinate with [frontend-portal](../../frontend-portal/SKILL.md) and [mcp-server](../../mcp-server/SKILL.md) after the backend contract is stable.
9. Run the static checker and focused backend tests from [workflows.md](workflows.md).

## OpenAPI drift notes

- Installed inspection currently reports duplicate operation-id warnings for several deprecated Oura webhook compatibility endpoints. Treat those as known drift unless you are changing those routes; if you touch them, prefer unique endpoint function names or explicit operation ids.
- The public docs navigation currently covers the external API groups: Authentication, Users, Connections, Providers, Data Sync, Summaries, Timeseries, Events, Health Scores, Data Sources, Meta, Apple Health Import, Mobile SDK, Webhooks, and Sync Status.
- Imported OpenAPI/docs comparison can currently flag existing navigation gaps for menstrual-cycle event endpoints, SDK logs, and the SNS notification endpoint. Treat those as known docs-nav drift unless your task touches those routes; for any new `External: *` route, do not add more drift.
- The safe checker can compare imported `External: *` OpenAPI paths against `docs/docs.json` with `--import-openapi` when the backend package can import.
