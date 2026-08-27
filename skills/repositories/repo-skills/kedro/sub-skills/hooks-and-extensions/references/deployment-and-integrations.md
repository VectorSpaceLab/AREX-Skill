# Deployment And Integrations

Use this reference when a Kedro extension touches notebooks/IPython, serving, orchestrators, Spark/cloud platforms, validation/tracking plugins, or deployment packaging. For exact server endpoint schemas and project snapshot APIs, route to `../inspection-and-server/SKILL.md`; for execution flags and runner choice, route to `../runners-and-execution/SKILL.md`.

## Notebook And IPython Extension Points

Kedro provides an IPython extension in `kedro.ipython`. Loading it registers line magics and, when a project is found, populates interactive variables:

```ipython
%load_ext kedro.ipython
%reload_kedro
```

After reload, the interactive namespace receives:

- `context`
- `catalog`
- `session`
- `pipelines`

`%reload_kedro` accepts a project path and selected options:

```ipython
%reload_kedro . --env=prod --params=threshold=0.82 --conf-source=conf
```

Use this when notebooks need current catalog, parameters, or pipeline registry values after config/code changes. If the extension cannot find a project, the expected guidance is to run `%reload_kedro <project_root>` from an explicit Kedro project root.

`%load_node <node_name>` is an experimental helper for Jupyter Notebook 7+, JupyterLab, IPython, and VS Code notebooks. It generates cells that load node inputs from `catalog`, import the node function dependencies, show the function body, and call the function. Requirements and caveats:

- The node must have a unique name.
- The node inputs must be persisted in the project catalog; in-memory-only inputs cannot be loaded into notebook cells.
- The command expects the node name, not the Python function name unless they are the same.
- If automatic cell creation is unavailable, Kedro prints the cells instead.

Plugins can add custom line magics with the `kedro.line_magic` entry point. These are registered during `reload_kedro()`.

```toml
[project.entry-points."kedro.line_magic"]
my_magic = "myplugin.magics:my_magic"
```

Keep notebook magics read-oriented or clearly flag side effects. If a magic starts servers, writes data, or contacts external services, include a dry-run or confirmation path.

## Minimal HTTP Serving

Kedro includes an optional FastAPI server for service-style integrations. Install optional dependencies before using it:

```bash
pip install 'kedro[server]'
```

Start from inside a Kedro project:

```bash
kedro server start --host 127.0.0.1 --port 8000
```

Useful options:

| Option | Use |
| --- | --- |
| `--host` / `-H` | Bind address; default is localhost. |
| `--port` / `-p` | Bind port; default is `8000`. |
| `--reload` | Development auto-reload only; do not use in production. |
| `--env` / `-e` | Configuration environment for server sessions. |
| `--conf-source` | Alternate configuration directory. |

The built-in app exposes `GET /health`, `GET /snapshot`, and `POST /run`. It is intentionally minimal: no authentication, no authorization, no request queue, no async job lifecycle, no run history, and no per-request session isolation. Do not expose it publicly without adding security controls.

Programmatic extension uses `create_http_server()`:

```python
from kedro.server import create_http_server

app = create_http_server(project_path=".", env="prod")


@app.get("/pipelines")
def list_pipelines() -> dict[str, list[str]]:
    from kedro.framework.project import pipelines
    return {"pipelines": list(pipelines.keys())}
```

When exposing `/run`, note that the first run request creates a `KedroServiceSession` and later requests reuse it. Concurrent requests share the session and are not isolated. Fully qualified custom runner names are restricted to `kedro.runner`, the project package, or modules listed in `RUNNER_MODULES_WHITELIST`.

## Serving Design Choices

Choose among these patterns:

| Need | Preferred surface |
| --- | --- |
| Read project metadata only | `kedro.inspection.get_project_snapshot()` or `GET /snapshot`; route details to `../inspection-and-server/SKILL.md`. |
| Local/manual triggering | `kedro run`, `KedroSession`, or `kedro server start` on localhost. |
| Multi-run service prototype | `KedroServiceSession` or `create_http_server()` with explicit security boundaries. |
| Production API | Wrap Kedro in your service framework, add auth/queueing/run isolation, and persist inputs/outputs. |
| Orchestrated production jobs | Package the project and use Airflow, Databricks Jobs, Kubeflow, Prefect, Argo, Vertex AI, SageMaker, AWS Batch, or similar platform tooling. |

## Deployment Integration Patterns

### Package First

Many orchestrator integrations expect an installable Kedro project package plus a deploy-specific configuration environment.

```bash
KEDRO_DISABLE_TELEMETRY=1 kedro package
```

`kedro package` builds distribution artifacts under `dist/` and archives project configuration while excluding local-only configuration. Packaging can require build tooling; route package setup issues to `../project-cli-and-sessions/SKILL.md`.

### Persist Intermediate Data

Orchestrators often execute each node in a separate process, task, job, or container. Replace `MemoryDataset` intermediates with catalog entries backed by persistent storage or use a plugin feature that groups memory-connected nodes into one task. For Airflow-style node-per-task execution, every dataset needed by a downstream task must be available outside the Python process that produced it.

### Use Environment-Specific Config

Create environment-specific config directories such as `conf/airflow`, `conf/databricks`, `conf/emr`, or `conf/prod` only in the user project. Keep credentials in secure stores or local/private config, not in generated runtime skill content. Run commands with `--env <env>` or `--conf-source <path>` where supported.

### Prefer Plugins For Platform Translation

Use platform plugins when they exist and fit the target:

- `kedro-airflow` converts Kedro pipelines into Airflow DAGs.
- `kedro-docker` packages Kedro projects for containers.
- `kedro-databricks` can produce production-grade Databricks deployment assets.
- Community plugins exist for Kubeflow, Vertex AI, SageMaker, Azure ML, Dagster, Prefect, MLflow, and other platforms.

Plugin commands may create files, start containers, contact cloud APIs, or upload artifacts. Ask before executing those commands and prefer `--help` or dry-run modes first.

## Platform Notes

### Airflow

Airflow integrations normally convert a Kedro pipeline into a DAG and execute nodes as Airflow tasks. Key constraints:

- Package the Kedro project so the Airflow environment can install it.
- Make intermediate data persistent; task-isolated `MemoryDataset` outputs are not shared.
- Use an Airflow-specific config environment when catalog paths or logging need platform changes.
- Keep requirements lean to avoid dependency conflicts in Airflow images.
- Cloud Airflow deployments usually require remote object storage for datasets and explicit credential management.

### Databricks

Databricks integrations usually follow one of three patterns:

- Run inside Databricks notebooks or Git folders and load Kedro with `%load_ext kedro.ipython` and `%reload_kedro`.
- Run locally while Spark executes remotely through Databricks Connect.
- Use a deployment plugin such as `kedro-databricks` for job-oriented production deployment.

Spark datasets often need remote paths such as Unity Catalog Volumes or cloud storage. Non-Spark local paths may not be visible to remote Spark executors. Databricks personal access tokens and workspace URLs are secrets; do not print or hard-code them.

### Dask And Custom Distributed Runners

A Dask-style custom runner subclasses `AbstractRunner`, uses Dask futures for node dependencies, and often creates a worker-side hook manager because Pluggy managers are not serializable. Design checks:

- Ensure node functions, datasets, and catalog objects are serializable or worker-accessible.
- Register or proxy hooks deliberately on workers if hook behavior must run there.
- Persist datasets through a shared scheduler, shared storage, or catalog-backed datasets.
- Close clients cleanly and propagate node errors back to the caller.

### Spark And PySpark

Spark integrations often combine `ThreadRunner`, Spark-aware datasets, and a Spark session created by project code or a plugin. Use Spark dataset types from `kedro-datasets` rather than assuming core Kedro bundles all concrete datasets. Check Spark, Python, pandas, and cluster runtime compatibility before blaming Kedro catalog syntax.

### Validation And Tracking Plugins

Great Expectations, Pandera, MLflow, StatsD, and similar integrations often fit naturally into hooks:

- Use `before_node_run` or `after_node_run` for input/output validation or tracking.
- Use `before_pipeline_run` and `after_pipeline_run` for run-level tracking lifecycle.
- Use `after_context_created` to inject external credentials into the config loader when needed.
- Avoid logging raw data, credentials, tokens, or personally identifiable information from hooks.

## Optional Dependency Notes

- `kedro[server]` installs server dependencies such as FastAPI, Pydantic support, and Uvicorn.
- Notebook workflows require IPython/Jupyter dependencies; `%load_node` in notebooks needs modern notebook front-end support.
- Most concrete dataset implementations live in `kedro-datasets` and may need backend extras such as `pandas`, `s3fs`, Spark libraries, `Pillow`, database drivers, or cloud SDKs.
- Platform plugins bring their own dependency and version constraints; check `kedro info`, plugin `--help`, and import errors before editing project code.

## Safety And Side Effects

- `kedro server start` opens a local HTTP server; binding to `0.0.0.0` exposes it to the network interface.
- `--reload` restarts on code changes and is development-only.
- Airflow, Databricks, cloud, Docker, and orchestration commands may create resources, start services, upload files, or use credentials.
- Use `KEDRO_DISABLE_TELEMETRY=1` or `DO_NOT_TRACK=1` for automated CLI probes when telemetry must be disabled.
- Never put cloud tokens, database passwords, or local absolute paths into reusable extension templates or public examples.
