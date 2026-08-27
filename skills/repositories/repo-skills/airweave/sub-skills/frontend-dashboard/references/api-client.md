# API Client, Auth, and Organization Headers

## When to read this

Read this before adding or changing dashboard API calls, debugging missing auth/org headers, handling stale organization context, changing token refresh behavior, or using dashboard SSE/fetch streaming.

For backend request and response schemas, pair this with sibling [backend-api](../../backend-api/SKILL.md).

## Runtime configuration

- The dashboard API base URL is `env.VITE_API_URL`.
- Runtime `window.ENV.API_URL` wins over Vite env configuration; otherwise the Vite value is used; the local fallback is `http://localhost:8001`.
- Runtime/local development flags also come from `window.ENV` or `import.meta.env`.
- The Vite dev server is configured for port `8080`; the API base URL is still the backend URL, not the frontend dev server URL.

## Endpoint construction rules

Use `apiClient` with endpoint strings that start at the backend route root:

```ts
await apiClient.get('/collections');
await apiClient.post(`/collections/${readableId}/search/classic`, { query });
```

Do not add an `/api/v1` prefix in dashboard code. Airweave endpoints are mounted without a version prefix from the dashboard point of view.

The shared methods return the raw `Response`; callers are responsible for `response.ok`, `response.json()`, and `response.text()` handling.

## Token provider lifecycle

The client starts with a default token provider that can read `VITE_ACCESS_TOKEN`. At app boot, `ApiAuthConnector` replaces it with the auth-context provider:

- `getToken()` returns a bearer token or `null`.
- `clearToken()` clears the cached auth-context token.
- `isReady()` tells the request queue when Auth0/local-dev auth initialization is complete.

Requests queue while `isReady()` is false. The queue is retried periodically and again when `setTokenProvider` is called. This prevents early dashboard data loads from racing Auth0 token acquisition.

## Auth modes

### Auth-disabled local/dev mode

When auth is disabled, the dashboard treats the user as authenticated and returns a fixed development token string from `getToken()`. The mock user is named `Developer`, has email `dev@example.com`, and is admin unless `VITE_DEV_IS_ADMIN` is set to `false`.

`AuthGuard` still tries to initialize organizations in this mode, but it allows the app to render even if org initialization fails.

### Auth0 mode

When auth is enabled:

- Auth0 supplies the authenticated user and `getAccessTokenSilently()`.
- After token initialization, the frontend fetches `/users/` to enrich the Auth0 user with backend fields such as `is_admin`.
- Unauthenticated users are redirected to the login route by `AuthGuard`.
- Authenticated users must have organizations; no organizations redirects to onboarding.

## Headers on normal requests

Every normal request includes:

- `Content-Type: application/json`
- `Authorization: Bearer <token>` when a token exists
- `X-Organization-ID: <currentOrganization.id>` when an active organization exists
- `X-Airweave-Session-ID: <posthog session id>` when PostHog exposes one

If you debug a request that reaches the backend but acts on the wrong org, inspect the organization store first; the header is derived from that store at request time.

## Method quirks to preserve

- `get(endpoint, params)` appends `params` as query parameters.
- `post(endpoint, data, paramsOrOptions)` accepts either query params or an object with `{ params, signal }` for abortable requests.
- `put(endpoint, params, data)` uses the unusual order `(endpoint, params, data)`. Verify call sites before changing it.
- `patch(endpoint, data, params)` and `delete(endpoint, params)` are conventional.
- Request bodies are only sent for methods that support bodies. `GET` and `DELETE` do not serialize `data`.
- If a future feature needs extra per-request headers, add explicit API-client support; passing an arbitrary `extraHeaders` property into the current `post` helper is ignored.

## 401 and 403 handling

For a `401` or `403`, the client:

1. Calls `tokenProvider.clearToken()` when available.
2. Rebuilds headers with a fresh token.
3. Retries the request once.
4. If the retry is still `403`, refreshes organizations so the UI can reflect revoked permissions.

Do not add unbounded retry loops. Backend auth/permission failures after the single refresh should remain visible to callers.

## Organization auto-switching on GET responses

The API client can recover from stale organization context for successful `GET` requests:

1. It clones and parses the JSON response.
2. It looks for `organization_id` on the response object, or on the first item of an array response.
3. If the response org differs from the current org and is one of the user's organizations, it clears organization-scoped dashboard caches, switches the current organization, shows an informational toast, and retries the same GET once.

Important limits:

- Auto-switch only happens for `GET`.
- Auto-switch is skipped on the dashboard homepage to avoid fighting manual org switching.
- Mutations (`POST`, `PUT`, `PATCH`, `DELETE`) never auto-switch, because retrying them under a new org could create side effects.
- The cleared caches are collections, API keys, auth-provider connections, and usage data through the organization switch path.

Use this behavior for stale-resource display recovery, not for mutation recovery.

## SSE helper

`apiClient.sse()` uses the same base URL, auth readiness, headers, and one-shot token refresh semantics with `@microsoft/fetch-event-source`.

Use it when a backend route is an EventSource-style stream and the caller supplies `onMessage`, `onOpen`, `onError`, and optional `onClose`. It refreshes headers for reconnects and supports an external `AbortSignal`.

The dashboard search box currently uses a normal `POST` and manually parses streamed frames from `response.body` for agentic search; do not assume all search streaming goes through `apiClient.sse()`.

## Change checklist

- Use root-relative endpoints with no `/api/v1` prefix.
- Keep the raw `Response` contract unless refactoring every caller.
- Preserve request queue behavior while auth is not ready.
- Preserve single retry after `401`/`403` and org refresh on persistent `403`.
- Never auto-switch organizations for mutations.
- If a response includes `organization_id`, verify that the auto-switch behavior is appropriate for that route.
