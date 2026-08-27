# Tracking and Registry API Reference

## Tracking Configuration

- `mlflow.set_tracking_uri(uri)` accepts an empty string, local path or `file:/` URI, HTTP(S) tracking server URI, Databricks URI such as `databricks` or `databricks://profile`, and `pathlib.Path` values. It updates `MLFLOW_TRACKING_URI` for subprocesses and affects future operations, not an already-active run.
- `mlflow.get_tracking_uri()` returns the resolved tracking URI. With no explicit configuration, local tracking writes under `mlruns`.
- `mlflow.set_registry_uri(uri)` and `mlflow.get_registry_uri()` configure model registry independently. If unset, the registry URI resolves from the tracking URI; for Databricks tracking URIs it defaults to Unity Catalog style registry URIs such as `databricks-uc` or `databricks-uc://profile`.
- `mlflow.MlflowClient(tracking_uri=None, registry_uri=None, workspace_store_uri=None)` is a unified client over tracking, model registry, and workspace provider operations. `workspace_store_uri` resolves separately but defaults to the tracking URI.

## Experiments and Runs

- `mlflow.set_experiment(experiment_name=None, experiment_id=None, trace_location=None)` requires exactly one of name or ID. A missing named experiment is created automatically; Databricks experiment names may need absolute workspace paths.
- `mlflow.create_experiment(name, artifact_location=None, tags=None)` is useful when the artifact root must be explicit before runs are created.
- `mlflow.start_run(run_id=None, experiment_id=None, run_name=None, nested=False, parent_run_id=None, tags=None, description=None, log_system_metrics=None)` creates or resumes a run and sets it active. Use a `with` block to guarantee `end_run()`.
- `start_run(run_id=...)` resumes an existing run and ignores most creation-only fields. `MLFLOW_RUN_ID` can also resume a run; an explicit `run_id` wins.
- Starting another run while one is active requires `nested=True` or a valid `parent_run_id`; otherwise MLflow raises an error telling you to end the current run or start a nested run.
- `MlflowClient.create_run(experiment_id, start_time=None, tags=None, run_name=None)` creates a run object but does not change the active fluent run.

## Logging Data

- Fluent logging such as `mlflow.log_param`, `mlflow.log_params`, `mlflow.log_metric`, `mlflow.log_metrics`, `mlflow.set_tag`, `mlflow.set_tags`, `mlflow.log_artifact`, and `mlflow.log_artifacts` targets the active run. Some fluent APIs create a run implicitly when none is active, but production code should usually use an explicit `with mlflow.start_run()` block.
- `mlflow.log_metric(key, value, step=None, synchronous=None, timestamp=None, run_id=None, model_id=None, dataset=None)` supports metric step, timestamp, explicit run ID, logged-model association, and dataset association.
- `MlflowClient.log_metric(run_id, key, value, timestamp=None, step=None, synchronous=None, dataset_name=None, dataset_digest=None, model_id=None)` is explicit and does not depend on active-run state. When using `dataset_name`, provide `dataset_digest` too.
- Metric keys allow alphanumerics, underscores, dashes, periods, spaces, and slashes. Backend stores guarantee support up to documented key and value lengths, but some stores may support more.
- With `synchronous=False`, logging methods may return a `RunOperations` future. Call `.wait()` before reading back data or before process exit if correctness depends on completion. If `synchronous=None`, behavior follows `MLFLOW_ENABLE_ASYNC_LOGGING`, defaulting to synchronous behavior when not enabled.
- `mlflow.log_input(dataset)` and metric `dataset=` / client `dataset_name` + `dataset_digest` connect tracking records to datasets. GenAI evaluation datasets and traces are owned by `genai-observability`.

## Artifacts and URIs

- `mlflow.log_artifact(local_path, artifact_path=None)` logs one file; `mlflow.log_artifacts(local_dir, artifact_path=None)` logs a directory tree.
- `artifact_path` is a logical path within the run artifact root, not a local destination path. Avoid leading slashes and do not pass a filename as `artifact_path` when logging a directory unless you intend that logical directory name.
- `mlflow.get_artifact_uri(artifact_path=None)` returns the active run artifact URI. `MlflowClient.list_artifacts(run_id, path=None)` and `download_artifacts` can inspect or retrieve artifacts later.
- Model registry sources often use `runs:/<run_id>/<artifact_path>`, `models:/<name>/<version>`, `models:/<name>@<alias>`, or MLflow 3 logged-model URIs such as `models:/<model_id>`.

## Searching

- `mlflow.search_runs(experiment_ids=None, filter_string="", run_view_type=ViewType.ACTIVE_ONLY, max_results=100000, order_by=None, output_format="pandas", search_all_experiments=False, experiment_names=None)` returns a pandas DataFrame by default or a list of `Run` objects with `output_format="list"`.
- `MlflowClient.search_runs(experiment_ids, filter_string="", run_view_type=ViewType.ACTIVE_ONLY, max_results=1000, order_by=None, page_token=None)` returns a paged list of `Run` entities and exposes pagination tokens when supported.
- Do not mix `experiment_ids` and `experiment_names` in fluent `search_runs`. Use `search_all_experiments=True` only when IDs and names are omitted or empty.
- Common filter prefixes are `metrics.`, `params.`, `tags.`, and run attributes such as `attributes.status`, depending on the search surface. Quote string values: `tags.release ILIKE '%rc%'`, `metrics.rmse < 0.5`, `params.model = 'rf'`.
- `LIKE` is case-sensitive and `ILIKE` is case-insensitive where supported. Tags or names with special characters may require backticks in search APIs that accept tag keys, for example `tags.`key.with.dot` = 'v'`.
- For MLflow 3 logged models, `mlflow.search_logged_models(...)` supports model attributes, params, metrics, tags, dataset-aware metrics, ordering, and `output_format="list"` for entity objects.

## Model Registry

- `mlflow.register_model(model_uri, name, await_registration_for=300, tags=None, env_pack=None)` creates a new model version under a registered model, creating the registered model if needed.
- Supported `register_model` sources include `runs:/<run_id>/<artifact_path>`, `models:/<model_name>/<version>`, `models:/<model_id>`, and local MLflow model paths. Actual model flavor logging is owned by `models-and-flavors`.
- `MlflowClient.create_registered_model(name, tags=None, description=None, deployment_job_id=None)` creates an empty registered model and fails if the name already exists.
- `MlflowClient.create_model_version(name, source, run_id=None, tags=None, run_link=None, description=None, await_creation_for=300, model_id=None)` creates a version from a model source. Use `await_creation_for=0` or `None` to skip waiting.
- Registry lifecycle methods include `get_registered_model`, `search_registered_models`, `update_registered_model`, `delete_registered_model`, `get_model_version`, `search_model_versions`, `update_model_version`, `delete_model_version`, `set_registered_model_tag`, `set_model_version_tag`, `set_registered_model_alias`, and `get_model_version_by_alias`.
- `transition_model_version_stage(...)` remains available for stage-compatible workflows, but aliases are the modern deployment selector pattern: assign an alias such as `champion` and load or query `models:/Name@champion`.
- Alias names like `v<number>` are reserved and cannot be set manually.

## Store and Backend Caveats

- Local SQLite tracking URIs (`sqlite:///...`) are the safest default for isolated MLflow 3 smoke tests and database-backed tracking/registry metadata. Filesystem tracking is legacy/maintenance-mode behavior and requires deliberate opt-out with `MLFLOW_ALLOW_FILE_STORE=true`.
- The registry implementation can resolve file, SQLAlchemy database, REST, Databricks workspace, and Unity Catalog style backends, but self-hosted registry server workflows should use a database-backed backend store.
- SQLAlchemy-backed tracking and registry support SQLite, PostgreSQL, MySQL, and MSSQL dialect families through SQLAlchemy. Use absolute SQLite paths for predictable local behavior.
- HTTP(S) tracking server interactions require the server to be running and configured with compatible backend/artifact stores. Server startup, auth setup, and self-hosting are owned by `serving-and-projects`.
- Databricks/cloud URIs require the appropriate host credentials. For Databricks Unity Catalog registry, configure `mlflow.set_registry_uri("databricks-uc")` or a profile URI and ensure credentials are available.
- Workspace-aware stores preserve workspace scoping in tracking and registry operations. Do not remove or bypass workspace URI, workspace header, or request-context plumbing when changing tracking store code.
