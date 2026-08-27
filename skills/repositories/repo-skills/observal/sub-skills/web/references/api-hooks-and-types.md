# API Hooks and Types

This reference captures how the web frontend talks to the server, where shared types live, and how to add or change frontend data contracts without falling back to scattered `fetch` calls.

## Core API wrapper

`web/src/lib/api.ts` is the typed HTTP gateway for the web app.

### Baseline behavior

- Base path: `/api/v1`
- Request helper: typed `get`, `post`, `put`, `patch`, `del`
- Content type: JSON for request bodies
- Cache mode: `no-store`
- Retry: one retry after a short pause for 5xx responses
- Auth header: `Authorization: Bearer <access_token>` when a session token exists
- Session refresh: on 401 outside `/auth/*`, the wrapper tries a refresh-token exchange once, retries the original request if refresh succeeds, and clears the session/redirects to login if refresh is rejected
- Network failure guard: HTML 5xx/502 responses are normalized into user-facing errors instead of raw markup

### Storage contract

The auth model is intentionally split:

| Key | Storage | Purpose |
|---|---|---|
| `observal_access_token` | `sessionStorage` | Access token, cleared on tab close |
| `observal_refresh_token` | `localStorage` | Silent refresh across reloads and tabs |
| `observal_user_role` | `localStorage` | Cached role for guards/nav |
| `observal_user_name` | `localStorage` | Cached display name |
| `observal_user_email` | `localStorage` | Cached email |
| `observal_user_username` | `localStorage` | Cached username |
| `observal_user_avatar` | `localStorage` | Cached avatar URL |

`clearSession()` also removes the legacy `observal_api_key` key.

### Auth edge cases

- `refreshAccessTokenWithReason()` returns `ok`, `rejected`, or `network_error`.
- `useAuthGuard()` treats a refresh-token-only new tab as `refreshing`, tries silent refresh, and only redirects if the refresh is truly rejected.
- `useOptionalAuth()` resolves authenticated users without forcing a redirect.
- `setUserAvatar()` dispatches a `storage` event so the sidebar/nav can update immediately.

When debugging login loops, stale profile chips, or token refresh issues, inspect `clearSession()`, `setTokens()`, and `useAuthGuard()` together.

## Domain client groups

`api.ts` exports grouped clients for common frontend domains:

| Client | Examples |
|---|---|
| `auth` | `init`, `login`, `register`, `whoami`, `exchangeCode`, `deviceConfirm`, password/avatar operations |
| `registry` | list/get/create/install/delete, resolve identifiers, drafts, submissions, versions, visibility, archive/unarchive, edit locks |
| `review` | list queue, approve/reject agents and components, team-specific queue, related skills |
| `telemetry` | status |
| `users` | search |
| `teams` | list, detail, visibility, invites, join requests, membership |
| `dashboard` | registry/session overview, leaderboard, top items, exec dashboard data |
| `config` | public config, version, harnesses, SSO health |
| `insights` | insight status, report generation, report fetch, suggestion application, HTML export |
| `inbox` | work-feed list, counts, read/unread/done/dismiss/reopen |
| `exec` | executive dashboard metrics and config |
| `feedback` | component/agent feedback |
| `graphql` | GraphQL query helper for live/structured telemetry surfaces |

### Registry and harness details worth remembering

- `RegistryType` is the union `mcps | agents | skills | hooks | prompts | sandboxes`.
- `registry.resolveIdentifier()` is the canonical `namespace/slug` or UUID resolver used by shareable routes.
- `registry.previewConfig()` and `registry.validate()` feed the agent builder and validation panels.
- `registry.startEdit()` / `registry.cancelEdit()` power pending-item edit locks.
- `config.harnesses()` returns a `HarnessesResponse` with `harnesses: HarnessEntry[]` and an optional `default_harness`.
- `HarnessEntry` carries `name`, `display_name`, `capabilities`, and `supported_models`.

## Query hooks

`web/src/hooks/use-api.ts` is the main reusable hook barrel. It reexports the feature hooks from:

- `use-dashboard-api`
- `use-traces-api`
- `use-review-api`
- `use-insights-api`
- `use-admin-api`
- `use-sessions-api`
- `use-agents-api`
- `use-registry-api`
- `use-user-search`
- `use-teams-api`

Use the barrel when a hook is useful to multiple screens. Keep highly specific hooks in their domain module.

`use-harnesses()` stays in `web/src/hooks/use-harnesses.ts` and should be imported directly unless you intentionally widen the hook barrel.

### Representative hook patterns

| Hook | Contract pattern |
|---|---|
| `useWhoami()` | Auth session identity, `retry: false` |
| `useRegistryList(type, filters)` | List query keyed by type and filters |
| `useRegistryResolve(type, identifier)` | 404 is non-retryable; other failures retry once |
| `useComponentSubmit(type)` | Mutation invalidates the registry list and review queue |
| `useComponentSaveDraft(type)` | Mutation invalidates the registry list only |
| `useComponentVersions(type, listingId)` | Query enabled only when both identifiers exist |
| `usePublishComponentVersion()` | Mutation invalidates version list and listing detail |
| `useInsightReports(agentId)` | Polls faster when any report is pending/running |
| `useSessionSubscription()` | WebSocket event invalidation for session list/detail |
| `useDeploymentConfig()` | Caches public config for 5 minutes |
| `useServerVersion()` | Feeds version mismatch/banner behavior |

## Shared type placement

`web/src/lib/types.ts` is a barrel over feature-specific type files. Add new shared API shapes there or in the closest type module before importing them into components.

| Type file | Owns |
|---|---|
| `web/src/lib/types/registry.ts` | registry items, leaderboard items, versions, registry resolution, agent/component version detail |
| `web/src/lib/types/sessions.ts` | session lists, session detail, traces, errors, aggregated session stats |
| `web/src/lib/types/admin.ts` | admin users/settings, audit/security events, diagnostics, insight report models |
| `web/src/lib/types/team.ts` | teamspace, invite, and join-request shapes |
| `web/src/lib/types/dashboard.ts` | overview, leaderboard, harness usage, exec dashboard, and related analytics types |
| `web/src/lib/types/inbox.ts` | inbox items, counts, filters, and states |

### Change rule

If a server payload is reused by more than one component or page, put the type in a shared type file. If a page only needs a small local shape for view state, keep that local shape in the page or component.

## Adding a new frontend endpoint

When a screen needs new data:

1. Add the typed client method to `web/src/lib/api.ts`.
2. Add or update the shared response type in `web/src/lib/types/*.ts`.
3. Add a TanStack Query hook in the closest domain hook file.
4. Export the hook from `web/src/hooks/use-api.ts` if another screen will reuse it.
5. Invalidate the right query keys from mutations so list/detail screens stay in sync.
6. Prefer `enabled` guards for optional IDs instead of manual null checks in components.
7. Keep direct `fetch` calls out of components unless the request is a narrow one-off that cannot reasonably be turned into a shared client/hook.

## Synthetic case this skill must support

A future change may add a registry page that renders harness compatibility from server data instead of a static array. The expected pattern is:

- fetch harnesses through `useHarnesses()` or a new hook over `config.harnesses()`
- surface display names from the server response
- keep harness defaults server-driven
- use TanStack Query cache keys so the page does not re-fetch unpredictably
- update shared types if the harness payload gains new fields
