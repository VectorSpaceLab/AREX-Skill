---
name: server
description: "Routes LabML app-server, FastAPI/MongoDB backend, analysis
  endpoints, settings, and deployment workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Server

Use this subskill for `labml_app`: the monitoring app backend, server settings,
analysis/data endpoints, MongoDB-backed models, and deployment/startup issues.

## Use this when

- The task mentions `labml_app`, `labml app-server`, FastAPI, MongoDB, custom
  metrics, data stores, analysis endpoints, logs, run status, or app server
  startup.
- The user wants to self-host or troubleshoot the monitoring web app.
- The user needs to understand server-side models or route registration.

## Boundaries

Include:
- App server startup, settings, static frontend asset checks, MongoDB setup, and
  FastAPI route registration.
- Analysis models such as metrics, logs, preferences, custom metrics, data
  stores, and computer metrics.
- Deployment notes, including reverse proxy and local startup caveats.

Exclude or route elsewhere:
- Client-side experiment logging and `AppAPI` usage → `tracking`.
- Remote server SSH/rsync orchestration → `remote`.
- Training helper abstractions → `helpers`.

## Read next

- `references/api-reference.md` for server entry points, route groups, and data
  models.
- `references/configuration.md` for settings, analysis registries, static
  assets, and MongoDB requirements.
- `references/workflows.md` for local app-server startup and deployment flow.
- `references/troubleshooting.md` for missing settings, missing static assets,
  MongoDB failures, and route errors.
- `scripts/server_smoke.py` for a safe route/series/static-assets preview that
  does not start MongoDB or the full server.

## Fail-fast before a real server

`scripts/server_smoke.py` is deliberately a stub-based analysis check: it
injects settings, does not start FastAPI/uvicorn, and does not connect to
MongoDB. Its exit status must never be reported as a real-server PASS. Use
`--require-server-prereqs` when missing settings or static assets should fail
the check.

Before `labml app-server`, stop and fix each prerequisite:

1. Create/configure `labml_app/settings.py` and
   `labml_app/analyses_settings.py` from their `*.sample.py` files.
2. Build frontend assets with `npm install && npm run build` in `app/ui`, or
   install a published package that includes its static directory.
3. Start MongoDB and verify `MONGO_HOST` (or localhost) on port `27017`.

Run `python scripts/server_smoke.py --require-server-prereqs` and
`python scripts/check_labml_stack.py --check-server` for file-level checks;
neither command probes MongoDB or validates the running API.

## Typical routes

### Start the app server
Choose this route for `labml app-server --ip ... --port ...`, `labml_app.start_server`,
`gunicorn`, `uvicorn`, and local UI startup issues.

### Inspect analysis endpoints
Choose this route for metrics, custom metrics, logs, preferences, data stores,
and run status endpoints.

### Fix server configuration
Choose this route for missing settings modules, static frontend assets, MongoDB
host/port, or reverse-proxy setup.
