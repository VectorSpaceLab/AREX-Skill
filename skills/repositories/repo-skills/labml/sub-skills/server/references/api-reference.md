# Server API Reference

## Purpose

Read this for verified app-server entry points, route groups, and analysis data
objects.

## Startup entry points

| Object | Signature | Use |
| --- | --- | --- |
| `labml_app.start_server` | `(ip: str, port: int)` | Launch the app backend through gunicorn and uvicorn. |
| `labml_app.db.init_mongo_db` | `(mongo_address: str = '', port: int = 27017)` | Connect models and indexes to MongoDB and initialize default projects. |
| `labml_app.handlers.add_handlers` | `(app: FastAPI)` | Register the app API routes on a FastAPI instance. |

The client command `labml app-server --ip IP --port PORT` delegates into
`labml_app.start_server`.

## Core analysis objects

| Object | Signature | Use |
| --- | --- | --- |
| `Series` | `__init__(max_buffer_length=None, keep_last_24h=False)` | Incrementally merge and summarize numeric series. |
| `Series.update` | `(step: List[float], value: List[float]) -> None` | Add new points to a series. |
| `Series.load` | `(data)` | Restore a stored series dictionary. |
| `SeriesCollection.track` | `(data, keep_last_24h=False) -> int` | Update named series and return the latest step. |
| `Preferences.update_preferences` | `(data)` | Update analysis preferences from a JSON-like dictionary. |
| `Logs.get_data` | `(page_no=-1)` | Fetch one, all, or the last log pages. |
| `MetricsAnalysis.track` | `(data, run_uuid=None) -> int` | Update tracked metric series for a run. |
| `MetricsAnalysis.get_tracking` | `()` | Return metric series for UI consumption. |
| `get_metrics_tracking_util` | `(track_data, indicators)` | Build full or summary metric payloads. |

## Route registration groups

`handlers.add_handlers(app)` registers these high-level groups:

- Server ingest: run tracking and computer monitoring packets.
- App init and version checks.
- Runs and sessions: list, get, edit, add, claim, delete, and status.
- Computer status.
- User/session authentication.
- Analysis routes contributed by `Analysis.route(...)` decorators.

## Analysis plugin mechanism

`Analysis` exposes decorators used by analysis modules:

- `Analysis.route(method, url, login_required=False)` registers a FastAPI route.
- `Analysis.db_model(serializer, path)` registers a persistent model.
- `Analysis.db_index(serializer, path)` registers an index.

`AnalysisManager` then provides:

- `track(run_uuid, data)` for experiment analysis updates.
- `track_computer(session_uuid, data)` for hardware analysis updates.
- `delete_run(run_uuid)` and `delete_session(session_uuid)` cleanup.
- `get_handlers()`, `get_db_models()`, and `get_db_indexes()` for app setup.

## Data-store endpoints

The data-store analysis exposes:

- `GET datastore/{run_uuid}`: returns a YAML string and dictionary.
- `POST datastore/{run_uuid}`: accepts a YAML string and updates the run's data
  store.

Invalid YAML or an empty dictionary produces an error response.

## Important runtime constraint

The server package may need a `labml_app.settings` module and static frontend
assets. If those are absent in a source checkout, use the server smoke script to
inspect route/model logic without starting the full app.
