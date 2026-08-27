# Install and Cross-cutting Troubleshooting

## When to read

Read this when a Lazy Predict import, optional dependency, CLI, GPU/Spark, or
package-version issue blocks a workflow before the task reaches a specific
modeling API.

## Base install

Lazy Predict is a Python package named `lazypredict` and imports as
`lazypredict`. The inspected package version was `0.3.0` and the package
metadata requires Python `>=3.9`.

```bash
pip install lazypredict
python - <<'PY'
import lazypredict
print(lazypredict.__version__)
PY
```

The base install covers the package import, `LazyClassifier`, `LazyRegressor`,
`LazyForecaster` base/sklearn forecasting paths, the CSV CLI, pandas/numpy data
handling, tqdm progress bars, joblib persistence, and scikit-learn estimators.

## Optional extras by task

Install extras only when the user asks for the feature or the selected workflow
requires it.

| Extra | Use it for | Notes |
|---|---|---|
| `boost` | XGBoost, LightGBM, CatBoost supervised and forecasting models | GPU still requires compatible CUDA-capable packages/hardware. |
| `mlflow` | automatic MLflow tracking when `MLFLOW_TRACKING_URI` is set | Does not start a server by itself. |
| `timeseries` | statsmodels/pmdarima statistical forecasters | Base forecasting still has Naive and sklearn lag-feature models. |
| `deeplearning` | LSTM/GRU time-series models via PyTorch | CUDA requires a CUDA-capable PyTorch build and hardware. |
| `foundation` | TimesFM foundation forecaster | May need Python 3.10-3.11 and local model weights for offline use. |
| `tune` | Optuna tuning backend | Keep `n_trials`, `timeout`, and `top_k` bounded. |
| `viz` | time-series plotting helpers | Requires matplotlib. |
| `explain` | SHAP explainability | Permutation importance works without SHAP. |
| `interpret` | Explainable Boosting Machine models | Adds InterpretML glass-box estimators when installed. |
| `flaml` | FLAML tuning backend | Use only when `tune_backend="flaml"` is requested. |
| `spark` | PySpark MLlib classes | Requires a working Spark/JVM runtime, not just package import. |
| `all` | broad local exploration | Avoid for minimal environments; it installs many optional stacks. |

## Bundled diagnostics

Run this package-level checker from any working directory:

```bash
python scripts/check_lazypredict_env.py --json
```

It reports the installed package version, CLI availability, selected public
module imports, optional dependency availability, and whether CUDA appears
available through PyTorch when PyTorch is installed. It does not install
packages, download model weights, start services, or require credentials.

## Common failures

### `ModuleNotFoundError: No module named 'lazypredict'`

Likely cause: the active Python is not the one where Lazy Predict was installed.
Run `python -m pip show lazypredict` and the import check with the same
`python` executable the user will use for the task. Do not assume a shell
activation changed the Python used by notebooks, services, or subprocesses.

### Optional model disappears from results

Likely causes: the optional package is not installed, the estimator failed and
`ignore_warnings=True` hid the warning, or a backend fallback changed the model
parameters. Inspect the estimator-specific `.errors` dictionary after `fit()`
and install only the needed extra.

### GPU requested but results still run on CPU

`use_gpu=True` is a request, not proof of GPU execution. Lazy Predict checks
CUDA availability through PyTorch for GPU parameter selection. Supported GPU
paths include XGBoost, LightGBM, CatBoost, cuML, LSTM/GRU, and TimesFM, but each
requires compatible optional dependencies and hardware. If GPU execution is a
hard requirement, first run the environment checker, then verify the framework's
own tiny CUDA operation before trusting benchmark results.

### Import succeeds but CLI command is missing

The console entry point is named `lazypredict`. If `python -c 'import
lazypredict'` succeeds but the command is not on `PATH`, run the CLI through the
same environment's scripts directory or reinstall the package into the active
environment. The [cli-and-integrations](../sub-skills/cli-and-integrations/SKILL.md)
sub-skill has a bundled CLI smoke helper.

### Spark, TimesFM, MLflow, or plotting failures

These are optional integration surfaces. Confirm the corresponding extra and
external runtime first: Spark/JVM for Spark classes, local TimesFM weights for
offline foundation forecasting, `MLFLOW_TRACKING_URI` and an installed MLflow
package for tracking, and matplotlib for plots. Do not treat a base package
install as validation of these optional paths.
