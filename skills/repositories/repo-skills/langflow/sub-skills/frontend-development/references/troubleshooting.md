# Frontend Troubleshooting

## Install and Import Failures

Symptoms:

- `npm install` or `npm ci` fails with engine errors.
- Vite cannot resolve `@/...` imports.
- Jest cannot resolve CSS, `uuid`, `vanilla-jsoneditor`, or Vite `import.meta` usage.
- Native browser packages or Playwright browsers are missing.

Checks and fixes:

- Confirm Node.js is `>=20.19.0`; use the project-recommended Node LTS when possible.
- Run commands from the frontend package directory unless using a root `make` target.
- Use the package lock from the checkout; do not hand-edit dependency versions unless the task is dependency maintenance.
- Confirm TypeScript path alias support is available through Vite tsconfig paths and Jest module name mapping.
- For Jest failures, check whether the test uses configured mocks and `src/setupTests.ts` browser API shims.
- For Playwright, install browser binaries only when the user approves the time/network cost.

Use the bundled static helper before npm work if package script drift is suspected:

```bash
python scripts/check_frontend_package.py src/frontend/package.json
```

## Vite Dev Server and Proxy Failures

Symptoms:

- Browser shows CORS errors, 404s, or API calls to `localhost:3000` without proxying.
- `/health` fails from the frontend dev server while the backend is down or on another port.
- Login or auto-login loops on first load.
- WebSocket or streaming behavior fails in dev but works in packaged mode.

Checks and fixes:

- Start the backend first and confirm `/health` returns a healthy response on the backend port.
- Start the frontend dev server after backend readiness.
- Set `VITE_PROXY_TARGET=http://localhost:7860` when the backend runs on the default port, or to the actual backend URL when different.
- Confirm API calls use proxied `/api/v1/`, `/api/v2/`, or `/health` paths instead of absolute incorrect origins.
- Check compiled env defaults for `BACKEND_URL`, `LANGFLOW_AUTO_LOGIN`, and feature flags when behavior differs between dev and build.
- If a change only fails in production build, run `npm run build` and inspect Vite import or asset errors before changing backend code.

## Data, Config, and Schema Errors

Symptoms:

- Component palette entries are missing or duplicated.
- A node has no template and is deleted or shows an error.
- Node inputs/outputs render with wrong handles, hidden fields, or colors.
- Saved flow JSON reloads with broken edges or stale node update prompts.
- React Query consumers hang because API errors are swallowed.

Checks and fixes:

- Confirm backend component metadata contains the expected template, inputs, outputs, display name, and icon key.
- Keep saved-flow compatibility in mind: do not rename backend component classes or serialized node identifiers to fix display-only issues.
- Update TypeScript types and store transformations when backend schemas change.
- Recompute node internals when handles, output visibility, or template structure changes.
- Preserve API error rejection so stores, React Query, and alert UI receive failures.
- If a node update validates code through the backend, preserve pending-update registration/completion so flow runs wait for node refresh.

## Icon Failures

Symptoms:

- Missing icon in component palette or node header.
- Console error from a lazy icon import.
- Build fails on JSX/SVG syntax.
- Icon is invisible in dark mode.

Checks and fixes:

- Confirm the backend `icon` string matches a Lucide name, category icon, or custom lazy import key.
- Confirm the custom icon directory exports the component name referenced by the lazy import callback.
- Use `forwardRef` and pass through SVG props so sizing and color work in existing icon wrappers.
- Prefer `currentColor` or explicit dark/light handling when an imported asset has fixed fills.
- Add a focused test or build check when editing lazy import maps.

## CLI/API Misuse From Frontend Context

Symptoms:

- A frontend task attempts to fix a backend route by hard-coding a different browser URL.
- A UI button calls a backend endpoint that lacks auth, route, or schema support.
- API-key, auth, or workspace behavior works through curl but fails in the browser.

Checks and fixes:

- Do not bypass the shared API controller or base URL helpers unless the endpoint is intentionally external.
- Keep custom headers same-origin only; do not leak them to GitHub or analytics domains.
- Coordinate backend route/schema/auth changes with backend-runtime and then update controller/query/store consumers.
- Confirm cookies and credentials behavior before adding manual `Authorization` handling.
- Use API mocks for frontend unit tests; use backend route tests in the backend owner area for server-side behavior.

## Backend, Runtime, Credentials, Network, and Hardware Boundaries

Frontend work may expose but should not solve unrelated backend/runtime issues.

- If the backend cannot import optional Python providers, route install/runtime fixes to deployment-and-operations or backend-runtime.
- If a flow uses API keys or provider credentials, keep frontend tests mocked or use non-credentialed fixtures.
- If PyTorch, transformers, GPU, or model execution is required, treat it as out of scope for normal frontend validation.
- If Playwright starts the backend and fails on Python dependency errors, record the dependency failure and choose Jest/static checks instead of mutating the Python environment without approval.
- If Docker or packaged serving fails after a successful frontend build, route operational serving concerns to deployment-and-operations.

## Build Mismatch After Component Index Changes

Symptoms:

- A backend component exists in source but not in the frontend palette.
- The UI shows an old display name, old icon, or stale input fields after backend edits.
- A node says updates are available even after a browser refresh.

Resolution sequence:

1. Confirm whether backend dynamic component loading is active during development.
2. If dynamic loading is off, have the component-development owner rebuild or refresh the backend component index.
3. Restart the backend and hard-refresh the browser.
4. Check whether the frontend `typesStore` receives updated component data.
5. Verify icon keys and display metadata in the frontend after backend metadata is corrected.
6. Only change frontend code when the UI mapping, icon import, controller, or graph rendering logic is the actual mismatch.

## Test Selection Problems

- Jest is best for stores, controllers, pure helpers, icon mapping utilities, auth context, and component rendering with mocks.
- Playwright is best for canvas interactions, keyboard shortcuts, graph layout, upload/import flows, browser clipboard, and full regression paths.
- `npm run type-check` catches TypeScript and Vite contract issues but can be slower than focused Jest.
- `npm run build` catches Vite/SWC/lazy import and asset issues that Jest may mock away.
- Avoid broad Playwright runs unless the environment is prepared and the task needs browser-level confidence.
