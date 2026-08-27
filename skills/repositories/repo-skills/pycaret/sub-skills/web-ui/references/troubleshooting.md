# Web UI Troubleshooting

## Purpose

Use this when PyCaret Control Plane UI work fails at auth, route wiring, schema-driven forms, Vite proxying, WebSockets, Plotly rendering, npm/Node versions, or browser/API integration. For backend route semantics, database behavior, or engine behavior, route to the owning backend/engine skills.

## 401 refresh and auth loops

### Symptoms

- A page loads, then redirects to `/login` after refresh.
- API calls fail with 401 even though a refresh token exists.
- Many concurrent requests all fail after one expired token.
- Blob downloads fail with 401 while normal JSON calls work.

### Likely causes

- `accessToken` is memory-only and was lost on reload; `AuthGate` should call `refresh()` using the persisted refresh token.
- `localStorage` key `pycaret.refresh_token` is missing or stale.
- The axios interceptor did not attach `Authorization`.
- Refresh endpoint returned 401/403 and `clear()` removed tokens.
- A plain `<a href download>` bypassed axios interceptors.

### Checks and fixes

1. In browser devtools, inspect localStorage for `pycaret.refresh_token`.
2. Confirm `POST /api/v1/auth/refresh` sends `{ refresh_token }` to `/api/v1/auth/refresh` and returns a `TokenPair`.
3. Confirm a retried request has `Authorization: Bearer <new access token>`.
4. Check `client.ts` still skips refresh recursion on `/auth/refresh` and marks retried requests with `_retried`.
5. Use endpoint helpers for authenticated downloads, e.g. `runsApi.trialDownload`, not a raw anchor tag.
6. In tests, reset the Zustand store and localStorage between cases.

Stop and route to the API skill if refresh returns a backend validation or auth-policy error despite correct request shape.

## Route/API mismatch

### Symptoms

- Browser shows the not-found page for an expected route.
- Sidebar link goes to a route but `App.tsx` has no matching `<Route>`.
- API call returns 404 while the page route exists.
- A page uses `wsId` but the route param is actually `id`.

### Checks and fixes

1. Print the route table:

   ```bash
   node scripts/list_ui_routes.mjs /path/to/repo
   ```

2. Confirm `src/App.tsx` imports the page and adds the route under `<Layout>` for authenticated surfaces.
3. Confirm sidebar links in `Layout` and `CommandPalette` use the same path string.
4. For `/workspaces/:id`, use `useParams<{ id: string }>()`; for most other workspace routes use `wsId`.
5. For flat routes (`/runs/:runId`, `/deployments/:deploymentId`), remember workspace context is recovered by `Layout` fetching the row.
6. For API 404s, inspect `src/api/endpoints.ts`; endpoint paths are relative to `/api/v1` and usually begin with `/workspaces`, `/runs`, `/deployments`, etc.
7. If the backend route truly changed, update `types.ts`, `endpoints.ts`, components, and tests together.

## DynamicForm schema problems

### Symptoms

- New engine setup parameter does not render.
- Default values are always submitted even when the user did not change them.
- A target/column param renders incorrectly.
- TypeScript errors around `SetupParam.kind` or missing fields.
- A future agent added hard-coded setup parameter names to `DynamicForm`.

### Likely causes

- `describeApi.setupParams(task)` response shape diverged from `SetupParamSchema`.
- `schema.groups` omitted a group; unlisted groups collapse into the created bucket, but ordering may be surprising.
- A new `ParamKind` was added by the backend/engine and the UI switch does not handle it.
- `stripDefaults()` was skipped before `experimentsApi.create`.
- `DynamicForm` was used where curated behavior belongs in `ExperimentConfigForm`.

### Checks and fixes

1. Fetch `GET /api/v1/describe/setup-params?task=<task>` and compare to `types.ts` `SetupParamSchema`.
2. Keep `DynamicForm` generic. It may switch on `kind`, but must not contain parameter-name-specific logic.
3. If a new structural kind exists, extend `ParamKind`, `ParamInput`, tests, and troubleshooting docs.
4. Use `applyDefaults(schema, params)` for display state and `stripDefaults(schema, seededParams)` for API payloads.
5. In curated screens, keep unknown params visible via `ExperimentConfigForm` "Other options" so engine additions do not disappear.
6. Run `npm test -- DynamicForm` or full `npm test` after form changes.

## Vite proxy issues

### Symptoms

- UI dev server loads but API calls return 404 or CORS/network errors.
- Event log WebSocket closes immediately in dev.
- `/healthz` from the browser hits the wrong service.

### Expected config

`vite.config.ts` serves on port `3020` and proxies:

- `/api` to the FastAPI backend with `changeOrigin: true` and `ws: true`.
- `/ws` to the backend with `ws: true`.
- `/healthz` to the backend.

### Checks and fixes

1. Confirm backend is running on the port in `vite.config.ts`.
2. Confirm `/api` proxy includes `ws: true`; without it, WebSocket upgrade can 404.
3. Confirm frontend calls use same-origin `/api/v1/...`, not a hard-coded backend host.
4. If local ports differ, update dev proxy or use the repository's documented environment/port overrides for the backend; do not bake private hostnames into runtime UI code.
5. Production nginx/Compose routing belongs to platform operations.

## WebSocket/event log failures

### Symptoms

- `EventLogDrawer` shows `connecting` then `closed` with zero events.
- Auth failure close code `4401` or `4403` appears.
- Events duplicate in React StrictMode.
- The event log works after refresh but not live.

### Likely causes

- Missing access token query parameter.
- Vite proxy lacks WebSocket upgrade support.
- Backend closed with auth failure.
- Terminal run sent `run.closed` before new live events.
- StrictMode/reconnect replay duplicates were not deduplicated.

### Checks and fixes

1. Inspect the WebSocket URL: it should include `/api/v1/runs/<id>/events/ws?token=<encoded access token>`.
2. Check close code. `4401`/`4403` means auth; verify token freshness.
3. Confirm `EventStream`/`EventLogDrawer` still deduplicate via a stable event key.
4. Confirm terminal sentinel `run.closed` disables retry.
5. Confirm the backend is writing stored run events by checking `runsApi.events(runId)` if available.
6. For dev-only failures, verify `vite.config.ts` proxy settings.

Route to the engine workflow skill if event kinds/messages are wrong or missing from the engine. Route to the API skill if the WebSocket endpoint or stored events are broken.

## Plotly rendering problems

### Symptoms

- Plot cards are blank.
- Plotly throws layout/data errors.
- Build/typecheck fails around Plotly types.
- Chart text is unreadable or clipped.

### Likely causes

- API did not return a `PlotEnvelope` with `figure.data` and `figure.layout`.
- Plot kind is not registered for the task.
- A component bypassed `PlotlyFigure` and missed responsive sizing.
- `react-plotly.js` or `plotly.js-basic-dist` types are mismatched.

### Checks and fixes

1. Confirm response shape matches `PlotEnvelope` in `types.ts`.
2. Use `plotsApi.registry()` or trial `available_plots` to avoid requesting unsupported kinds.
3. Prefer `PlotlyFigure` for standard cards. It handles loading, error, retry, empty, width measurement, responsive config, and toolbar settings.
4. For specialized charts such as `TrialsCard`, keep `config={{ displayModeBar: false, responsive: true }}` and explicit layout margins/ranges.
5. If Plotly needs browser APIs in tests, assert wrapper behavior instead of relying on full chart rendering.

Route to the backend/engine owner if plot JSON generation is invalid.

## npm and Node version problems

### Symptoms

- `npm install` errors on engine version.
- TypeScript/Vite build behaves differently across machines.
- Native dependency install fails unexpectedly.
- Tests cannot find jsdom.

### Expected versions and deps

- `package.json` engines: `node >=20`.
- Project guidance: Node 22 primary, Node 20 floor; npm workspace with checked-in `package-lock.json`.
- Vite 5, React 18, TypeScript 5.6+, Vitest 2, jsdom 25.

### Checks and fixes

1. Check versions:

   ```bash
   node --version
   npm --version
   ```

2. Use `npm install` in `apps/web` with the checked-in lockfile.
3. Remove stale `node_modules` and reinstall if dependency resolution is corrupted.
4. Do not switch package managers or regenerate lockfiles unless explicitly required.
5. If `npm run build` fails before Vite output, inspect TypeScript errors first (`build` runs `tsc -b`).

## TypeScript/import failures

### Symptoms

- Error says a type import must use `import type`.
- Unused local/parameter breaks `typecheck`.
- Hooks lint error after adding early return.
- React-refresh lint warning fails the lint command.

### Fixes

- Convert type-only imports to `import type`.
- Delete unused values or prefix intentionally unused function parameters with `_`.
- Move hooks before conditional returns.
- Move non-component helpers/constants that trigger react-refresh into a separate `*.helpers.ts` file when needed.
- Keep `@/` alias imports for `src` code.

## LLM widget failures

### Symptoms

- LLM widget returns 400 or says no key configured.
- Advice renders but action is unclear or dangerous.
- A component fires an LLM call on page load unexpectedly.

### Checks and fixes

1. Check `/workspaces/:wsId/llm` settings. A key must be on file and enabled.
2. Use `llmApi.testConnection(wsId)` from the settings page to verify provider reachability.
3. Ensure every widget renders the four advice fields and labels the result advisory.
4. Auto-fire is only appropriate for modal consultations where opening the modal is the explicit user action (`AnalyzeDatasetModal`, `DeploymentReviewModal`, drift modal). Inline cards like run explain/debug should fire on button click.
5. Never wire `suggested_action` to a destructive mutation. Keep approve/deploy/retry as separate user actions.

## Useful diagnostic commands

From a repository checkout:

```bash
# List UI routes without installing packages.
node skills/disco/pycaret/sub-skills/web-ui/scripts/list_ui_routes.mjs .

# Run selected frontend static checks.
bash skills/disco/pycaret/sub-skills/web-ui/scripts/ui_static_check.sh --typecheck --test

# Full frontend gate.
cd apps/web && npm run typecheck && npm run lint && npm test && npm run build
```
