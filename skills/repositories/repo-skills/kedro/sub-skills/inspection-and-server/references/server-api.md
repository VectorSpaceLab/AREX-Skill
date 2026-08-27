# Server API

Use this reference when the task involves the optional Kedro HTTP server, `kedro server start`, `create_http_server()`, `GET /snapshot`, or diagnosing server request/response behavior. Treat the server as optional and potentially run-capable; prefer the programmatic inspection API for purely local read-only summaries.

## Optional Dependencies

The base `kedro` install may not include the server stack. The `server` optional extra installs FastAPI and Uvicorn and depends on Kedro's pydantic support:

```bash
pip install 'kedro[server]'
```

If `kedro server start` fails with a message that FastAPI, pydantic, or Uvicorn is required, install the `server` extra in the target environment. If code imports `kedro.server.models` directly, pydantic support must also be available.

## CLI Start Command

Run from inside a Kedro project:

```bash
KEDRO_DISABLE_TELEMETRY=1 kedro server start --host 127.0.0.1 --port 8000
```

Useful options:

- `--host` or `-H`: bind host; default is `127.0.0.1`.
- `--port` or `-p`: bind port; default is `8000`.
- `--reload`: enables Uvicorn reload for development only; do not use in production.
- `--env` or `-e`: Kedro configuration environment used by server sessions and `/snapshot`.
- `--conf-source`: custom configuration directory used by server sessions and `/snapshot`.

The CLI sets `KEDRO_PROJECT_PATH` from the project metadata path. It also clears stale `KEDRO_SERVER_ENV` and `KEDRO_SERVER_CONF_SOURCE` values when the corresponding options are omitted, so a previous server invocation does not silently affect the next one.

## Programmatic Factory

Create a FastAPI app with:

```python
from kedro.server import create_http_server

app = create_http_server(project_path=".", env="local", conf_source="conf")
```

Factory arguments take precedence over environment variables. If `project_path` is omitted, the factory resolves it from `KEDRO_PROJECT_PATH`. `env` and `conf_source` can also come from `KEDRO_SERVER_ENV` and `KEDRO_SERVER_CONF_SOURCE`.

The app bootstraps the Kedro project during FastAPI lifespan startup and stores metadata on app state. On shutdown, it closes a reused service session if one was created by `/run`.

## Endpoints

### `GET /health`

Returns HTTP 200 with:

```json
{
  "status": "healthy",
  "kedro_version": "<installed-kedro-version>"
}
```

`kedro_version` is the running Kedro package version, not the project metadata version.

### `GET /snapshot`

Read-only endpoint that returns the same structural fields as `ProjectSnapshot`, serialized as JSON:

```json
{
  "status": "success",
  "metadata": {
    "project_name": "My Project",
    "package_name": "my_project",
    "kedro_version": "1.0.0"
  },
  "pipelines": [
    {
      "name": "__default__",
      "nodes": [
        {
          "name": "split_data_node",
          "namespace": null,
          "tags": [],
          "inputs": ["raw_data"],
          "outputs": ["train_data", "test_data"]
        }
      ],
      "inputs": ["raw_data"],
      "outputs": ["test_data", "train_data"]
    }
  ],
  "datasets": {
    "raw_data": {
      "name": "raw_data",
      "type": "pandas.CSVDataset",
      "filepath": "data/01_raw/raw.csv"
    }
  },
  "parameters": ["model_options"]
}
```

If snapshot construction raises, the endpoint still returns HTTP 200 with failure status and no data fields:

```json
{
  "status": "failure",
  "error": {
    "type": "RuntimeError",
    "message": "project not found"
  }
}
```

The endpoint calls `get_project_snapshot(env=<server env>, conf_source=<server conf_source>, metadata=<startup metadata>)`. It does not accept per-request `env` or `conf_source`; use the Python inspection API for multi-environment comparison.

### `POST /run`

This endpoint executes a Kedro pipeline. Do not use it for read-only inspection. Route full execution guidance to `../runners-and-execution/SKILL.md`.

Accepted `RunRequest` fields include:

- `pipeline_names`: list of registered pipeline names.
- `tags`, `node_names`, `from_nodes`, `to_nodes`, `from_inputs`, `to_outputs`, and `namespaces`: run slicing fields.
- `runner`: runner class short name or dotted path; default is `SequentialRunner`.
- `is_async`: load/save node inputs and outputs asynchronously with threads.
- `load_versions`: dataset load-version mapping.
- `params`: runtime parameters.
- `only_missing_outputs`: skip nodes whose persistent outputs already exist.

The pydantic model forbids unknown fields. `env` and `conf_source` are not accepted per request; set them at server startup.

A successful response contains `status`, `run_id`, and `duration_ms`. A failed run response contains the same plus `error.type` and `error.message`; tracebacks are not returned in the response.

## Runner Security And Validation

Runner strings must be valid Python dotted identifiers such as `SequentialRunner`, `kedro.runner.SequentialRunner`, or `my_project.runners.CustomRunner`. Obvious code-injection strings, paths, empty strings, spaces, and invalid identifiers are rejected by request validation.

Execution then applies additional checks:

- Short runner names resolve against `kedro.runner`.
- Dotted runner modules must be `kedro.runner`, the project package, a project subpackage, or a module prefix listed in `RUNNER_MODULES_WHITELIST` in `settings.py`.
- The loaded object must be a class and a subclass of `kedro.runner.AbstractRunner`.
- Disallowed modules are rejected before importing the requested runner.

## Session And Concurrency Notes

The first `/run` request creates a `KedroServiceSession`; later `/run` requests reuse it. Requests share server process state and are not isolated per request. The built-in server does not provide request queues, run history, authentication, authorization, or public-network hardening.

## Security Boundary

The built-in server is intentionally minimal. Keep it bound to `127.0.0.1` for local diagnostics unless the user explicitly accepts the risks and adds appropriate controls. Do not expose `/run` publicly without authentication, authorization, request isolation, input validation, network controls, and secret handling. Use `GET /snapshot` rather than `/run` when the user asks only for project structure.
