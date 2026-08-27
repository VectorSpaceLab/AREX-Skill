# API Hooks and State

## When to read

Read this when adding or changing frontend API access, TanStack Query hooks, query keys, runtime API URL handling, auth/session behavior, uploads, OAuth connection UI, sync-status streams, or mutation invalidation. Backend endpoint implementation details belong to `backend-core`; provider behavior and coverage truth belong to `provider-integrations`.

## Runtime API URL contract

The frontend has one public backend URL variable: `VITE_API_URL`.

`resolveApiUrl()` resolves the API base URL in this order:

1. Browser runtime config: `window.__APP_CONFIG__?.apiUrl`, injected before hydration by the root route.
2. SSR server runtime: `process.env.VITE_API_URL`.
3. Vite build-time env: `import.meta.env.VITE_API_URL`.
4. Fallback: `http://localhost:8000`.

`API_CONFIG.baseUrl` is the only application-facing API URL value. Do not read `import.meta.env.VITE_API_URL` directly outside the runtime-config helper; Vite will inline it at build time and a prebuilt Docker/SSR image can keep pointing at the wrong backend.

`API_CONFIG` also sets a 30-second request timeout, three retry attempts for `5xx` server errors, and a one-second base retry delay.

## Shared API client behavior

Use `apiClient` for normal backend calls:

- `request<T>()` builds `${API_CONFIG.baseUrl}${endpoint}` and serializes `options.params` into the query string.
- `get`, `post`, `patch`, `put`, and `delete` wrap `request`.
- `postForm` sends `application/x-www-form-urlencoded` data and is used by login.
- `postMultipart` uploads `FormData` and intentionally does not set `Content-Type`; the browser sets the multipart boundary.
- `fetchRaw` returns the raw `Response` for streaming flows such as Server-Sent Events.
- Bearer tokens are read from session storage and attached as `Authorization: Bearer <token>` when available.
- `401` clears the local session and redirects browser users to `ROUTES.login`.
- `5xx` responses are retried; `4xx` responses are not retried by TanStack Query defaults.
- Responses parse as JSON when `content-type` includes `application/json`, text otherwise, and `204`/empty responses return `undefined`.

## Session and auth state

`lib/auth/session` stores:

- `ow_auth_token`
- `ow_developer_id`
- `ow_session_expiry`

The default session duration is 24 hours. `getSession()` returns `null` during SSR and clears expired sessions. Protected routes must keep browser-only auth checks guarded by `typeof window === 'undefined'`.

`useAuth()` owns login, register, logout, `me`, forgot/reset password, and change-password mutations. Login and register store the token/developer id, show a toast, and navigate to `DEFAULT_REDIRECTS.authenticated`. Logout clears session even if the server call fails.

## Query client defaults

The shared query client uses:

- Query `staleTime`: 5 minutes.
- Query `gcTime`: 10 minutes.
- Query retry: skip `ApiError` client errors (`4xx`), retry up to three times otherwise.
- `refetchOnWindowFocus`: false.
- `refetchOnReconnect`: true.
- Mutations: no retry.

Respect these defaults unless a route has a specific reason to override them.

## Query-key factory map

All server state keys come from `queryKeys`. Important families:

| Family | Key purpose | Typical owner |
| --- | --- | --- |
| `auth.session()` | Current developer/session query | `useAuth` |
| `users.list(params)`, `users.detail(id)` | User list/detail state | users pages and profile panels |
| `dashboard.stats()`, `dashboard.charts(timeRange)` | Dashboard metrics and chart data | dashboard page |
| `apiKeys.*` | API-key list/detail | credentials settings |
| `applications.*` | SDK application list | credentials settings |
| `oauthProviders.list(cloudOnly, enabledOnly)` | Provider settings and provider pickers | settings providers, pairing, widget, sync filters |
| `priorities.providers()`, `priorities.deviceTypes()`, `priorities.dataSources(userId)` | Provider/device/source priority state | settings priorities and user source controls |
| `archival.settings()` | Data lifecycle settings and estimates | settings data lifecycle |
| `seedData.presets()`, `seedData.sleepProfiles()` | Seed-data form options | settings seed data |
| `webhooks.list()`, `detail(id)`, `secret(id)`, `eventTypes()`, `attempts(id)` | Outgoing webhook list/detail/delivery state | webhooks pages |
| `config.all` | Instance feature/config flags | webhooks and settings-gated UI |
| `syncStatus.recent`, `runs`, `allRuns` | Sync status lists and monitor | syncs page and user profile |
| `connections.all(userId)` | User provider connections | profile and pairing success |
| `health.*` | Workouts, summaries, sleep, activity, body, scores, timeseries, data summaries | user detail tabs |
| `garmin.backfillStatus(userId)` | Garmin historical backfill state | connection card |
| `meta.coverage()` | Provider coverage matrix | coverage page |

Never invent new bare arrays in feature code when a key belongs in this factory.

## Service and hook map

| Frontend need | Service module | Hook(s) | Notes |
| --- | --- | --- | --- |
| Login/register/session/password | `authService` | `useAuth` | Login is form-encoded; other auth calls are JSON. |
| User list/detail CRUD | `usersService` | `useUsers`, `useUser`, `useCreateUser`, `useUpdateUser`, `useDeleteUser` | `useUpdateUser` performs optimistic detail-cache updates and rolls back on error. |
| Apple Health XML import | `usersService` | `useUploadAppleXml`, `useUploadAppleXmlViaS3`, `useAppleXmlUpload` | `useAppleXmlUpload` validates `.xml`/XML MIME, max size, and chooses direct vs S3 based on file size. |
| Mobile app invitation code | `usersService` | `useGenerateInvitationCode` | Used by the user-detail mobile app dialog. |
| Health summaries/events/timeseries | `healthService` | `useWorkouts`, `useTimeSeries`, `useSleepSessions`, `useSleepSummaries`, `useActivitySummaries`, `useBodySummary`, `useHealthScores`, `useUserDataSummary`, `useMenstrualCycles` | Query hooks usually require `userId`; date-range hooks require start/end fields before enabling. |
| Provider connections and sync | `healthService` | `useUserConnections`, `useDisconnectProvider`, `usePurgeProviderData`, `useSynchronizeDataFromProvider`, `useSyncHistoricalData`, Garmin backfill hooks | Mutations invalidate connections and relevant health/data-summary keys. |
| OAuth provider settings | `oauthService` | `useOAuthProviders`, `useUpdateOAuthProviders`, `useUpdateProviderLiveSyncMode` | Live-sync mode uses optimistic updates across all OAuth provider queries. |
| Pairing OAuth redirect | Direct fetch through `API_CONFIG.baseUrl` | `useOAuthConnect` | Calls `/api/v1/oauth/{provider}/authorize` with `user_id` and `redirect_uri`, then assigns `window.location.href` to the returned authorization URL. |
| Provider/device/source priority | `priorityService` | priority hooks | Bulk updates invalidate the `priorities.all` family. |
| Dashboard metrics | `dashboardService` | dashboard hooks | Endpoint constants mark dashboard chart/stat endpoints as frontend-known; confirm backend support before relying on new behavior. |
| Outgoing webhooks | `webhooksService` | webhook hooks | Event types and secrets are long-lived; endpoint changes update detail cache and invalidate list. |
| Sync monitor/SSE | `syncStatusService` | `useRecentSyncs`, `useSyncRuns`, `useAllSyncRuns`, `useSyncStatusStream` | SSE uses `fetchRaw` with `Accept: text/event-stream` and `replay` query param. |
| Instance config | `configService` | `useConfig` | Webhook UI disables create when outgoing webhooks are off. |
| API keys | `apiKeysService` | API-key hooks | Create/update/revoke/delete invalidate API-key lists. |
| SDK applications | `applicationsService` | application hooks | Create/rotate return one-time app secrets for UI reveal dialogs. |
| Developers/team | `developersService`, `invitationsService` | developer/invitation hooks | Invitation creation adds to cached list; revoke/resend invalidate list. |
| Data lifecycle | `archivalService` | archival hooks | Save and manual trigger invalidate archival settings. |
| Seed data | `seedDataService` | seed hooks | Generate invalidates dashboard and users; backend work runs asynchronously. |
| Provider coverage | `metaService` | `useCoverage` | Coverage is capabilities, not per-user synced data. If provider `coverage.py` changes but `/api/v1/meta/coverage` keeps the same schema, the hook and coverage page should update from API data without a frontend code change. |
| Automations | `automationsService` | automation hooks | Frontend hooks exist; confirm backend endpoint availability before UI expansion. |

## Mutation invalidation patterns

Use these examples as the house style:

- User create/delete: invalidate `queryKeys.users.lists()` and active `queryKeys.dashboard.stats()`.
- User update: cancel detail query, snapshot previous detail, optimistically update the detail cache, set server result on success, invalidate lists, and roll back on error.
- Apple XML upload: invalidate the user detail and active health-family queries.
- Provider disconnect/purge/sync: invalidate `queryKeys.connections.all(userId)` and affected health/data-summary keys.
- Historical sync start: invalidate connections and provider-specific backfill status where relevant.
- Pairing success: invalidate `queryKeys.connections.all(userId)` with `refetchType: 'all'`.
- Webhook create/delete: invalidate `queryKeys.webhooks.lists()`.
- Webhook update: set `queryKeys.webhooks.detail(id)` to the updated endpoint and invalidate lists.
- OAuth provider toggles: invalidate `queryKeys.oauthProviders.all` after save; single live-sync-mode changes use optimistic `setQueriesData` across provider queries.
- Seed generation: invalidate dashboard and users because generated data arrives asynchronously.
- Sync SSE terminal events: invalidate the `syncStatus.all` family; started events invalidate connections because a provider may have just been paired.

## SSE sync-status state

`useSyncStatusStream(userId, enabled = true, replay = 20)`:

- Clears previous user events before opening a new stream.
- Opens `/api/v1/users/{userId}/sync/stream?replay=<n>` through `syncStatusService.openStream`.
- Expects event blocks with event name `sync.status`; malformed JSON is ignored.
- Keeps up to 200 recent events.
- Tracks latest active event per `run_id` until status becomes one of `success`, `failed`, `partial`, `cancelled`, or `skipped`.
- Exposes `connected`, `error`, and `reconnect()` for UI recovery.

Use this hook once per user-detail profile and pass grouped state into provider cards instead of opening one stream per card.

## Adding a frontend endpoint consumer

1. Confirm backend endpoint shape and authorization with `backend-core`; do not guess server semantics from a UI mock.
2. Add or update an `API_ENDPOINTS` entry.
3. Add a typed service method in the closest service module.
4. Add a query-key family or method in `queryKeys` if no existing key fits.
5. Add a hook in `hooks/api` using `useQuery` or `useMutation`.
6. Add correct `enabled` guards for required params and date ranges.
7. In mutations, update the exact detail cache when possible and invalidate list/summary/dashboard families as needed.
8. Surface success/error toasts only where user action feedback is useful; avoid noisy toasts for passive refetch failures that routes already render.
9. Use `API_CONFIG.baseUrl` only for display, image URL construction, raw provider OAuth redirects, and runtime API URL copy UI; normal calls should go through services and `apiClient`.

## Special data shapes and caveats

- Coverage matrix rows represent provider capability declarations. They do not mean the current user has synced that data.
- Sync run list filters use strings for `provider`, `status`, `source`, and `user_id`; frontend pagination overfetches by one item to detect `hasMore`.
- Webhook delivery attempts use an iterator stack for previous/next pagination and can filter by status, limit, and multiple event types.
- Direct uploaded Apple XML and S3 uploaded XML both invalidate health data but processing can be asynchronous.
- Provider icon URLs may be relative from the backend; build display URLs with `new URL(relative, API_CONFIG.baseUrl)` or `${API_CONFIG.baseUrl}${icon_url}` depending on the component's existing style.
- The widget connect page currently simulates OAuth and posts `wearable_connected` / `wearable_widget_close` messages to a parent frame; the real OAuth pairing flow lives under `/users/$userId/pair`.
