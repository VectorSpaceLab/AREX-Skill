# MLflow Tools and Agent Workflows

This reference covers the MLflow surfaces bundled with `ai-data-science-team`: the deterministic direct tools and the LLM-backed `MLflowToolsAgent`.

## Choose direct tools or agent

| Use case | Prefer | Why |
|---|---|---|
| Scripted experiment/run inspection | Direct tools | Explicit inputs, deterministic outputs, no LLM call. |
| Logging known params/metrics/tables/artifacts | Direct tools | Safer for automation; easy to review side effects. |
| Natural-language exploration of experiments/runs | `MLflowToolsAgent` | The agent can choose search/detail tools and format summaries. |
| Prediction from a run id with a user-provided dataset | Agent or direct tool with explicit state | The tool expects data in the tool/agent state. |
| Launching/stopping MLflow UI | Direct tool after consent | These start or kill local processes. |
| Model registry stage transition | Direct tool after consent | Registry mutation should be explicit and auditable. |

## Tracking and registry URIs

All MLflow operations should begin by identifying the tracking destination.

```python
from ai_data_science_team.tools.mlflow import mlflow_tracking_info

message, artifact = mlflow_tracking_info.invoke({})
print(message)
print(artifact["tracking_uri"], artifact["registry_uri"])
```

When the user provides a tracking URI, pass it explicitly to direct tools or set it in `MLflowToolsAgent(mlflow_tracking_uri=...)`. Use local/disposable destinations for experiments unless the user authorizes a remote server.

## Read-only inspection tools

### Experiments

```python
from ai_data_science_team.tools.mlflow import mlflow_search_experiments

msg, artifact = mlflow_search_experiments.invoke({
    "filter_string": None,
    "tracking_uri": "file:./mlruns",
})
experiments = artifact["experiments"]
```

Artifact fields include `experiment_id`, `name`, `artifact_location`, lifecycle stage, and timestamps.

### Runs

```python
from ai_data_science_team.tools.mlflow import mlflow_search_runs, mlflow_get_run_details

msg, runs_artifact = mlflow_search_runs.invoke({
    "experiment_ids": ["0"],
    "filter_string": None,
    "max_results": 10,
    "order_by": ["attributes.start_time DESC"],
    "include_details": False,
    "tracking_uri": "file:./mlruns",
})

run_id = runs_artifact["runs"][0]["run_id"]
msg, details = mlflow_get_run_details.invoke({
    "run_id": run_id,
    "tracking_uri": "file:./mlruns",
})
```

Run search records can include `run_id`, `run_name`, `status`, `experiment_id`, `start_time`, `duration_seconds`, `has_model`, `model_uri`, and metric/parameter previews. Set `include_details=True` only when full params, metrics, and tags are needed and safe to reveal.

### Artifact listing

```python
from ai_data_science_team.tools.mlflow import mlflow_list_artifacts

msg, artifacts = mlflow_list_artifacts.invoke({
    "run_id": run_id,
    "path": "model",
    "tracking_uri": "file:./mlruns",
})
```

This is read-only and returns entries with `path`, `is_dir`, and `file_size`.

### UI status

```python
from ai_data_science_team.tools.mlflow import mlflow_ui_status

msg, status = mlflow_ui_status.invoke({"port": 5000})
```

This inspects local processes and sockets via `psutil`; it does not launch or kill anything.

## Mutating run logging tools

These tools create or modify MLflow tracking state. Use only after user authorization and with a known tracking URI/experiment.

### Create an experiment

```python
from ai_data_science_team.tools.mlflow import mlflow_create_experiment

msg = mlflow_create_experiment.invoke({"experiment_name": "H2O AutoML"})
```

### Set tags, params, and metrics

```python
from ai_data_science_team.tools.mlflow import mlflow_set_tags, mlflow_log_params, mlflow_log_metrics

common = {"tracking_uri": "file:./mlruns", "experiment_name": "H2O AutoML"}

msg, tags_artifact = mlflow_set_tags.invoke({
    **common,
    "tags": {"workflow": "h2o_automl", "owner": "local"},
})
run_id = tags_artifact["run_id"]

mlflow_log_params.invoke({
    "run_id": run_id,
    "params": {"target": "target", "max_models": 3, "seed": 42},
    "tracking_uri": "file:./mlruns",
})
mlflow_log_metrics.invoke({
    "run_id": run_id,
    "metrics": {"accuracy": 0.91, "auc": 0.95},
    "tracking_uri": "file:./mlruns",
})
```

Metrics are coerced to floats where possible; non-numeric metric values are skipped.

### Log tables, dictionaries, figures, and local artifacts

```python
from ai_data_science_team.tools.mlflow import (
    mlflow_log_table,
    mlflow_log_dict,
    mlflow_log_figure,
    mlflow_log_artifact,
)

mlflow_log_table.invoke({
    "run_id": run_id,
    "data": [{"model_id": "m1", "auc": 0.95}],
    "artifact_file": "leaderboard.json",
    "tracking_uri": "file:./mlruns",
})
mlflow_log_dict.invoke({
    "run_id": run_id,
    "data": {"best_model_id": "m1"},
    "artifact_file": "model_info.json",
    "tracking_uri": "file:./mlruns",
})
# plotly_graph_dict should be a Plotly figure represented as a JSON-serializable dict.
mlflow_log_figure.invoke({
    "run_id": run_id,
    "plotly_graph_dict": plotly_graph_dict,
    "artifact_file": "plots/evaluation.html",
    "tracking_uri": "file:./mlruns",
})
# Only log local paths the user approved.
mlflow_log_artifact.invoke({
    "run_id": run_id,
    "local_path": "./models/h2o_best",
    "artifact_path": "h2o_best_model",
    "tracking_uri": "file:./mlruns",
})
```

`mlflow_log_artifact` logs either a single file or a directory. Confirm the path does not contain secrets before logging.

## Artifact download

`mlflow_download_artifacts` writes files locally. Use only after the user authorizes a destination.

```python
from ai_data_science_team.tools.mlflow import mlflow_download_artifacts

msg, downloaded = mlflow_download_artifacts.invoke({
    "run_id": run_id,
    "path": "model",
    "dst_path": "./downloaded_artifacts",
    "tracking_uri": "file:./mlruns",
})
```

Validate `downloaded["downloaded_files"]` before using the files. Avoid downloading artifacts from untrusted remote tracking servers into sensitive directories.

## Prediction from a run id

The prediction tool loads `runs:/<run_id>/model` with `mlflow.pyfunc.load_model` and predicts on a pandas DataFrame built from supplied state data.

Agent route:

```python
from ai_data_science_team.ml_agents import MLflowToolsAgent

agent = MLflowToolsAgent(model=llm, mlflow_tracking_uri="file:./mlruns")
agent.invoke_agent(
    user_instructions="Use run id <RUN_ID> to predict on the provided rows.",
    data_raw=scoring_df,
)
prediction_artifacts = agent.get_mlflow_artifacts()
```

Direct route when your LangChain version exposes the injected state parameter:

```python
from ai_data_science_team.tools.mlflow import mlflow_predict_from_run_id

msg, prediction_artifact = mlflow_predict_from_run_id.invoke({
    "run_id": "<RUN_ID>",
    "data_raw": scoring_df.to_dict(),
    "tracking_uri": "file:./mlruns",
})
```

Expected failures:

- No `data_raw`: the tool returns a message asking for data.
- No `model` artifact at `runs:/<run_id>/model`: `mlflow.pyfunc.load_model` fails.
- Scoring columns differ from the model's expected inputs: model prediction raises an inference error.

## Model registry tools

Registry tools can be read-only or mutating. Confirm registry URI and permissions before use.

Read-only:

```python
from ai_data_science_team.tools.mlflow import (
    mlflow_list_registered_models,
    mlflow_search_registered_models,
    mlflow_get_model_version_details,
)

msg, models = mlflow_list_registered_models.invoke({
    "max_results": 100,
    "tracking_uri": "file:./mlruns",
})
msg, matches = mlflow_search_registered_models.invoke({
    "filter_string": "name LIKE 'h2o%'",
    "max_results": 20,
    "tracking_uri": "file:./mlruns",
})
msg, version = mlflow_get_model_version_details.invoke({
    "name": "h2o_churn",
    "version": "1",
    "tracking_uri": "file:./mlruns",
})
```

Mutating stage transition:

```python
from ai_data_science_team.tools.mlflow import mlflow_transition_model_version_stage

msg = mlflow_transition_model_version_stage.invoke({
    "name": "h2o_churn",
    "version": "1",
    "stage": "Staging",
    "archive_existing_versions": False,
    "tracking_uri": "file:./mlruns",
})
```

Stage transitions should be treated as release operations. Ask before using stages such as `Production` or archiving existing versions.

## MLflow UI tools

These affect local processes.

Launch:

```python
from ai_data_science_team.tools.mlflow import mlflow_launch_ui

msg = mlflow_launch_ui.invoke({
    "port": 5000,
    "host": "localhost",
    "tracking_uri": "file:./mlruns",
})
```

The tool scans for an available port at or above the requested port and starts `mlflow ui` in a subprocess. It returns the URL and process id.

Stop:

```python
from ai_data_science_team.tools.mlflow import mlflow_stop_ui

msg = mlflow_stop_ui.invoke({"port": 5000})
```

The stop tool enumerates local network connections and kills the process listening on the port when permissions allow. Never call it for a shared port without user confirmation.

## `MLflowToolsAgent` post-processing

`MLflowToolsAgent` wraps the tools in a React-style graph and then post-processes artifacts.

```python
agent.invoke_agent("Show the most recent H2O AutoML runs.")
summary = agent.get_ai_message(markdown=False)
artifacts = agent.get_mlflow_artifacts(as_dataframe=False)
artifact_frame = agent.get_mlflow_artifacts(as_dataframe=True)
tool_calls = agent.get_tool_calls()
```

Post-processing behavior:

- Experiment artifacts are formatted into a Markdown table with experiment id, name, lifecycle stage, timestamps, and artifact location.
- Run artifacts are formatted into a Markdown table with run id, name, status, time, duration, model availability, params preview, and metrics preview.
- When exactly one tool artifact is present and `as_dataframe=False`, the getter may unwrap the single artifact for backwards-compatible shape.
- `get_internal_messages()` can expose detailed tool outputs; redact sensitive URIs, params, tags, or artifacts before sharing outside the task.

## Safety checklist for MLflow operations

Before returning success:

1. Confirm which tool was called with `get_tool_calls()` or direct return values.
2. Confirm the tracking URI/registry URI matches the user's intended destination.
3. Confirm whether the operation was read-only or mutating.
4. For logging, verify the returned `run_id` and artifact path/name.
5. For downloads, list downloaded files and scan for unexpected locations.
6. For UI operations, report host/port and whether a process was launched or stopped.
7. For registry transitions, report model name, version, target stage, and whether existing versions were archived.
