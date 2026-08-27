# Modeling and MLflow Troubleshooting

Use this table when H2O AutoML, deterministic evaluation, MLflow tools, or optional imports fail. Recovery steps are intentionally bounded and avoid external services unless the user authorizes them.

## Quick triage sequence

1. Run the optional readiness checker:
   ```bash
   python sub-skills/modeling-and-mlflow/scripts/check_ml_optional_imports.py --format text
   ```
2. Decide whether the failing operation is import-only, H2O cluster/training, deterministic evaluation, MLflow tracking, MLflow UI/process, MLflow artifacts/prediction, or LLM tool-calling.
3. Confirm side-effect authorization before installing packages, starting services, training, downloading artifacts, logging to MLflow, or stopping UI processes.
4. Prefer direct deterministic tools for diagnosis before using LLM-backed agents.

## Import and optional dependency failures

| Symptom | Likely cause | Recovery steps |
|---|---|---|
| `ModuleNotFoundError: No module named 'IPython'` while importing ML agent modules | Agent modules use notebook display helpers for Markdown output. | Install the notebook display dependency in the active environment, then retry the import. Do not diagnose H2O/MLflow until this base import issue is resolved. |
| `ImportError: The 'h2o' library is not installed` from H2O agent/factory | Optional `h2o` dependency is absent. | Install the package's machine-learning extra or explicitly install `h2o`; rerun the readiness checker. |
| `MLflow is not installed. Please install it by running: pip install mlflow` | Optional `mlflow` dependency is absent. | Install the package's machine-learning extra or explicitly install `mlflow`; rerun the readiness checker. |
| Public imports work but H2O training fails immediately | H2O's Java-backed runtime is unavailable or cannot start. | Check Java availability, memory limits, firewall/port constraints, and whether another H2O cluster is already running. Keep the first verification import-only unless the user authorizes H2O startup. |
| `langgraph` or `langchain` import errors | Base package dependencies are missing or version-incompatible. | Reinstall/repair the base package dependencies in the active environment; do not install optional ML extras as a substitute for base graph dependencies. |

## H2O AutoML training failures

| Symptom | Likely cause | Recovery steps |
|---|---|---|
| `Target variable '<name>' not found in data` | `target_variable`/`target` does not match DataFrame columns after cleaning or dropping columns. | Print column names, verify exact spelling/case, and pass the target explicitly. Do not let the agent infer target if the dataset has multiple plausible labels. |
| `Target variable ... has no non-null values` | Target column is present but empty after filtering. | Revisit upstream cleaning/filtering; use a non-empty label column before training. |
| `Target variable ... has <2 classes` | Classification target has one class after filtering or null handling. | Use a less restrictive subset, fix label preprocessing, or treat the task as invalid for classification. |
| H2O treats a binary target as regression | Numeric/binary target was not made categorical for classification semantics. | Convert target to string/category before training or instruct the H2O agent to convert binary/categorical targets to H2O factors. Verify leaderboard metrics are classification metrics. |
| H2O training runs too long | AutoML budget is too large, time budget is unbounded, or algorithms are expensive. | Set `max_runtime_secs`, reduce `max_models`, use a fixed `seed`, and consider `exclude_algos=["DeepLearning"]`. |
| Out-of-memory or JVM memory errors | H2O Java heap, XGBoost, or dataset size exceeds available memory. | Sample rows/columns, reduce algorithms/models/folds, leave memory headroom for XGBoost, or use a larger machine. Do not continue retrying without changing budget. |
| Empty or missing leaderboard | Training failed, target invalid, H2O error was swallowed into response, or generated code returned an unexpected shape. | Inspect `agent.response` for error fields/messages, rerun with smaller deterministic settings, and require `leaderboard` plus `best_model_id` before reporting success. |
| `h2o.is_running` attribute error in generated code | Generated code used a non-existent H2O helper. | Remove the check and call `h2o.init()` directly; the package prompt explicitly warns that `h2o.init()` should handle cluster startup/connection. |
| Model path is `None` after training | Neither `model_directory` nor `log_path` was provided. | This is expected when persistence is disabled. Re-run with a user-approved `model_directory` if a saved model is needed. |

## Deterministic evaluation failures

| Symptom | Likely cause | Recovery steps |
|---|---|---|
| Response says no dataset is available | `data_raw` was `None`, not a pandas DataFrame, or empty. | Pass the same modeling DataFrame or a validated holdout DataFrame. |
| Response asks for target column name | `target_variable` was missing. | Pass `target_variable` explicitly. |
| Response says target column was not found | Evaluation DataFrame does not include the target column. | Join/retain the target in the evaluation frame; do not pass scoring-only features to metrics evaluation. |
| Response says H2O could not initialize or load | H2O missing, Java/H2O startup failed, `model_path` invalid, or `best_model_id` no longer exists in the current H2O cluster. | Prefer a saved `model_path` for cross-session evaluation; rerun readiness checks and confirm H2O can initialize. |
| Response says it could not load trained model | `model_artifacts` lacks both `model_path` and `best_model_id`, or the values are stale. | Re-run training with model saving enabled or pass the current H2O `best_model_id` while the cluster still has the model. |
| Metrics appear optimistic | Evaluator used `evaluation_source="random_split_in_sample"` after the model was trained on the full dataset. | Report the optimism caveat; for stronger validation, train with cross-validation/holdout design or use a true unseen holdout workflow. |
| Classification precision/recall/f1 missing or odd | Positive label selection did not match the user's domain semantics. | Check `positive_label`; if needed, remap labels so the intended positive class is one of the recognized values or post-compute metrics manually. |
| AUC/ROC missing | H2O prediction output did not include a probability column matching the selected positive label. | Verify classifier probability outputs and label names; use confusion matrix/accuracy when probability columns are unavailable. |
| Regression metrics fail with conversion errors | Target or predictions are non-numeric after task inference. | Clean target dtype or treat the task as classification if labels are discrete. |

## MLflow tracking and logging failures

| Symptom | Likely cause | Recovery steps |
|---|---|---|
| Experiment/run search returns no results | Wrong tracking URI, wrong experiment id, or no completed runs. | Call `mlflow_tracking_info`, list experiments, and verify the exact `experiment_id` used by `mlflow_search_runs`. |
| `MlflowClient` connection/authentication errors | Remote tracking/registry URI requires credentials or is unreachable. | Ask the user to configure credentials/network outside the skill; do not invent or echo secrets. Retry read-only tracking info after credentials are configured. |
| Logging starts a new run unexpectedly | No active run or `run_id`; helper starts a run under the selected experiment. | Pass `run_id` explicitly when adding to an existing run. Confirm active run with `mlflow_tracking_info`. |
| Metrics silently missing | Metric values were non-numeric and skipped by the helper. | Convert metrics to floats before logging; keep text metadata in tags, params, or dictionaries. |
| Table logging fails or has unexpected shape | Input was not DataFrame-like and was coerced unexpectedly. | Convert to a pandas DataFrame explicitly and log a small preview first. |
| Figure logging falls back to JSON | `plotly_graph_dict` was not reconstructible as a Plotly figure. | Validate the figure with Plotly before logging, or accept JSON artifact fallback. |
| Artifact logging uploads sensitive files | Directory/file path included credentials, raw private data, or broad outputs. | Stop and inspect paths before logging; use task-scoped sanitized artifacts only. |

## MLflow model logging or prediction fails

| Symptom | Likely cause | Recovery steps |
|---|---|---|
| Warning about model logged without signature/input example | MLflow model logging did not receive an input example/signature. | Treat as a warning for reproducibility; provide or log separate schema metadata when promoting the model. |
| H2O model metrics logged but no model artifact appears | MLflow/H2O flavor API mismatch, H2O model not available, or model logging raised an exception after metrics. | Check run artifacts, package versions, and `agent.response` fields such as `mlflow_model_uri` or `mlflow_model`. Re-run with model saving enabled if needed. |
| `mlflow_predict_from_run_id` says no data was provided | Prediction tool did not receive `data_raw` in agent/tool state. | Use `MLflowToolsAgent.invoke_agent(..., data_raw=df)` or pass the injected data field if direct invocation supports it in the installed LangChain version. |
| `mlflow.pyfunc.load_model` fails for `runs:/<run_id>/model` | The run has no `model` artifact or the model is not PyFunc-loadable. | List artifacts for the run; verify a `model` directory exists; use a run id from H2O training with MLflow model logging enabled. |
| Prediction raises feature/schema errors | Scoring DataFrame columns differ from model expectations. | Align columns and dtypes with the training data; remove target column only if the model expects features only. |
| Downloaded artifacts are not where expected | `dst_path` defaulted or MLflow returned a nested local artifact path. | Pass an explicit destination and inspect `downloaded_files` before using the artifacts. |

## MLflow UI and local process failures

| Symptom | Likely cause | Recovery steps |
|---|---|---|
| UI launches on a different port | Requested port was busy; launcher scans for a free port at or above the requested value. | Read the returned URL/port and report that exact value. |
| UI launch fails with command not found | `mlflow` CLI is not installed or not on PATH. | Install/repair MLflow in the active environment; verify `python -m mlflow --help` or equivalent before launching. |
| UI status says not detected but UI appears open | Process enumeration permissions, different port, or different host. | Check the returned process/port data, browser URL, and actual launch message. |
| Stop UI returns permission denied | Current user cannot enumerate or kill the process. | Ask the user to stop it manually or run with appropriate permissions; do not escalate automatically. |
| Stop UI would kill an unrelated service | Another process is listening on the selected port. | Confirm process details with the user before calling `mlflow_stop_ui`; never stop shared ports blindly. |

## LLM-backed agent failures

| Symptom | Likely cause | Recovery steps |
|---|---|---|
| `H2OMLAgent` or `MLflowToolsAgent` makes no useful tool/model call | User instructions were vague, LLM did not choose a tool, or provider call failed. | Use direct deterministic APIs for the desired operation, or restate instructions with explicit tool/action names and required arguments. |
| External provider/API-key error | Caller-provided model object needs credentials/network. | Ask the user to configure the provider externally; do not print or request secrets in logs. |
| Natural-language MLflow request mutates state unexpectedly | Agent interpreted the request as a logging/management operation. | Prefer direct read-only tools for inspection; review `get_tool_calls()` and MLflow state before reporting. |
| Generated H2O code is unsafe or too broad | LLM-generated code followed vague instructions or large defaults. | Review `get_h2o_train_function()`, constrain `max_models`, `max_runtime_secs`, `exclude_algos`, paths, and MLflow settings; rerun with explicit instructions. |

## Reporting unresolved gaps

If optional dependencies are not installed or services are not authorized, report precisely:

- Which imports passed or failed.
- Whether H2O cluster startup/training was attempted.
- Whether MLflow tracking was read-only or mutating.
- Whether model saving/logging/prediction was verified.
- Which operation remains blocked by missing packages, Java, credentials, user consent, memory, or unavailable artifacts.
