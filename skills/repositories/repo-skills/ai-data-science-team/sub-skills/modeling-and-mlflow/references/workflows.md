# Modeling and Evaluation Workflows

This file covers H2O AutoML training, deterministic evaluation, and H2O-to-MLflow handoff patterns for `ai-data-science-team`.

## Workflow 0: Dependency and side-effect gate

Before any modeling operation, decide which side effects are authorized.

| Question | Default | Escalate when |
|---|---|---|
| Is an LLM call allowed? | No. | `H2OMLAgent` or `MLflowToolsAgent` is required. |
| Is H2O training allowed? | No. | The user asks to train AutoML or evaluate a model that must be loaded from H2O. |
| Are model/log writes allowed? | No. | The user asks to persist best models, generated code, MLflow artifacts, or downloaded artifacts. |
| Is MLflow mutation allowed? | No. | Creating experiments, logging metrics/artifacts, transitioning model stages, or starting runs is required. |
| Is a local service/process allowed? | No. | Launching the MLflow UI or starting H2O for training/evaluation is requested. |

Safe readiness check:

```bash
python sub-skills/modeling-and-mlflow/scripts/check_ml_optional_imports.py
```

If H2O or MLflow is missing, see [optional dependencies](optional-dependencies.md) and [troubleshooting](troubleshooting.md).

## Workflow 1: Prepare a DataFrame for H2O AutoML

H2O workflows operate on tabular pandas data. Upstream cleaning and feature engineering belong in sibling sub-skills; this sub-skill only checks modeling-readiness.

```python
import pandas as pd

TARGET = "target"
df = ...  # already loaded and cleaned pandas DataFrame

if not isinstance(df, pd.DataFrame) or df.empty:
    raise ValueError("H2O AutoML requires a non-empty pandas DataFrame.")
if TARGET not in df.columns:
    raise ValueError(f"Target column {TARGET!r} is not present.")
if df[TARGET].notna().sum() == 0:
    raise ValueError(f"Target column {TARGET!r} has no non-null values.")
if df[TARGET].dropna().nunique() < 2:
    raise ValueError(f"Target column {TARGET!r} must have at least two values/classes.")

# Keep identifiers or leakage-prone columns out of the training data when appropriate.
training_df = df.drop(columns=["row_id"], errors="ignore")
```

Classification target hints:

- String, categorical, and boolean targets are treated as classification by the package's evaluation helper.
- Low-cardinality integer targets can be treated as classification by the evaluator; tell H2O explicitly when class semantics matter.
- For binary classification, ensure the intended positive label is understandable. The evaluator prefers labels like `yes`, `true`, `1`, `churn`, or `positive`; otherwise it falls back to a stable label choice.

Regression target hints:

- Numeric continuous targets are evaluated with RMSE, MAE, and R².
- Do not use classification-only H2O metrics such as AUC/logloss for regression tasks.

## Workflow 2: Bounded H2O AutoML with `H2OMLAgent`

Use this when the user wants the package's LLM-assisted agent to generate and execute the H2O AutoML function.

```python
from ai_data_science_team.ml_agents import H2OMLAgent

llm = ...  # caller-provided; do not construct provider clients silently

agent = H2OMLAgent(
    model=llm,
    n_samples=30,
    log=False,
    model_directory=None,
    human_in_the_loop=False,
    bypass_recommended_steps=True,
    bypass_explain_code=True,
    enable_mlflow=False,
)

agent.invoke_agent(
    data_raw=training_df,
    target_variable=TARGET,
    user_instructions=(
        "Train an H2O AutoML model for the target column. "
        "Use seed=42, max_models=3, max_runtime_secs=60, "
        "and exclude DeepLearning unless explicitly needed."
    ),
    max_retries=3,
    retry_count=0,
)

leaderboard = agent.get_leaderboard()
best_model_id = agent.get_best_model_id()
model_path = agent.get_model_path()
generated_function = agent.get_h2o_train_function()
```

Validation after invocation:

```python
response = agent.response or {}
error = response.get("h2o_ml_error") or response.get("error")
if error:
    raise RuntimeError(error)

if leaderboard is None or getattr(leaderboard, "empty", False):
    raise RuntimeError("H2O AutoML did not return a leaderboard.")
if not best_model_id:
    raise RuntimeError("H2O AutoML did not return a best_model_id.")
```

When to disable bypasses:

- Set `bypass_recommended_steps=False` when the user wants the agent's modeling plan.
- Set `bypass_explain_code=False` when the user wants a code explanation.
- Enable `human_in_the_loop=True` only in interactive workflows with a checkpointer strategy.

## Workflow 3: Direct `train_h2o_automl` tool use

Use this when an explicit tool call is preferable to the full H2O agent. This still trains models and starts/uses H2O.

```python
import json
from ai_data_science_team.tools.h2o import train_h2o_automl

payload = {
    "data_raw": training_df.to_dict(orient="records"),
    "target": TARGET,
    "max_runtime_secs": 60,
    "max_models": 3,
    "seed": 42,
    "exclude_algos": ["DeepLearning"],
    "nfolds": 5,
    "sort_metric": "AUC",      # classification; use RMSE/MAE style choices for regression
    "stopping_metric": "logloss",
    "model_directory": None,
    "log_path": None,
    "enable_mlflow": False,
}

# LangChain tool invocation style; exact returned wrapper can vary by LangChain version.
result = train_h2o_automl.invoke(payload)
content = result[0] if isinstance(result, tuple) else result
parsed = json.loads(content) if isinstance(content, str) else content
```

Expected parsed keys: `leaderboard`, `best_model_id`, `model_path`, `model_results`, and `mlflow_run_id`.

## Workflow 4: Save a model only when persistence is requested

The package skips saving when both `model_directory` and `log_path` are absent. To persist a best model, provide a task-scoped directory.

```python
agent = H2OMLAgent(
    model=llm,
    log=False,
    model_directory="./models/h2o_best",
    enable_mlflow=False,
)
agent.invoke_agent(data_raw=training_df, target_variable=TARGET, user_instructions="Use max_models=3 and seed=42.")
model_path = agent.get_model_path()
```

Model persistence considerations:

- Saved H2O model artifacts are tied to the H2O runtime/version. Record H2O and package versions in experiment notes.
- `best_model_id` can work in the current H2O cluster session; `model_path` is more reliable across sessions.
- Use explicit user-approved output directories; do not write to broad project roots by default.

## Workflow 5: Deterministic evaluation with `ModelEvaluationAgent`

Use this after training when the user asks for metrics, confusion matrix, ROC, or residual diagnostics.

```python
from langchain_core.messages import HumanMessage
from ai_data_science_team.ml_agents import ModelEvaluationAgent

model_artifacts = {
    "model_path": model_path,
    "best_model_id": best_model_id,
}

evaluator = ModelEvaluationAgent()
evaluator.invoke_messages(
    [HumanMessage(content="Evaluate the trained model.")],
    data_raw=training_df,
    model_artifacts=model_artifacts,
    target_variable=TARGET,
    test_size=0.2,
    random_state=42,
)

eval_artifacts = evaluator.get_eval_artifacts()
plotly_graph = (evaluator.response or {}).get("plotly_graph")
message = (evaluator.response or {}).get("messages", [])[-1].content
```

Interpretation rules:

- `evaluation_source="cross_validation_holdout"` is preferred when H2O supplies cross-validation holdout predictions.
- `evaluation_source="random_split_in_sample"` means predictions came from a deterministic random split but may be optimistic if the H2O model was trained on all rows.
- Classification outputs can include `accuracy`, `precision`, `recall`, `f1`, `auc`, `positive_label`, `confusion_matrix`, and `roc_curve`.
- Regression outputs include `rmse`, `mae`, and `r2` plus a residual plot.

Escalate to the user if evaluation returns a message asking for a missing target, a valid model path, or H2O availability.

## Workflow 6: Log H2O training to MLflow

Only enable MLflow after dependency checks and tracking destination approval.

```python
tracking_uri = "file:./mlruns"  # example local tracking destination

agent = H2OMLAgent(
    model=llm,
    log=False,
    model_directory="./models/h2o_best",
    enable_mlflow=True,
    mlflow_tracking_uri=tracking_uri,
    mlflow_experiment_name="H2O AutoML",
    mlflow_run_name="bounded-h2o-automl",
)
agent.invoke_agent(
    data_raw=training_df,
    target_variable=TARGET,
    user_instructions="Train a bounded model with max_models=3, max_runtime_secs=60, seed=42.",
)

run_id = (agent.response or {}).get("mlflow_run_id")
model_uri = (agent.response or {}).get("mlflow_model_uri")
```

Post-run checks:

```python
from ai_data_science_team.tools.mlflow import mlflow_get_run_details, mlflow_list_artifacts

if run_id:
    details_msg, details = mlflow_get_run_details.invoke({"run_id": run_id, "tracking_uri": tracking_uri})
    artifacts_msg, artifacts = mlflow_list_artifacts.invoke({"run_id": run_id, "tracking_uri": tracking_uri})
```

If MLflow logging succeeds but model logging fails, check [troubleshooting](troubleshooting.md#mlflow-model-logging-or-prediction-fails). The package tries to record leaderboard, metrics, parameters, and model metadata even when the model flavor API differs across MLflow versions.

## Workflow 7: Use `MLflowToolsAgent` for natural-language MLflow work

Use this only when an LLM-backed tool-calling workflow is appropriate.

```python
from ai_data_science_team.ml_agents import MLflowToolsAgent

mlflow_agent = MLflowToolsAgent(
    model=llm,
    mlflow_tracking_uri="file:./mlruns",
    log_tool_calls=True,
)
mlflow_agent.invoke_agent("List recent runs in the H2O AutoML experiment.")
summary = mlflow_agent.get_ai_message()
artifacts = mlflow_agent.get_mlflow_artifacts(as_dataframe=False)
tool_calls = mlflow_agent.get_tool_calls()
```

Guardrails for natural-language MLflow operations:

- Read-only prompts are acceptable after the user approves the tracking URI.
- For mutations, ask for explicit consent if the user request is ambiguous: create experiment, log metrics/artifacts, transition registry stage, download artifacts, launch UI, or stop UI.
- Inspect `tool_calls` before reporting success; a natural-language answer with no tool call may not prove that MLflow state changed.

## Workflow 8: Predict from an MLflow run id

The prediction tool expects a run with a logged PyFunc-compatible model at `runs:/<run_id>/model` and data supplied to the agent/tool state.

Agent route:

```python
mlflow_agent.invoke_agent(
    user_instructions="Predict with run id <RUN_ID> on the provided rows.",
    data_raw=scoring_df,
)
predictions = mlflow_agent.get_mlflow_artifacts()
```

Direct route:

```python
from ai_data_science_team.tools.mlflow import mlflow_predict_from_run_id

msg, prediction_artifact = mlflow_predict_from_run_id.invoke({
    "run_id": "<RUN_ID>",
    "data_raw": scoring_df.to_dict(),
    "tracking_uri": "file:./mlruns",
})
```

If prediction fails, verify the run actually has a `model` artifact, the model is PyFunc-loadable, and the scoring DataFrame columns match the training signature or model expectations.

## Workflow 9: Integrate with upstream and supervisor sub-skills

Use this sub-skill as the modeling/evaluation leaf in larger workflows:

1. Load or query data with `data-access-and-eda` or `sql-analysis`.
2. Clean, wrangle, and engineer features with `dataframe-code-agents`.
3. Train/evaluate/log here.
4. Return model artifacts, metrics, and MLflow run ids to `multiagent-and-app-workflows` only when the user wants a supervisor/app flow.

Do not duplicate feature generation or app-launch guidance here. Keep this sub-skill focused on H2O, deterministic evaluation, MLflow, and optional ML dependency triage.
