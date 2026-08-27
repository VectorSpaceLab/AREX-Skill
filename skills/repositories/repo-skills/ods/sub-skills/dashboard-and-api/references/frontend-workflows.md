# ODS Dashboard Frontend Workflows

This reference distills the React/Vite dashboard, its production nginx wrapper, local development workflow, and focused UI validation surfaces.

## Frontend shape

- Product service: `dashboard`.
- Default UI port: `3001`.
- Stack: React 18, Vite 7, Tailwind CSS, lucide-react icons, Vitest, Testing Library, ESLint flat config.
- Production image: Node `20.19-alpine` builder runs `npm ci` and `npm run build`, then nginx serves `dist/` as a single-page app.
- Production nginx proxies `/api/*` to `dashboard-api:3002` and injects the dashboard API Bearer token.
- Vite dev server listens on port `3001` and proxies `/api` to `http://localhost:3002`.

## Directory and ownership map

| Area | Responsibility |
| --- | --- |
| `src/App.jsx` | App shell, first-run gate, ODS Talk host/path bypass, splash, sidebar layout, dynamic route rendering. |
| `src/plugins/core.js` | Built-in internal dashboard routes and the OpenCode external launcher. |
| `src/plugins/registry.js` | Extension points for internal routes and sidebar external links; merges API links with static/plugin links. |
| `src/pages/` | Route pages: Dashboard, Extensions, Service Map, Models, Remote Provider, Usage, Invites, Settings, FirstBoot, ODS Talk. |
| `src/components/` | Shared panels and UI: GPU cards/charts, setup wizard, preflight checks, feature discovery, topology, troubleshooting assistant, template picker, sidebar. |
| `src/hooks/` | API polling and workflow state: system status, version/update, first-run, session bootstrap, GPU details, models, downloads, PWA prompt. |
| `src/lib/serviceUrls.js` | Public/fallback service URL helpers used by sidebar/external links. |
| `src/test/` | Testing setup and utilities for Vitest/Testing Library. |
| `Dockerfile`, `nginx.conf`, `entrypoint.sh` | Production build and proxy/auth runtime. |
| `vite.config.js`, `vitest.config.js`, `eslint.config.js`, `tailwind.config.js` | Frontend build/test/lint/theme config. |

## Built-in UI route map

| Browser route | Page/component | Notes |
| --- | --- | --- |
| `/` | `Dashboard` | Main system overview; consumes `/api/status`, `/api/features`, `/api/services/resources`, service restart actions. |
| `/gpu` | `GPUMonitor` | Always registered, sidebar entry appears only on multi-GPU systems. Uses detailed GPU APIs. |
| `/extensions` | `Extensions` | Extension portal UI; consumes extension catalog/progress/template APIs. Manifest semantics belong to `services-and-extensions`. |
| `/extensions/integrations` | `ServiceMap` | Integration/service topology map. |
| `/models` | `Models` | Model library, Hugging Face import, download/load/delete/benchmark flows. Model internals belong to `hardware-and-models`. |
| `/remote-provider` | `RemoteProvider` | Remote GPU plan/probe/apply and peer model controls. |
| `/usage` | `Usage` | Token-spy/readiness/report flow; linked from Settings rather than top sidebar. |
| `/invites` | `Invites` | Owner/magic-link management. |
| `/settings` | `Settings` | Version, storage, settings summary/env edit/apply, setup state, usage summary. |
| `/talk` or `talk.<device>` host | `ODSTalk` | Chat/voice/attachment interface; rendered outside the normal sidebar shell. |
| first-run state | `FirstBoot` | Fullscreen onboarding when `/api/setup/status` reports `first_run=true`. |

## Production proxy behavior

The dashboard production container is not just static hosting. Its nginx layer is part of the authentication and timeout design:

- `location /` serves the React SPA and falls back to `index.html`.
- `location /api/` proxies to `dashboard-api:3002`, injects `Authorization: Bearer <DASHBOARD_API_KEY>`, and uses a normal API timeout.
- ODS Talk paths (`/api/talk/`) use unbuffered proxying and longer read/send timeouts for streaming and cold model sessions.
- Template apply, model load, and extension update/rollback have scoped long timeouts because those actions can pull/start services or load large local models.
- nginx uses Docker DNS (`127.0.0.11`) with a short validity window so recreated `dashboard-api` containers are resolved at request time instead of pinning an old IP.
- Static assets get long cache headers; security headers include frame/content-type/XSS protections, a CSP, and pre-staged HSTS.

The entrypoint reads the API key from `DASHBOARD_API_KEY` or `/data/dashboard-api-key.txt` and substitutes it into nginx config before starting nginx. If no key is available, same-origin API calls will fail with 401.

## Local development workflow

### Recommended host-side loop

For dashboard API and UI code edits, replace only the two dashboard containers with host-side processes and leave the rest of the ODS stack running:

```bash
# From the installed ODS root; frees ports 3001 and 3002.
docker compose stop dashboard dashboard-api

# Terminal 1: frontend hot reload on port 3001.
cd <ODS checkout>/ods/extensions/services/dashboard
npm install
npm run dev

# Terminal 2: native FastAPI reload on port 3002.
cd <ODS checkout>/ods/extensions/services/dashboard-api
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
ODS_INSTALL_DIR=<ODS checkout>/ods \
ODS_DATA_DIR=<ODS checkout>/ods/data \
ODS_AGENT_HOST=127.0.0.1 \
ODS_AGENT_PORT=7710 \
DASHBOARD_API_KEY=<dashboard-api-key> \
ODS_AGENT_KEY=<host-agent-key> \
  uvicorn main:app --host 127.0.0.1 --port 3002 --reload
```

Use placeholders above; do not paste secrets into logs or committed files.

Why this loop matters:

- The dashboard-api production image bakes Python files into `/app`. Host edits do not hot-reload in the running container.
- Vite's `/api` proxy points to `localhost:3002`, matching native uvicorn.
- Native uvicorn needs `ODS_AGENT_HOST=127.0.0.1` on typical host-side runs; otherwise host-agent-backed routes may try `host.docker.internal` and fail DNS or networking.
- Stop both containers. If only `dashboard-api` is stopped, the Docker `dashboard` nginx container still owns port `3001` and still proxies to the Docker service name `dashboard-api:3002`, which returns 502 when the API container is absent.

### Auth during local UI work

Production UI code usually calls `fetch('/api/...')` without manually setting an Authorization header because nginx injects it. Vite's default proxy forwards `/api` to native uvicorn but is not the production nginx entrypoint. If protected calls return 401 in a Vite-only loop, do not remove backend auth. Instead:

- confirm `DASHBOARD_API_KEY` is set in the uvicorn environment;
- test protected routes with `curl -H "Authorization: Bearer <key>"` or the pytest `TestClient`;
- if a local browser loop needs header injection, keep a dev-only proxy/header override outside committed production config unless the repo intentionally adds and tests one.

### Returning to production containers

```bash
docker compose start dashboard dashboard-api
```

Permanent shipped changes require a dashboard or dashboard-api image rebuild. A one-file `docker cp` into `/app` can prove a hot patch, but it is temporary and is overwritten by the next image rebuild.

## Frontend scripts

Run commands from the dashboard frontend directory:

```bash
npm install              # Install frontend dependencies.
npm run dev              # Vite dev server on port 3001.
npm run build            # Production build into dist/.
npm run lint             # ESLint over src/.
npm run test             # Vitest run.
npm run test:watch       # Interactive Vitest.
npm run test:coverage    # Coverage run.
```

Vite 7 requires Node 20.19 or newer in the production build image. If a local build fails before app code runs, check the Node version first.

## Frontend API consumers

| Consumer | Key endpoints |
| --- | --- |
| `useSystemStatus` | `/api/status` polling with abort/timeouts. |
| `useVersion` | `/api/version`, `POST /api/update`. |
| `useFirstRun` | `/api/setup/status`. |
| `useSessionBootstrap` | `/api/auth/verify-session`, `POST /api/auth/admin-session`; mints an owner session cookie when needed. |
| `useGPUDetailed` | `/api/gpu/detailed`, `/api/gpu/history`, `/api/gpu/topology`. |
| `useModels` and `useDownloadProgress` | `/api/models`, Hugging Face routes, model download/load/benchmark/delete/status/cancel routes. |
| `PreFlightChecks` | `/api/preflight/required-ports`, docker/gpu/ports/disk endpoints. |
| `FeatureDiscovery` | `/api/features`, `/api/features/{id}/enable`. |
| `Sidebar` | `/api/service-tokens`, `/api/external-links`. |
| `SetupWizard` / `FirstBoot` | templates, setup test/complete, magic-link owner-card/generate/QR, admin-session. |
| `Extensions` | extension catalog/progress/detail/install/update/rollback/enable/disable/uninstall/data purge. |
| `Settings` | `/api/settings/summary`, `/api/storage`, `/api/settings/env`, `/api/settings/env/apply`, `/api/usage/report`, `/api/setup/status`. |
| `RemoteProvider` | remote-provider status, peer model routes, plan/probe/apply. |
| `Usage` | usage readiness/report and remediation actions. |
| `ODSTalk` | talk status/session/message/stream/attachment/audio-message/speak. |

## Focused UI validation

Pick tests by changed surface:

```bash
cd <ODS checkout>/ods/extensions/services/dashboard

# URL helper / sidebar link behavior.
npm run test -- --run src/lib/serviceUrls.test.js
npm run test -- --run src/plugins/registry.test.js

# App routing/session bootstrap/first-run shell.
npm run test -- --run src/App.test.jsx
npm run test -- --run src/pages/FirstBoot.test.jsx
npm run test -- --run src/pages/Invites.test.jsx

# API-backed pages.
npm run test -- --run src/pages/Dashboard.test.jsx
npm run test -- --run src/pages/Extensions.test.jsx
npm run test -- --run src/pages/Models.test.jsx
npm run test -- --run src/pages/RemoteProvider.test.jsx
npm run test -- --run src/pages/Settings.test.jsx
npm run test -- --run src/pages/Usage.test.jsx
npm run test -- --run src/pages/ODSTalk.test.jsx

# Production build smoke.
npm run build
```

When tests mock `fetch`, mock every endpoint the mounted component can request during effects. Many dashboard pages fetch multiple APIs on mount; leaving one unmocked often produces confusing jsdom rejections unrelated to the intended assertion.

## Safe frontend change checklist

- Keep browser routes registered through the plugin route registry unless the route is intentionally outside the normal shell, such as ODS Talk.
- Preserve first-run gating: normal dashboard shell should be blocked while `/api/setup/status` reports first-run.
- Preserve production Bearer injection assumptions. Do not put raw dashboard API keys in React source or local storage.
- Keep long-running calls aligned with nginx timeouts and component AbortController/request budgets.
- For service URLs, prefer API-provided `public_url` when present and fallback to the dashboard host plus service port/path.
- If changing pages that manage extensions, models, settings, updates, Wi-Fi, or service restarts, verify backend auth and host-agent failure behavior as well as frontend state transitions.
