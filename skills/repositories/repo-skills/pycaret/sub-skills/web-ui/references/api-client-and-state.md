# API Client and State

## Purpose

Read this before changing API calls, auth state, token refresh, WebSocket URLs, TanStack Query usage, Zustand stores, or API type mirrors in the React UI.

## File ownership

| File | Role |
|---|---|
| `src/api/client.ts` | Thin axios instance with `/api/v1` base URL, bearer token injection, single-flight 401 refresh, and `errorMessage()`. |
| `src/api/endpoints.ts` | One typed function per backend route used by the UI. Components import endpoint groups from here. |
| `src/api/types.ts` | Hand-written mirrors of pycaret-server Pydantic schemas and UI response envelopes. |
| `src/state/auth.ts` | Zustand auth store: access token in memory, refresh token in `localStorage`, user row, refresh/clear helpers. |
| `src/state/uiPrefs.ts` | UI preferences such as sidebar collapse and theme. |
| `src/main.tsx` | Creates the global QueryClient and applies theme behavior. |

## Axios client contract

`client.ts` exports `api`, an axios instance configured with:

- `baseURL = '/api/v1'`.
- `timeout = 30_000` for normal API calls.
- Request interceptor reads `useAuthStore.getState().accessToken` and sets `Authorization: Bearer <token>` when present.
- Response interceptor retries once on a 401 by calling `useAuthStore.getState().refresh()`.
- Refresh is single-flight: concurrent 401s share the same in-flight promise.
- Requests to `/auth/refresh` are not recursively refreshed.
- `errorMessage(err)` extracts backend `{detail}` strings from axios errors and falls back to `err.message` or `String(err)`.

Do not create independent axios instances in pages. The auth store intentionally imports bare `axios` for refresh to avoid circular imports and interceptor recursion.

## Auth store contract

`state/auth.ts` stores:

- `accessToken`: memory only.
- `refreshToken`: loaded from `localStorage` key `pycaret.refresh_token`.
- `user`: current user, populated by `Layout` via `authApi.me`.
- `setTokens(pair)`: writes refresh token to localStorage and access token to memory.
- `clear()`: removes refresh token and clears auth/user state.
- `refresh()`: bare `axios.post('/api/v1/auth/refresh', { refresh_token })`, then `setTokens`; returns `false` and clears state on failure.

`AuthGate` renders children only when an access token exists. If only a refresh token exists, it calls `refresh()` once, shows "Restoring session…", then either renders or redirects to `/login` with `state.from`.

### Auth troubleshooting signals

- Login works but refresh after reload fails: check `pycaret.refresh_token` in localStorage and `POST /api/v1/auth/refresh` response.
- Infinite 401 loop: confirm only one retry is attempted (`_retried` flag) and refresh endpoint itself is exempt.
- Blob downloads: use endpoint helpers like `runsApi.trialDownload`; a plain `<a download>` will skip bearer headers.

## Endpoint groups

`endpoints.ts` groups API methods by surface. Keep one function per route and return `r.data` from axios. Current groups include:

- `setupApi`: setup status and bootstrap.
- `authApi`: login, refresh, logout, me.
- `workspacesApi`, `projectsApi`, `experimentsApi`.
- `describeApi`: `setupParams(task)`, `models(task)`, `metrics(task)`; this drives dynamic forms and dropdowns.
- `runsApi`: run list/submit/get/events/cancel/wait/promote, run-level trials, trial detail/download/plot/promote/unpromote/tune/ensemble/blend/stack/patch/predict/cv/cohorts.
- `trialsApi`: experiment-level trial views and direct trial operations.
- Catalog/governance/admin groups: secrets, connections, datasets, lineage, git, registry, monitoring, governance, queue admin, notebooks, analyses, pipelines, deployments, schedules, templates, webhooks, model library, admin, data sources, sample datasets, plots, audit, API keys, drift, members.
- `llmApi`: provider settings, connection test, dataset analysis, experiment design, run explain/debug, deployment review, drift analysis, consultation list/get.

When adding a backend route to the UI:

1. Add a request/response type in `types.ts` or a narrow inline type only when it is truly one-off and small.
2. Add an endpoint function in the matching group in `endpoints.ts`.
3. Use existing URL conventions: endpoint functions use paths relative to `/api/v1`, e.g. `/workspaces/${workspace_id}/projects`.
4. Encode IDs for path segments when the ID or kind can contain special characters; plot endpoints already use `encodeURIComponent`.
5. Add or update tests that mock the endpoint group.

## Type mirror rules

`types.ts` is currently hand-written while the UI surface is still manageable. It mirrors Pydantic schemas closely enough for TypeScript strictness and UI payload construction.

Rules:

- Keep enum/string literal unions aligned with backend values (`TaskType`, `RunStatus`, `TrialKind`, `TrialStatus`, `ScheduleKind`, `LLMProviderName`, etc.).
- Use `Record<string, unknown>` for JSON blobs that the UI displays or forwards but does not own.
- Preserve nullability from the backend; do not replace nullable fields with optional fields unless the backend truly omits the key.
- Add comments for contract details that affect UI behavior, such as `TokenPair`, `SetupParamSchema`, `LLMAdvice`, `PlotEnvelope`, `PipelineNode`, and deployment prediction response.
- `npm run gen:api` and `npm run gen:api:file` exist to produce `src/api/schema.ts`, but the generated file is not the active client surface.

## Dynamic form and describe API contract

`describeApi.setupParams(task)` returns `SetupParamSchema`:

```ts
type TaskType = 'classification' | 'regression' | 'clustering' | 'anomaly' | 'time_series';
type ParamKind = 'bool' | 'int' | 'float' | 'enum' | 'column' | 'string';

interface SetupParamSchema {
  task: TaskType;
  parameters: SetupParam[];
  groups: string[];
}
```

`DynamicForm` must be driven entirely by this schema:

- Preserve `schema.groups` order.
- Render `bool` as a switch, `int`/`float` as numeric input with min/max/step, `enum` as choices, `column` as a dataset-column select when columns are known and a text input otherwise, and `string` as text.
- Use `applyDefaults(schema, current)` to seed defaults without overwriting user choices.
- Use `stripDefaults(schema, values)` before submit so the API receives only user intent.
- Do not hard-code parameter names in `DynamicForm`. If a curated screen needs first-class widgets for known parameters, do it in `ExperimentConfigForm` and keep a fallback for the remaining schema parameters.

## TanStack Query conventions

The global `QueryClient` in `main.tsx` sets:

- `refetchOnWindowFocus: false`
- `retry: 1`
- `staleTime: 30_000`

Per-component conventions observed in the UI:

- Scope keys by entity and ID: `['runs', runId]`, `['runs', runId, 'trials']`, `['workspaces', wsId, 'llm', 'settings']`.
- Use `enabled` to avoid calls with empty IDs.
- Poll only while a resource is active. Example: run detail refetches every 2 seconds while queued/running; deployment lists poll counters every 5 seconds; queue admin polls every 5 seconds.
- Set longer `staleTime` for introspection data such as models, metrics, setup params, and plot registry.
- Invalidate narrow keys after mutations: trial promote invalidates run trials and pipeline lists; deployment create invalidates deployments; model status changes invalidate the model detail and versions.
- In tests, create a new `QueryClient({ defaultOptions: { queries: { retry: false } } })` for each render.

## WebSocket contract

Both `EventStream` and `EventLogDrawer` connect to:

```text
/api/v1/runs/:run_id/events/ws?token=<access_token>
```

Runtime behavior:

- The client builds an absolute `ws://` or `wss://` URL from `window.location`.
- Server replays stored events, then streams live events.
- Terminal sentinel is `{ kind: 'run.closed' }`; the client treats it as terminal and does not reconnect.
- Auth close codes `4401` and `4403` are not retried.
- Unexpected close is retried once after 500 ms.
- Events are deduplicated because React StrictMode and reconnects can replay stored events.

Dev proxy support lives in `vite.config.ts`: `/api` has `ws: true`, and `/ws` is also proxied. If event logs show `closed · 0 events`, verify the backend port in the proxy and that `ws: true` is still present.

## LLM advice envelope

Every LLM component should render the same envelope from `LLMConsultationRead.response_json`:

- `suggested_config_json`
- `suggested_action`
- `reasoning_summary`
- `risk_flags`

UI components may label these fields differently for context ("Verdict", "Suggested fix", "Next step"), but must keep the advisory contract visible. Do not auto-execute the suggested action. User-initiated actions may copy values into forms or navigate to an approval/deploy screen.

## API changes checklist

When the backend adds or changes a route that the UI consumes:

1. Update `types.ts` mirrors.
2. Update `endpoints.ts` group functions.
3. Update affected components to use the endpoint group.
4. Update tests to mock the endpoint group and assert request body/query params.
5. Run `npm run typecheck` before manual browser testing.
6. If a route changed path or auth behavior, also run route/API mismatch checks from [Troubleshooting](troubleshooting.md).
