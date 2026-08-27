# Optional ML Dependencies

The base `ai-data-science-team` install exposes many package modules, but H2O AutoML and MLflow operations require optional ML packages that may not be installed in a minimum environment.

## Dependency groups

| Capability | Required package/runtime | Notes |
|---|---|---|
| Importing public agent modules | `IPython` display helpers plus base package dependencies | Agent getters can return `IPython.display.Markdown`; import failures can occur before H2O/MLflow checks if display helpers are missing. |
| H2O AutoML training | `h2o` Python package and a compatible Java runtime | `H2OMLAgent`, `make_h2o_ml_agent`, and `train_h2o_automl` check/import H2O before training. |
| H2O model evaluation | `h2o` plus base numeric/plot dependencies | `ModelEvaluationAgent` loads a saved H2O model or resolves a model id in a running H2O cluster. |
| MLflow tracking/tools | `mlflow` | `MLflowToolsAgent` imports MLflow at graph construction; direct MLflow tools import MLflow inside each tool. |
| MLflow UI status/stop | `psutil` and `mlflow` CLI for launch | `psutil` is used to inspect/kill local UI processes. |
| Metric/plot outputs | pandas, NumPy, scikit-learn, Plotly | These are base dependencies for evaluation metrics and Plotly figure dictionaries. |
| LLM-backed agents | LangChain/LangGraph plus a caller-provided chat model object | This skill does not create provider clients or supply credentials. |

The package's optional `machine_learning` extra corresponds to H2O and MLflow. In environments that support extras, install the equivalent of:

```bash
python -m pip install "ai-data-science-team[machine_learning]"
```

If the package is already installed from a local wheel/source, install the equivalent optional packages explicitly:

```bash
python -m pip install h2o mlflow
```

Use the package manager and environment policy chosen by the user or project. Do not mutate a shared environment without permission.

## Safe readiness checker

Run:

```bash
python sub-skills/modeling-and-mlflow/scripts/check_ml_optional_imports.py
```

Useful options:

```bash
# Fail non-zero if H2O or MLflow is unavailable.
python sub-skills/modeling-and-mlflow/scripts/check_ml_optional_imports.py --require h2o mlflow

# Also import public ai-data-science-team ML APIs and report signatures.
python sub-skills/modeling-and-mlflow/scripts/check_ml_optional_imports.py --inspect-public-apis

# Emit pretty human-readable output instead of JSON.
python sub-skills/modeling-and-mlflow/scripts/check_ml_optional_imports.py --format text
```

The script does not start H2O, launch MLflow, call an LLM, download anything, train models, or write files.

## H2O runtime expectations

H2O AutoML is not just a Python import. Training and evaluation can start or attach to a local H2O cluster and usually require Java.

Before training:

1. Check `h2o` import availability.
2. Check that a Java executable is available.
3. Decide the memory budget. H2O and XGBoost can need extra RAM; when XGBoost is enabled, leave memory headroom outside the H2O Java heap.
4. Bound runtime with `max_runtime_secs` and/or `max_models`.
5. For reproducibility, prefer explicit `max_models` and `seed`; time-budgeted AutoML can vary when machines are slow or busy.
6. For low-resource local runs, consider `exclude_algos=["DeepLearning"]` and smaller `max_models`.

H2O training side effects:

- Starts or attaches to an H2O cluster.
- May create temporary files managed by H2O.
- May write a model file if `model_directory` or `log_path` is provided.
- May log MLflow artifacts/metrics if `enable_mlflow=True`.

## MLflow runtime expectations

MLflow can operate with local file tracking or remote tracking/registry servers.

Before using MLflow tools:

1. Confirm `mlflow` import availability.
2. Confirm the tracking URI and registry URI, if any.
3. Confirm whether the operation is read-only or mutating.
4. For remote servers, ensure credentials are already configured outside this skill; do not ask the model to invent tokens.
5. For local file tracking, choose a task-scoped tracking directory and avoid broad home/project roots unless the user requested them.

MLflow tool side effects:

- `mlflow_search_*`, `mlflow_get_*`, `mlflow_list_*`, `mlflow_tracking_info`, and `mlflow_ui_status` are read-only with respect to MLflow state.
- `mlflow_create_experiment`, `mlflow_set_tags`, `mlflow_log_*`, `mlflow_transition_model_version_stage`, and H2O training with `enable_mlflow=True` mutate MLflow state.
- `mlflow_download_artifacts` writes files locally.
- `mlflow_launch_ui` starts a local subprocess.
- `mlflow_stop_ui` kills a local process listening on the selected port when permissions allow.

## LLM dependency boundary

`H2OMLAgent` and `MLflowToolsAgent` require a caller-supplied model object. They can call external LLM providers depending on that object. This sub-skill should not:

- Create provider clients without user authorization.
- Store API keys or credentials in code snippets.
- Treat MLflow or H2O dependency checks as permission to make LLM calls.
- Use natural-language MLflow operations for a deterministic scripted workflow when direct tools are sufficient.

## Minimum environment versus optional ML environment

A minimum environment can verify package import, data loading, EDA summaries, SQL safety, and Streamlit package availability without installing H2O or MLflow. That is not sufficient evidence for H2O AutoML or MLflow workflows.

When optional ML dependencies are absent:

- Keep this sub-skill usable for planning, API explanation, and dependency triage.
- Do not claim H2O training/evaluation or MLflow execution was verified.
- Use the checker script and the troubleshooting tables to provide concrete next steps.
- Mark H2O/MLflow runtime execution as optional/unverified in handoffs until installed and smoke-checked.

## Suggested lightweight smoke checks after installation

Only after the user authorizes optional dependencies:

```python
# Import-only smoke checks: no training, UI, or tracking mutation.
import h2o
import mlflow
from ai_data_science_team.ml_agents import H2OMLAgent, ModelEvaluationAgent, MLflowToolsAgent
from ai_data_science_team.tools.h2o import train_h2o_automl
from ai_data_science_team.tools.mlflow import mlflow_tracking_info

print(h2o.__version__)
print(mlflow.__version__)
print(mlflow_tracking_info.invoke({})[0])
```

Do not run AutoML or launch MLflow UI as an installation check unless the user explicitly asks for that side effect.
