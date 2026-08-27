# Tracking and Registry Troubleshooting

## Tracking URI vs Registry URI

Symptoms:

- Runs are visible in one backend but registry operations query another.
- `MlflowClient()` works for tracking but registry methods fail or target Unity Catalog unexpectedly.
- Databricks tracking defaults registry operations to `databricks-uc`.

Checks:

```python
import mlflow
from mlflow import MlflowClient

print("tracking", mlflow.get_tracking_uri())
print("registry", mlflow.get_registry_uri())
client = MlflowClient()
print("client tracking", client.tracking_uri)
```

Fixes:

- Set both URIs explicitly before creating clients: `mlflow.set_tracking_uri(...)` and `mlflow.set_registry_uri(...)`.
- For one-off clients, pass `MlflowClient(tracking_uri=..., registry_uri=...)`.
- For Databricks workspace registry instead of Unity Catalog, set an explicit registry URI and verify that the target backend supports the methods you need.

## No Active Run or Wrong Run

Symptoms:

- A metric or artifact appears under a new unexpected run.
- Client-created runs stay empty after fluent `mlflow.log_*` calls.
- A run remains `RUNNING` because client CRUD did not end it.

Fixes:

- Prefer `with mlflow.start_run() as run:` around fluent logging.
- If using `MlflowClient.create_run()`, use `client.log_param`, `client.log_metric`, `client.log_artifact`, and `client.set_terminated(run_id)`.
- To resume a run for fluent logging, use `with mlflow.start_run(run_id=run_id): ...`.
- Print `mlflow.active_run().info.run_id` before logging when repairing mixed fluent/client code.

## Nested Run Errors

Symptoms:

- Error says a run is already active and suggests `nested=True`.
- Child runs do not show as children in search results.
- `parent_run_id` fails because the parent is not active or valid.

Fixes:

- Use `with` blocks so active-run stack state is balanced.
- For immediate child runs under the current run, pass `nested=True`.
- For an explicit parent, pass `parent_run_id=<active_parent_run_id>` and verify the parent run exists and is active.
- Search children with `tags.mlflow.parentRunId = '<parent_run_id>'`.

## Async Logging and Read-After-Write

Symptoms:

- Search or `get_run` immediately after logging misses params, metrics, or tags.
- Process exits before asynchronous logging finishes.
- Tests are flaky with `synchronous=False` or `MLFLOW_ENABLE_ASYNC_LOGGING`.

Fixes:

- Use `synchronous=True` in tests, smoke scripts, and critical read-after-write paths.
- If a logging call returns `RunOperations`, call `.wait()` before reading or exiting.
- Clear or set `MLFLOW_ENABLE_ASYNC_LOGGING` deliberately in test environments.

## Artifact Path Mistakes

Symptoms:

- Artifacts upload but appear under unexpected nested paths.
- `download_artifacts` cannot find a file.
- A local path was used as `artifact_path`.

Fixes:

- Treat `artifact_path` as a logical run-relative directory, for example `reports`, not as a filesystem destination.
- Avoid leading `/` in artifact paths.
- Use `client.list_artifacts(run_id, None)` and then drill down: `client.list_artifacts(run_id, "reports")`.
- Print `mlflow.get_artifact_uri()` inside the run to see the resolved artifact root.

## Registry Backend Support

Symptoms:

- `Model Registry features are not supported by the store with URI ...`.
- Registry UI/API unavailable when running a self-hosted tracking server.
- Local experiments work but model version operations fail.

Fixes:

- For self-hosted registry workflows, configure a database-backed backend store such as SQLite, PostgreSQL, MySQL, or MSSQL.
- For local scripts, set both tracking and registry to the same SQLite URI when testing registry metadata.
- If using a file-backed local store for smoke tests, do not assume that behavior maps to a production tracking server registry configuration.
- Confirm the registry URI scheme is supported before calling registry methods.

## Model URI and Registration Failures

Symptoms:

- `register_model` cannot find `runs:/.../model`.
- Registering from a run path chooses the wrong model checkpoint or asks for `models:/<model_id>`.
- `models:/Name@alias` cannot be resolved.

Fixes:

- Confirm the flavor logging call wrote the model under the expected artifact path; model flavor details belong in `models-and-flavors`.
- Prefer the returned `model_info.model_uri` or `models:/<model_id>` from MLflow 3 model logging when multiple logged models exist in a run.
- After setting aliases, use `MlflowClient.get_model_version_by_alias(name, alias)` to verify the alias target.
- Avoid alias names such as `v1` or `v42`; version-like aliases are reserved.

## Search Filter Syntax

Symptoms:

- Search returns no rows despite visible runs.
- Search raises parse or invalid parameter errors.
- Case-sensitive filters miss expected tags or model names.

Fixes:

- Quote string values: `params.model = 'rf'`, `tags.owner = 'risk'`.
- Use `ILIKE` for case-insensitive matching where supported.
- Use proper prefixes: `metrics.`, `params.`, `tags.`, and supported attributes for the target search API.
- Do not mix fluent `search_runs(experiment_ids=..., experiment_names=...)` in the same call.
- For client search, pass experiment IDs as a list or single ID and page with `page_token` when needed.

## SQLite and Legacy File Store Limits

Symptoms:

- Concurrent writers hit SQLite locking.
- A filesystem tracking backend raises a maintenance-mode error unless `MLFLOW_ALLOW_FILE_STORE=true` is deliberately set.
- A legacy file-store smoke test passes but server-backed registry behavior differs.
- Relative paths create `mlruns` or database files in surprising working directories.

Fixes:

- Use absolute paths for SQLite tracking URIs in tests and scripts.
- Keep SQLite for local development and small workflows; use a production database for shared tracking servers.
- Do not use local file-backed tracking as proof of remote artifact-store or registry-server behavior; prefer SQLite for local MLflow 3 smoke tests.
- Clean up temp tracking directories only after async logging has completed.

## Workspace-Aware Store Plumbing

Symptoms:

- Runs, experiments, models, or registry entries leak across workspaces.
- Tests pass for single-tenant stores but fail in workspace-aware variants.
- Request headers or workspace context are ignored.

Fixes:

- Preserve workspace-aware classes and request-context plumbing when touching `mlflow/store/tracking` or `mlflow/store/model_registry` code.
- Check SQLAlchemy workspace tests when changing tracking store query, CRUD, validation, or search behavior.
- Do not remove workspace columns, filters, or default workspace handling from model registry or tracking store paths.

## Databricks and Cloud Credentials

Symptoms:

- Databricks URI fails with missing host/token or auth errors.
- Unity Catalog model registration fails because of permissions, model name format, or missing signatures.
- Tracking works locally but remote artifact access fails.

Fixes:

- Configure credentials through supported environment variables, profiles, or platform auth; never embed tokens in code.
- Use `mlflow.set_tracking_uri("databricks")` and `mlflow.set_registry_uri("databricks-uc")` deliberately for UC workflows.
- For Unity Catalog, verify catalog/schema/model naming and required model signatures in the model-flavor workflow.
- Separate credential failures from MLflow API misuse by first running a local smoke script, then a minimal remote list/search call.
