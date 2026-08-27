---
name: dashboard-and-api
description: "Route ODS FastAPI dashboard API, React/Vite dashboard UI, API auth
  and session flows, route ownership, local dashboard development, and focused
  dashboard tests."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Dashboard And API

Use this sub-skill when the task touches the ODS dashboard FastAPI backend, React/Vite dashboard frontend, dashboard API authentication, owner-session and magic-link flows, API route ownership, or dashboard-focused tests.

## First Moves

1. Read [references/api-reference.md](references/api-reference.md) before changing FastAPI routers, endpoint auth, response payloads, settings/session flows, or dashboard-api environment handling.
2. Read [references/frontend-workflows.md](references/frontend-workflows.md) before changing Vite, React routes, dashboard pages/components/hooks, nginx proxy behavior, or frontend tests.
3. Read [references/troubleshooting.md](references/troubleshooting.md) when diagnosing 401/403 auth failures, 502s, missing host-agent access, stale container code, port conflicts, session-cookie issues, or dashboard dev workflow surprises.
4. Use the bundled read-only route lister when reviewing API ownership or route drift:

```bash
python3 sub-skills/dashboard-and-api/scripts/list_dashboard_api_routes.py \
  --api-dir <ODS checkout>/ods/extensions/services/dashboard-api
```

The script imports the supplied dashboard-api source tree and prints FastAPI routes. Importing dashboard-api initializes module-level config from environment variables, so set the same safe env values your task needs before running it.

## Route Here For

- FastAPI app wiring, lifespan/background polling, CORS, API auth, settings endpoints, service status, storage, readiness, and preflight routes.
- Dashboard API router modules for workflows, features, setup wizard, updates, agents, privacy, extensions portal endpoints, GPU detail/history, resources/restarts, model library lifecycle, remote-provider status, templates, auth/session, magic links, OAuth passthrough, ODS Talk, Tailscale, usage, and node capabilities.
- React/Vite dashboard pages, hooks, components, plugin route registry, first-boot flow, ODS Talk UI, Settings, Models, Extensions, Remote GPU, Usage, Invites, Service Map, and dashboard route tests.
- Dashboard production proxy behavior: dashboard nginx on port 3001 proxying `/api/*` to dashboard-api on port 3002 and injecting `Authorization: Bearer <dashboard-api-key>`.
- Local dashboard development, especially the native uvicorn plus Vite workflow and the baked-container code trap.

## Route Elsewhere

- Service manifest schema, compose extension semantics, extension catalog design, and compose security rules: use `../services-and-extensions/SKILL.md`.
- GPU backend detection internals, model catalog/tier selection, inference backend contracts, and model runtime internals: use `../hardware-and-models/SKILL.md`.
- Operator CLI lifecycle commands, host-agent implementation internals, doctor/support bundle depth, backup/restore, and memory shepherd: use `../ops-cli-and-host-tools/SKILL.md`.
- Test lane selection across multiple repo areas, CI matrix interpretation, release gates, and full validation planning: use `../testing-and-release/SKILL.md`.

## Safety Rules

- Do not weaken `verify_api_key` or remove Bearer auth from protected routes to make a local UI test pass. Production relies on nginx injecting the admin Bearer token; direct API calls must provide the header explicitly.
- Treat host-agent-backed endpoints as mutating or host-observing unless proven otherwise. Settings apply, extension install/enable/disable/update/rollback, model download/load/delete, service restart, Wi-Fi setup, and update actions can change the installed system.
- Do not assume host edits under the dashboard-api source tree affect a running `ods-dashboard-api` container. The image bakes Python files into `/app`; run native uvicorn for hot reload or rebuild/copy into the container intentionally.
- Keep dashboard UI and API instructions self-contained. Source repo paths named here are evidence/provenance; future usage should rely on this bundled skill content, bundled scripts, and explicit public commands.
- Do not expose API keys, session cookies, magic-link tokens, OAuth codes, host-agent keys, local absolute checkout paths, private environment names, or generated logs in user-facing output.

## Verification Shortlist

Safe first-pass checks for dashboard/API work:

```bash
# Static route ownership check supplied by this skill.
python3 sub-skills/dashboard-and-api/scripts/list_dashboard_api_routes.py \
  --api-dir <ODS checkout>/ods/extensions/services/dashboard-api

# Native source-check candidates when an ODS checkout and dependencies are available.
cd <ODS checkout>/ods/extensions/services/dashboard-api
pytest tests/test_routers.py -q
pytest tests/test_auth_router.py -q
pytest tests/test_main.py -q
pytest tests/test_settings_env.py -q

cd <ODS checkout>/ods/extensions/services/dashboard
npm run test -- --run src/lib/serviceUrls.test.js
npm run test -- --run src/App.test.jsx
npm run test -- --run src/pages/Settings.test.jsx
npm run build
```

Choose narrower tests for focused changes. Run host-mutating dashboard endpoints or full Docker workflows only after confirming user intent and host impact.
