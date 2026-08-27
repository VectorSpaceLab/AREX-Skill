# Server Workflows

## Purpose

Read this for app-server startup, backend inspection, and deployment patterns.

## 1) Start a local monitoring app

1. Install `labml-app` together with `labml`.
2. Make sure MongoDB is installed and running.
3. Start the server through the client CLI:

```bash
labml app-server --port 5005
```

4. Point clients at the app URL through `.labml.yaml`, `lab.configure`, or the
   `app_url` argument to `experiment.record`.
5. Open the UI URL from the startup output or browser.

## 2) Inspect backend routes without starting the full server

If the source checkout lacks settings or static assets, do not import the full
`flask_app` module first. Instead:

- Run `python scripts/server_smoke.py` only for the explicitly stubbed,
  MongoDB-free analysis check. Its zero exit status is **not** a real-server
  pass.
- Use `python scripts/server_smoke.py --require-server-prereqs` to fail fast
  when settings or static assets are missing.
- Inspect analysis classes such as `Series`, `MetricsAnalysis`, and
  `Preferences`, or use route decorator metadata to understand registration.

Before `labml app-server`, provide both settings modules, packaged static
assets, and a reachable MongoDB instance; the smoke script deliberately does
none of those things.

## 3) Work with series and metrics

- Use `Series.update(step, value)` to merge new numeric points.
- Use `Series.to_data()` and `Series.load(data)` to persist and reload state.
- Use `MetricsAnalysis.track(data, run_uuid)` to update metrics for a run.
- Use `get_metrics_tracking_util(track_data, indicators)` when preparing a UI
  payload with full or summary series.

## 4) Work with data stores

The app exposes a run-level data store as YAML plus a dictionary.

- `GET datastore/{run_uuid}` returns the stored dictionary.
- `POST datastore/{run_uuid}` accepts a YAML string.
- Empty YAML or invalid YAML should produce explicit error responses.

## 5) Deploy behind Nginx

Use Nginx only after the app works locally.

1. Install and start Nginx.
2. Configure a server block that proxies `/` to `http://127.0.0.1:<port>`.
3. Forward `Host`, `X-Real-IP`, and `X-Forwarded-For` headers.
4. Link the config into `sites-enabled` and restart Nginx.

## 6) When to use the smoke script

Use `scripts/server_smoke.py` only for the stubbed series/log/preferences
inspection. It avoids MongoDB and long-running app startup, so it is suitable
for source-level debugging, but it cannot validate settings, static serving,
database connectivity, or a real FastAPI deployment. Run the real
`labml app-server` only after the fail-fast preflight and MongoDB checks pass.
