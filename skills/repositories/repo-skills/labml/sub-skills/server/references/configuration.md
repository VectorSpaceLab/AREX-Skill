# Server Configuration

## Purpose

Read this before starting or troubleshooting the LabML monitoring app backend.

## Settings values

The app server expects settings equivalent to these public sample fields:

| Setting | Meaning |
| --- | --- |
| `PORT` | Server port, default sample value `5005`. |
| `SERVER_URL` | Backend URL used by the server. |
| `WEB_URL` | Web URL allowed by CORS. |
| `SLACK_BOT_TOKEN` / `SLACK_CHANNEL` | Optional notification settings. |
| `SENTRY_DSN` | Optional error reporting DSN. |
| `FLOAT_PROJECT_TOKEN` | Token for the float/default project. |
| `SAMPLES_PROJECT_TOKEN` | Token for sample project data. |
| `LABML_VERSION` | Expected client package version. |
| `IS_LOCAL_SETUP` | Whether this is a local deployment. |
| `INDICATOR_LIMIT` | Maximum number of metric indicators tracked. |
| `IS_DEBUG` | Debug logging flag. |
| `LOG_CHAR_LIMIT` | Maximum log chunk size. |
| `APP_API_VERSION` | App API version checked by the client. |
| `DB_NAME` | MongoDB database name. |

## Analysis registry

The analysis settings file lists the experiment and computer analyses that are
loaded into `AnalysisManager`.

Typical experiment analysis:
- `MetricsAnalysis`

Typical computer analyses:
- `CPUAnalysis`
- `GPUAnalysis`
- `MemoryAnalysis`
- `NetworkAnalysis`
- `DiskAnalysis`
- `ProcessAnalysis`

## MongoDB requirement

`init_mongo_db(mongo_address='', port=27017)` connects to MongoDB. If
`mongo_address` is not passed, the server checks `MONGO_HOST` and otherwise uses
`localhost`.

A connection failure means MongoDB is missing, stopped, or unreachable at the
configured host/port.

## Static frontend assets

The full FastAPI app imports `flask_app.py`, which tries to locate static files
under the packaged app layout. If the static folder is absent in a source
checkout, importing the full app can fail before route inspection.

Use one of these paths:

- Install a published `labml-app` package with bundled static assets.
- Build the UI assets before starting the app from source.
- Use the server smoke script when you only need safe backend logic inspection.

## Fail-fast preflight (not a server start)

Run the bundled checker before attempting a deployment:

```bash
python sub-skills/server/scripts/server_smoke.py --require-server-prereqs
python scripts/check_labml_stack.py --check-server
```

Both commands inspect files only. They must report real `settings.py` and
`analyses_settings.py` modules plus a static directory before the full server is
attempted. If settings are absent, copy the two `*.sample.py` files beside the
package modules and configure the values above. If static assets are absent,
run `npm install && npm run build` in `app/ui` or install a published package
that actually contains them. The smoke script's injected settings are a test
stub and do not satisfy this preflight.

The preflight deliberately does not connect to MongoDB. Before running
`labml app-server`, start MongoDB and verify `MONGO_HOST` (or localhost) and
port `27017`; a successful smoke/preflight result never means the database or
the real FastAPI server is healthy.

## Reverse proxy notes

When deploying behind Nginx, forward to the local app port and set the usual
proxy headers: `Host`, `X-Real-IP`, and `X-Forwarded-For`. Restart Nginx after
linking the site configuration.
