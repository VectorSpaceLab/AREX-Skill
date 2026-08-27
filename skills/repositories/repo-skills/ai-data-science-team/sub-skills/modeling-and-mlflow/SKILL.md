---
name: modeling-and-mlflow
description: "Operate ai-data-science-team H2O AutoML, deterministic model
  evaluation, MLflow tools, and optional ML dependency checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Modeling and MLflow

Use this sub-skill when the task is to train or inspect H2O AutoML workflows, evaluate a trained H2O model deterministically, manage MLflow experiments/runs/models with the package tools, or troubleshoot optional ML dependencies for `ai-data-science-team`.

## Route here for

- `H2OMLAgent`, `make_h2o_ml_agent`, and the `train_h2o_automl` LangChain tool.
- Dataset/target validation before H2O AutoML training and safe extraction of leaderboard, best model id, model path, generated function, recommended steps, and log summary.
- Deterministic holdout evaluation with `ModelEvaluationAgent`, including classification metrics, regression metrics, confusion matrix, ROC curve when available, and residual plots.
- `MLflowToolsAgent`, `make_mlflow_tools_agent`, and direct `ai_data_science_team.tools.mlflow` helpers for experiment/run search, logging, artifacts, prediction, model registry, and UI status.
- Optional dependency triage for `h2o`, `mlflow`, Java/H2O runtime, local MLflow UI/process issues, and import-time notebook display helpers.

## Route away

- For data loading, EDA summaries, and optional EDA reports before modeling, use the sibling `data-access-and-eda` sub-skill.
- For feature engineering, generated pandas code, wrangling, cleaning, or visualization before training, use the sibling `dataframe-code-agents` sub-skill.
- For supervisor teams, Streamlit apps, or cross-agent orchestration around modeling, use the sibling `multiagent-and-app-workflows` sub-skill.
- For SQL-backed feature extraction, use the sibling `sql-analysis` sub-skill first, then return here with a pandas DataFrame.

## Safe operating defaults

1. Treat H2O and MLflow as optional extras. Run the bundled optional import check before promising runtime availability.
2. Do not launch the MLflow UI, kill UI processes, start H2O training, download artifacts, or write model/log artifacts unless the user explicitly asked for that side effect.
3. Keep AutoML bounded with `max_runtime_secs`, `max_models`, `seed`, and usually `exclude_algos=["DeepLearning"]` for quick local experiments.
4. Prefer explicit `target_variable`/`target` and verify the target exists, has non-null values, and has at least two classes for classification.
5. Use local/disposable MLflow tracking locations for experiments unless the user provides and authorizes a remote tracking/registry URI.
6. Never embed API keys, service tokens, tracking-server credentials, local environment prefixes, or absolute checkout paths in generated logs or reports.

## Quick routes

### Check optional ML readiness without side effects

```bash
python sub-skills/modeling-and-mlflow/scripts/check_ml_optional_imports.py
python sub-skills/modeling-and-mlflow/scripts/check_ml_optional_imports.py --inspect-public-apis --require h2o mlflow
```

The script only checks imports, package metadata, public signatures, and Java availability. It does not train, start H2O, launch MLflow, call an LLM, download data, or write artifacts.

### Train with H2OMLAgent when the caller supplies an LLM

```python
from ai_data_science_team.ml_agents import H2OMLAgent

llm = ...  # caller-provided LangChain-compatible chat model
df = ...   # pandas DataFrame already loaded and cleaned

agent = H2OMLAgent(
    model=llm,
    log=False,
    model_directory=None,
    enable_mlflow=False,
    bypass_recommended_steps=True,
    bypass_explain_code=True,
)
agent.invoke_agent(
    data_raw=df,
    target_variable="target",
    user_instructions="Train a bounded H2O AutoML model; use max_models=3 and seed=42.",
)

leaderboard = agent.get_leaderboard()
best_model_id = agent.get_best_model_id()
model_path = agent.get_model_path()
```

Use [workflows](references/workflows.md) before enabling model saving, MLflow logging, human review, or large AutoML budgets.

### Evaluate a trained H2O model deterministically

```python
from langchain_core.messages import HumanMessage
from ai_data_science_team.ml_agents import ModelEvaluationAgent

model_artifacts = {
    "model_path": agent.get_model_path(),
    "best_model_id": agent.get_best_model_id(),
}
evaluator = ModelEvaluationAgent()
evaluator.invoke_messages(
    [HumanMessage(content="Evaluate the trained model on a holdout split.")],
    data_raw=df,
    model_artifacts=model_artifacts,
    target_variable="target",
    test_size=0.2,
    random_state=42,
)
artifacts = evaluator.get_eval_artifacts()
```

`ModelEvaluationAgent` does not need an LLM response to compute metrics, but it does need H2O available and a resolvable saved model path or H2O model id.

### Inspect MLflow without natural-language tool calling

```python
from ai_data_science_team.tools.mlflow import mlflow_tracking_info, mlflow_search_experiments

tracking_msg, tracking_artifact = mlflow_tracking_info.invoke({})
experiments_msg, experiments_artifact = mlflow_search_experiments.invoke({"filter_string": None})
```

Use the direct tools for deterministic scripting. Use `MLflowToolsAgent` only when the user wants natural-language MLflow operations and supplies an LLM.

## References and bundled checks

- [API reference](references/api-reference.md): public imports, constructor signatures, response fields, and API boundaries.
- [Workflows](references/workflows.md): H2O AutoML training, deterministic evaluation, H2O-to-MLflow logging, and validation patterns.
- [MLflow tools](references/mlflow-tools.md): tool catalog, safe direct use, agent use, UI/process behavior, artifacts, prediction, and registry operations.
- [Optional dependencies](references/optional-dependencies.md): extras, runtime expectations, Java/H2O notes, and dependency gates.
- [Troubleshooting](references/troubleshooting.md): symptoms, likely causes, and recovery steps for optional ML workflows.
- [Optional import check](scripts/check_ml_optional_imports.py): safe readiness checker with no LLM call, service launch, download, training, or destructive write.
