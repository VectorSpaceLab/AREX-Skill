# Modeling and MLflow API Reference

This reference distills the package APIs for H2O AutoML, deterministic model evaluation, and MLflow operations. It is self-contained: use the import paths and guidance below instead of reopening repository examples.

## Import map

| Capability | Public import | Optional dependencies | Side effects when invoked |
|---|---|---|---|
| H2O AutoML agent | `from ai_data_science_team.ml_agents import H2OMLAgent, make_h2o_ml_agent` | `h2o`; caller-provided LangChain-compatible LLM | Agent generation calls the LLM; execution starts/uses a local H2O cluster and may write logs/models if configured. |
| H2O AutoML tool | `from ai_data_science_team.tools.h2o import train_h2o_automl` | `h2o`; `mlflow` only when `enable_mlflow=True` | Starts/uses H2O and trains; may write a saved model and MLflow run. |
| Deterministic evaluation | `from ai_data_science_team.ml_agents import ModelEvaluationAgent` | `h2o`; package base dependencies include pandas, NumPy, scikit-learn, and Plotly | Starts/uses H2O to load or resolve the model; computes metrics locally; no LLM call is required. |
| MLflow tools agent | `from ai_data_science_team.ml_agents import MLflowToolsAgent, make_mlflow_tools_agent` | `mlflow`; caller-provided LangChain-compatible LLM | Tool-calling agent may inspect, mutate, launch UI, stop UI, download artifacts, or predict depending on user request. |
| Direct MLflow tools | `from ai_data_science_team.tools import mlflow as mlflow_tools` | `mlflow`; `psutil` for UI status/stop | Deterministic function/tool calls; some are read-only, some mutate tracking/registry state or local files. |

Import-time note: several agent modules use notebook display helpers for Markdown output. If public imports fail with an `IPython` error, install the notebook display dependency before diagnosing H2O or MLflow.

## `H2OMLAgent`

Constructor signature distilled from the public class:

```python
H2OMLAgent(
    model,
    n_samples=30,
    log=False,
    log_path=None,
    file_name="h2o_automl.py",
    function_name="h2o_automl",
    model_directory=None,
    overwrite=True,
    human_in_the_loop=False,
    bypass_recommended_steps=False,
    bypass_explain_code=False,
    enable_mlflow=False,
    mlflow_tracking_uri=None,
    mlflow_artifact_root=None,
    mlflow_experiment_name="H2O AutoML",
    mlflow_run_name=None,
    checkpointer=None,
)
```

### Key constructor parameters

| Parameter | Use | Safe default guidance |
|---|---|---|
| `model` | LangChain-compatible chat model used to generate training code and optional explanations. | Require the caller to provide it; do not create external-provider clients without authorization. |
| `n_samples` | Number of rows used when summarizing data for the code-generation prompt. | Keep small for wide/sensitive data. |
| `log`, `log_path`, `file_name`, `function_name`, `overwrite` | Controls saving generated H2O training code. | Keep `log=False` unless the user requested generated-code artifacts. |
| `model_directory` | Directory for saved best H2O model. If absent and `log_path` is absent, saving is skipped. | Use a task-scoped output directory only when model persistence is required. |
| `human_in_the_loop`, `checkpointer` | Enables graph interrupt/review. If review is enabled without a checkpointer, the implementation falls back to memory. | Keep disabled in non-interactive automation. |
| `bypass_recommended_steps`, `bypass_explain_code` | Skips optional prompt/report nodes. | Enable bypasses for short automated runs. |
| `enable_mlflow`, `mlflow_tracking_uri`, `mlflow_artifact_root`, `mlflow_experiment_name`, `mlflow_run_name` | Adds MLflow logging to the generated/managed H2O workflow. | Keep `enable_mlflow=False` until `mlflow` is installed and the tracking destination is authorized. |

### Invocation methods

| Method | Inputs | Returns | Response impact |
|---|---|---|---|
| `invoke_agent(data_raw, user_instructions=None, target_variable=None, max_retries=3, retry_count=0, **kwargs)` | pandas DataFrame, optional text instructions, target column. | `None`; stores graph output in `agent.response`. | Synchronous H2O training workflow. |
| `ainvoke_agent(...)` | Same logical inputs as `invoke_agent`. | `None`; stores output. | Async graph invocation. |
| `invoke_messages(messages, data_raw, target_variable=None, max_retries=3, retry_count=0, **kwargs)` | Explicit message list plus DataFrame. | `None`; stores output. | Preferred when a supervisor/team already has message history. |
| `ainvoke_messages(...)` | Async version of explicit-message invocation. | `None`; stores output. | Async graph invocation. |
| `update_params(**kwargs)` | Any constructor parameter. | Rebuilds the compiled graph. | Use when toggling MLflow/logging after dependency checks. |

### H2O response accessors

| Accessor | Value returned when present | Notes |
|---|---|---|
| `get_leaderboard()` | pandas DataFrame built from response `leaderboard`. | Ranked AutoML models and metrics. |
| `get_best_model_id()` | String model id. | Use with `h2o.get_model` in the same H2O cluster session or pass to evaluation. |
| `get_model_path()` | Saved model path or `None`. | Available only when model saving occurred. |
| `get_data_raw()` | pandas DataFrame reconstructed from response `data_raw`. | Useful for downstream evaluation/inspection. |
| `get_h2o_train_function(markdown=False)` | Generated function source, optionally IPython Markdown. | Treat as generated code; review before reuse. |
| `get_recommended_ml_steps(markdown=False)` | Recommended steps from the agent. | Absent when bypassed. |
| `get_workflow_summary(markdown=False)` | Summary derived from the final message. | Depends on graph response shape. |
| `get_log_summary(markdown=False)` | Function path/name, best model id, model path when logged. | Only meaningful after logging/model saving. |
| `get_response()` | Inherited/base response access pattern when available. | Use direct `agent.response` if no explicit getter is exposed in the installed version. |

## `make_h2o_ml_agent`

Factory signature mirrors the class parameters:

```python
make_h2o_ml_agent(
    model,
    n_samples=30,
    log=False,
    log_path=None,
    file_name="h2o_automl.py",
    function_name="h2o_automl",
    model_directory=None,
    overwrite=True,
    human_in_the_loop=False,
    bypass_recommended_steps=False,
    bypass_explain_code=False,
    enable_mlflow=False,
    mlflow_tracking_uri=None,
    mlflow_artifact_root=None,
    mlflow_experiment_name="H2O AutoML",
    mlflow_run_name=None,
    checkpointer=None,
)
```

Use the factory when a raw compiled graph is preferred over the convenience wrapper. It imports and checks `h2o` during graph construction, so missing optional dependencies fail before training.

## `train_h2o_automl` tool

`train_h2o_automl` is registered as a LangChain tool named `train_h2o_automl` with `return_direct=True` and a content/artifact response format.

```python
train_h2o_automl(
    data_raw,
    target="Churn",
    max_runtime_secs=30,
    exclude_algos=None,
    balance_classes=True,
    nfolds=5,
    seed=42,
    max_models=20,
    stopping_metric="logloss",
    stopping_tolerance=0.001,
    stopping_rounds=3,
    sort_metric="AUC",
    model_directory=None,
    log_path=None,
    enable_mlflow=False,
    mlflow_tracking_uri=None,
    mlflow_experiment_name="H2O AutoML",
    run_name=None,
    **kwargs,
)
```

Input expectations:

- `data_raw` is row-wise data, normally `df.to_dict(orient="records")`.
- `target` must be an existing column.
- `exclude_algos` defaults to `["DeepLearning"]` when omitted.
- `**kwargs` are passed through to `H2OAutoML`.

Output JSON content contains:

```python
{
    "leaderboard": {...},
    "best_model_id": "...",
    "model_path": "... or None",
    "model_results": {
        "model_flavor": "H2O AutoML",
        "model_path": "... or None",
        "best_model_id": "...",
        "metrics": {...},
    },
    "mlflow_run_id": "... or None",
}
```

Use a bounded `max_runtime_secs` and `max_models` in notebooks, apps, and tests. Prefer `max_models` plus a fixed `seed` when reproducibility is more important than time-budget behavior.

## `ModelEvaluationAgent`

Constructor:

```python
ModelEvaluationAgent(model=None, log=False)
```

Primary method:

```python
invoke_messages(
    messages,
    *,
    data_raw,
    model_artifacts=None,
    target_variable=None,
    test_size=0.2,
    random_state=42,
    **kwargs,
)
```

Behavior:

1. Validates that `data_raw` is a non-empty pandas DataFrame.
2. Requires `target_variable` and checks that it exists in the DataFrame.
3. Resolves the H2O model from `model_artifacts["model_path"]` or `model_artifacts["best_model_id"]`.
4. Infers task type: boolean/object/category targets and low-cardinality integer targets are classification; other targets are regression.
5. Prefers H2O cross-validation holdout predictions when available.
6. Falls back to a deterministic `train_test_split(test_size=test_size, random_state=random_state)`. This fallback may be optimistic if the model was trained on the full dataset.
7. Stores `response` with `messages`, `eval_artifacts`, and `plotly_graph`.

Response fields:

| Field | Meaning |
|---|---|
| `eval_artifacts.target_variable` | Evaluated target column. |
| `eval_artifacts.task_type` | `classification` or `regression`. |
| `eval_artifacts.evaluation_source` | `cross_validation_holdout` or `random_split_in_sample`. |
| `eval_artifacts.metrics` | Classification: `accuracy`, optional `precision`, `recall`, `f1`, `auc`; regression: `rmse`, `mae`, `r2`. |
| `eval_artifacts.positive_label` | Classification positive label selected from known labels when available. |
| `eval_artifacts.confusion_matrix` | Classification confusion matrix dict. |
| `eval_artifacts.roc_curve` | Plotly ROC curve dict when probability columns allow AUC. |
| `plotly_graph` | Confusion matrix or residual Plotly figure dict. |

Accessor:

```python
evaluator.get_eval_artifacts()
```

## `MLflowToolsAgent`

Constructor:

```python
MLflowToolsAgent(
    model,
    mlflow_tracking_uri=None,
    mlflow_registry_uri=None,
    create_react_agent_kwargs={},
    invoke_react_agent_kwargs={},
    checkpointer=None,
    log_tool_calls=True,
)
```

Factory:

```python
make_mlflow_tools_agent(
    model,
    mlflow_tracking_uri=None,
    mlflow_registry_uri=None,
    create_react_agent_kwargs={},
    invoke_react_agent_kwargs={},
    checkpointer=None,
    log_tool_calls=True,
)
```

The factory imports `mlflow`, applies provided tracking/registry URIs, builds a React-style tool-calling subgraph, and post-processes tool artifacts into concise user messages.

Invocation and accessors:

| Method | Purpose |
|---|---|
| `invoke_agent(user_instructions=None, data_raw=None, **kwargs)` / `ainvoke_agent(...)` | Natural-language MLflow operations. `data_raw` is converted to dict for prediction tools. |
| `invoke_messages(messages, data_raw=None, **kwargs)` / `ainvoke_messages(...)` | Use existing message history instead of a fresh user string. |
| `get_ai_message(markdown=False)` | Final assistant/tool summary. |
| `get_mlflow_artifacts(as_dataframe=False)` | Raw tool artifacts or a best-effort DataFrame for experiments/runs. |
| `get_internal_messages(markdown=False)` | Full internal tool-call transcript; use for debugging, not for user-facing secrets. |
| `get_tool_calls()` | Tool names called in the last response. |
| `update_params(**kwargs)` | Rebuilds the graph with new URIs, checkpointer, or tool-call settings. |

## Direct MLflow tool catalog

See [MLflow tools](mlflow-tools.md) for workflows and safety notes. Public direct tools include:

| Tool | Category | Typical result |
|---|---|---|
| `mlflow_tracking_info` | Read-only tracking state | Tracking URI, registry URI, active run info. |
| `mlflow_search_experiments` | Read-only experiments | Experiment records with ids, names, stages, artifact locations. |
| `mlflow_search_runs` | Read-only runs | Recent/filter-matched run records; optional params/metrics/tags. |
| `mlflow_get_run_details` | Read-only run details | Run info, params, metrics, tags, shallow artifact listing. |
| `mlflow_ui_status` | Read-only local process status | UI process/listening port summary. |
| `mlflow_create_experiment` | Mutating experiment management | New experiment id. |
| `mlflow_set_tags`, `mlflow_log_params`, `mlflow_log_metrics`, `mlflow_log_table`, `mlflow_log_dict`, `mlflow_log_figure`, `mlflow_log_artifact` | Mutating run logging | Run id plus logged payload/artifact metadata. |
| `mlflow_list_artifacts` | Read-only artifacts | Artifact listing for a run/path. |
| `mlflow_download_artifacts` | Local write | Downloaded files under destination path. |
| `mlflow_predict_from_run_id` | Inference | Prediction summary and artifacts from `runs:/<run_id>/model`. |
| `mlflow_list_registered_models`, `mlflow_search_registered_models`, `mlflow_get_model_version_details` | Registry read | Registered model/version metadata. |
| `mlflow_transition_model_version_stage` | Registry mutation | Stage transition confirmation. |
| `mlflow_launch_ui` | Local process launch | Starts `mlflow ui` on an available port. |
| `mlflow_stop_ui` | Local process kill | Kills a process listening on the specified port when permitted. |

## API boundary notes

- The H2O agent is an LLM code-generation workflow, not a deterministic training wrapper. The generated function should be reviewed before promoting it.
- The direct `train_h2o_automl` tool is deterministic with respect to its explicit arguments and H2O behavior, but still starts local H2O and performs actual model training.
- `ModelEvaluationAgent` is the deterministic evaluation layer for already-trained H2O models.
- `MLflowToolsAgent` can call mutating tools from natural language. For automated workflows, prefer direct tool calls with explicit arguments and a user-authorized tracking URI.
