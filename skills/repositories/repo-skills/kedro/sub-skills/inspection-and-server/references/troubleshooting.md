# Inspection And Server Troubleshooting

Use this reference when inspection snapshots or the optional HTTP server fail, return unexpected fields, or blur into execution behavior.

## Quick Triage

1. Confirm Kedro itself imports: `python -c "import kedro; print(kedro.__version__)"`.
2. For CLI probes, disable telemetry in automation: `KEDRO_DISABLE_TELEMETRY=1 kedro --version`.
3. For inspection, confirm the project root is the directory containing `pyproject.toml` with Kedro metadata.
4. For server tasks, confirm optional dependencies are installed with `pip install 'kedro[server]'` in the active environment.
5. Decide whether the task is read-only. If yes, use `get_project_snapshot()` or `GET /snapshot`; do not use `kedro run` or `POST /run`.

## Import Or Optional Dependency Errors

Signals:

- `ImportError` or CLI error mentioning `fastapi`, `pydantic`, or `uvicorn` when starting the server.
- `ModuleNotFoundError` while importing `kedro.server.models` or constructing the FastAPI app.
- Base Kedro commands work, but `kedro server start` fails.

Fixes:

- Install the server extra in the same environment that runs the command: `pip install 'kedro[server]'`.
- If only pydantic model support is needed, install Kedro's pydantic extra or the server extra.
- Do not treat a missing server extra as a Kedro project error; the inspection Python API can still work without FastAPI/Uvicorn.

## Project Path And Bootstrap Failures

Signals:

- `ValueError: Either project_path or metadata must be provided` from snapshot construction.
- `ServerSettingsError` saying `KEDRO_PROJECT_PATH` is not set or the project path does not exist.
- CLI project commands are unavailable or Kedro cannot locate project metadata.

Fixes:

- Pass `project_path` explicitly to `get_project_snapshot(project_path=".")` or pass `metadata=bootstrap_project(project_root)`.
- Start `kedro server start` from inside a Kedro project, or use `create_http_server(project_path="...")` programmatically.
- Route project detection, `pyproject.toml`, `bootstrap_project()`, and CLI command availability problems to `../project-cli-and-sessions/SKILL.md`.

## Invalid Environment Or Config Source

Signals:

- `ValueError` mentioning an invalid `env` value.
- Snapshot or server startup fails after `--env`, `KEDRO_SERVER_ENV`, or `conf_source` changes.
- `/snapshot` keeps using an unexpected environment.

Fixes:

- Use only letters, digits, hyphens, and underscores in `env` names, for example `local`, `staging`, or `prod_1`.
- For programmatic inspection, pass `env=` and `conf_source=` directly to `get_project_snapshot()`.
- For HTTP snapshots, set `--env` and `--conf-source` when the server starts; `/snapshot` does not accept per-request environment overrides.
- If starting through the CLI, omitted `--env` and `--conf-source` clear stale server env vars for that invocation; with programmatic use, factory arguments override env vars.

## Empty Or Unexpected Snapshot Content

Signals:

- `snapshot.datasets` is empty even though nodes reference datasets.
- `snapshot.parameters` is empty.
- A pipeline is missing from `snapshot.pipelines`.
- Dataset paths are redacted or incomplete.

Explanations and fixes:

- Missing catalog configuration is represented as an empty `datasets` mapping; validate catalog config in `../data-catalog-and-config/SKILL.md` if this is unexpected.
- Only dictionary catalog entries that are not private helper entries are converted into `DatasetSnapshot` objects.
- Dataset factory patterns are expanded only for concrete dataset names referenced by pipeline node inputs or outputs.
- Datasets referenced by nodes but not present in catalog config and not resolved by factories are not included in `snapshot.datasets`.
- Parameter values are intentionally omitted; only sorted top-level parameter keys are returned.
- Pipeline registry entries with `None` values are skipped; route registry design to `../pipelines-and-nodes/SKILL.md`.
- URI credentials in dataset file paths are redacted as `<redacted>`; do not try to recover or print secret values.

## Snapshot Endpoint Failures

Signals:

- `GET /snapshot` returns HTTP 200 with `{"status": "failure", "error": ...}`.
- Failure response has no `metadata`, `pipelines`, `datasets`, or `parameters` fields.

Fixes:

- Treat failure status as the real error signal; HTTP 200 only means the server handled the request.
- Inspect `error.type` and `error.message`, then route by cause: config/catalog errors to `../data-catalog-and-config/SKILL.md`, pipeline registry import errors to `../pipelines-and-nodes/SKILL.md`, project bootstrap errors to `../project-cli-and-sessions/SKILL.md`.
- If environment-specific config is the issue, restart the server with the correct `--env` or `--conf-source`; do not add `env` or `conf_source` fields to the request.

## Server Startup And Runtime Issues

Signals:

- `kedro server start --reload` warns about development-only use.
- Port already in use, wrong bind host, or long-running command blocks the shell.
- `GET /health` works but `GET /snapshot` fails.
- Server starts with a warning about a custom `SESSION_CLASS`.

Fixes:

- Use `--host 127.0.0.1` and an available `--port` for local diagnostics.
- Use `--reload` only for development; avoid it for production or shared environments.
- `GET /health` proves the FastAPI app is alive, not that project config and pipelines are valid.
- The built-in HTTP server is designed around `KedroServiceSession`; custom session classes may not be used by the server.
- Stop the long-running Uvicorn process when finished; do not leave an unauthenticated server exposed.

## Run Endpoint Mistaken For Inspection

Signals:

- A read-only request proposes `POST /run`, `kedro run`, or `KedroSession.run()`.
- The request body contains `params`, `runner`, `only_missing_outputs`, or slicing fields for what should be a structure summary.

Fixes:

- Use `get_project_snapshot()` or `GET /snapshot` for structure-only tasks.
- Route explicit execution requests to `../runners-and-execution/SKILL.md`.
- Warn that `/run` executes project code, can load/save datasets, and reuses a server-side `KedroServiceSession` across requests.

## Run Endpoint Validation And Runner Errors

Signals:

- Pydantic validation rejects extra fields or invalid runner strings.
- Response has `status: failure` with errors mentioning `AbstractRunner`, unknown runner, or module not allowed.
- `env` or `conf_source` fields sent in the JSON body are rejected.

Fixes:

- Remove unknown fields; `RunRequest` forbids extras.
- Use valid dotted identifiers for runners, for example `SequentialRunner`, `ParallelRunner`, `kedro.runner.SequentialRunner`, or a project package runner.
- Fully qualified custom runner modules must be in `kedro.runner`, the project package, a project subpackage, or a module prefix in `RUNNER_MODULES_WHITELIST`.
- The loaded runner must be a class and subclass `kedro.runner.AbstractRunner`.
- Set `env` and `conf_source` at server startup, not per `/run` request.

## Security Checklist

- Keep the built-in server on localhost unless a hardened deployment wrapper is in place.
- Add authentication, authorization, input validation, request isolation, logging policy, and network controls before exposing the server beyond local development.
- Never print credential config, environment variables, access tokens, or parameter values while summarizing snapshots.
- Treat `conf_source`, remote catalog paths, custom runner modules, and project imports as trusted-code boundaries.
- Use `KEDRO_DISABLE_TELEMETRY=1` or `DO_NOT_TRACK=1` for automated CLI probes when telemetry must be disabled.
