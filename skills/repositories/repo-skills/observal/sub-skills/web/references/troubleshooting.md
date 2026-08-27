# Web Troubleshooting

Use this reference when the frontend change fails to install, typecheck, build, navigate, refresh auth, fetch config, or pass Playwright.

## Start with the likely boundary

| Symptom | Likely owner |
|---|---|
| CLI command syntax, install semantics, or bundled command output | CLI |
| API response shape, auth enforcement, migrations, or server error text | Server |
| Harness registry, hook specs, telemetry delivery, or session parser issues | Harness-telemetry |
| Frontend route/component/hook/theme/rendering problem | Web |
| Repo-wide policy, release, lint, or broad test orchestration | Repo-development |

If the failure is really a backend or harness problem, fix the source owner instead of working around it in the UI.

## Install and import problems

| Symptom | What usually happened | Fix |
|---|---|---|
| `pnpm: command not found` | Corepack/pnpm is not active | Enable Corepack or activate the repo's pnpm version before installing |
| Workspace scripts cannot see `web` | Command ran outside the repo root or wrong workspace scope | Run from the repo root with `pnpm --filter web ...`, or `cd web` first |
| `ERR_PNPM_*` lockfile or resolution mismatch | Mixed package manager state or stale install | Re-run the install from the repo root with the repo's pnpm version; do not mix npm/yarn lockfiles |
| Import resolution fails for `@/...` | Vite/TSC alias or cwd mismatch | Keep the `@` alias rooted at `web/src` and run the commands in the workspace that owns `web/vite.config.ts` |

Useful baseline checks:

```bash
node --version
pnpm --version
pnpm --filter web typecheck
```

Expected signal: Node meets the repo's minimum, pnpm is the workspace version, and the typecheck exits cleanly.

## CLI/API/config failures that look like web bugs

### API proxy or backend unavailable

Symptoms:

- browser shows a blank shell, 502, HTML error text, or a generic request failure
- API calls time out or return a raw gateway page
- route renders but data never loads

Checks:

```bash
pnpm --filter web dev
curl -I http://localhost:3000/api/v1/config/version
```

Expected signal: the Vite dev server proxies `/api` and `/health` to the local API server. If the proxy call fails, the backend is the real problem.

### Auth/session refresh loops

Symptoms:

- redirected back to `/login` after opening a new tab
- user chip or sidebar role does not update after login/logout
- session disappears after a temporary network failure

Checks:

- inspect `sessionStorage` for `observal_access_token`
- inspect `localStorage` for `observal_refresh_token` and cached profile fields
- verify `clearSession()` is only called on a truly rejected refresh, not on a transient network error
- verify the `storage` event is fired after token/profile changes

Expected signal: a new tab with only a refresh token should recover silently; a genuinely rejected refresh should clear the session and redirect to `/login` with the saved next path.

### Missing harness data or hardcoded harness lists

Symptoms:

- a registry page shows old harness names
- pull/install commands use the wrong default harness
- harness badges do not match server configuration

Checks:

- verify the page reads `useHarnesses()` or a hook over `config.harnesses()`
- verify the UI uses the server-provided `display_name`
- verify `web/src/lib/api.ts` still exposes `config.harnesses()` and the `HarnessEntry` shape

Expected signal: harness names come from the server response, not a local array.

## Optional dependency and browser tooling issues

| Symptom | Likely cause | Fix |
|---|---|---|
| Playwright cannot launch Chromium | Browser binaries are missing | Install the browser for the workspace Playwright install, then rerun the spec |
| `pnpm --filter web e2e` fails immediately locally | The backend stack is not running | Start the local dev/API stack first; Playwright only drives the browser |
| CodeMirror, Mermaid, or charts fail to bundle | Dependency install was partial or stale | Reinstall the workspace dependencies and rerun `pnpm --filter web build` |
| Import errors mention Vite plugin or route generation | Route tree is stale | Restart the dev server and let the TanStack Router Vite plugin regenerate the tree |

Useful browser command when the Chromium binary is missing:

```bash
pnpm --filter web exec playwright install chromium
```

## Route generation and workflow problems

### TanStack route tree does not match the new file route

Symptoms:

- route file exists but navigation 404s
- a page component is never reached
- the generated tree appears stale

Fixes:

1. Confirm the route file is under `web/src/routes/`.
2. Confirm the file name uses the correct pathless layout conventions.
3. Restart `pnpm --filter web dev` so the route plugin rebuilds the tree.
4. Run `pnpm --filter web typecheck` after the tree refresh.

### Typecheck/build fail after a UI refactor

Symptoms:

- `pnpm --filter web typecheck` fails on API response shapes or route params
- `pnpm --filter web build` fails after a seemingly small component change

Fixes:

- update `web/src/lib/types/*.ts` rather than inventing ad hoc component types for shared responses
- add `validateSearch`/typed params when the route depends on query-state
- move repeated logic into the appropriate hook or component module
- keep shared values in `web/src/lib/api.ts` and its domain hook module

### Screenshot spec fails

Symptoms:

- a screenshot test times out
- an expected dialog/preview does not open
- the image path is missing

Fixes:

- wait for the relevant network idle or mutation completion before taking the screenshot
- use the exact tab/button/combobox text from the page
- ensure the fixture created the data required for the screenshot state
- rerun the targeted spec instead of the full E2E suite while debugging

## Telemetry and trace-rendering confusion

When the traces or insights UI looks empty, remember:

- the web app only renders the data; it does not create telemetry
- session ingestion, harness instrumentation, and GraphQL subscription behavior belong to the telemetry/harness/server stack
- `useSessionSubscription()` only invalidates the list/detail cache when live session events arrive

If there are no sessions to render, confirm the harness or server path first. Do not spend time patching the trace list component for missing upstream data.

## Escalate instead of masking

Escalate out of web when:

- a fix would require changing server auth, data shapes, or routes
- the issue is really harness naming, hook installation, or telemetry ingestion
- the CLI output or command syntax has changed
- the repo-wide test/lint/release workflow is the blocker

The web sub-skill should keep the frontend contract clean, not absorb another layer's responsibilities.
