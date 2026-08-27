# Integration Reference

`optuna.integration` contains lazy import shims for third-party framework integrations. In current Optuna, many integrations are implemented in the separate `optuna-integration` package and may also require the framework package itself.

## Import Routing Rule

Use `optuna.integration` only when the task is specifically about a third-party framework callback, estimator, or storage adapter. If the task is just a normal objective loop, route to `../optimization-workflows/SKILL.md` and write plain Optuna code.

Common imports:

```python
from optuna.integration import LightGBMPruningCallback
from optuna.integration import XGBoostPruningCallback
from optuna.integration import MLflowCallback
from optuna.integration import OptunaSearchCV
from optuna.integration import WeightsAndBiasesCallback
```

Many historical module paths are compatibility shims. When an import warning says to use `optuna_integration.<name>`, prefer installing and importing from `optuna-integration` for new integration-heavy code if the user accepts the extra dependency.

## Dependency Map

The base Optuna installation does not guarantee any of these optional packages. Probe or document requirements before using them.

| Integration surface | Primary object(s) | Typical extra dependencies |
| --- | --- | --- |
| BoTorch | `BoTorchSampler` | `botorch`, `gpytorch`, `torch` |
| CatBoost | `CatBoostPruningCallback` | `catboost` |
| pycma | `PyCmaSampler` | `cma` |
| Dask | `DaskStorage` | `distributed` |
| FastAI | `FastAIV2PruningCallback`, `FastAIPruningCallback` | `fastai` |
| Keras | `KerasPruningCallback` | `keras` |
| LightGBM | `LightGBMPruningCallback`, `LightGBMTuner`, `LightGBMTunerCV` | `optuna-integration`, `lightgbm`, sometimes `scikit-learn` |
| MLflow | `MLflowCallback` | `optuna-integration`, `mlflow` |
| PyTorch distributed | `TorchDistributedTrial` | `torch` |
| PyTorch Ignite | `PyTorchIgnitePruningHandler` | `pytorch-ignite`, `torch` |
| PyTorch Lightning | `PyTorchLightningPruningCallback` | `pytorch-lightning`, `torch` |
| SHAP | `ShapleyImportanceEvaluator` | `shap`, `scikit-learn` |
| scikit-learn | `OptunaSearchCV` | `pandas`, `scipy`, `scikit-learn` |
| skorch | `SkorchPruningCallback` | `skorch`, `torch` |
| TensorBoard | `TensorBoardCallback` | `tensorboard`, `tensorflow` |
| TensorFlow | `TensorFlowPruningHook`, `TFKerasPruningCallback` | `tensorflow`, sometimes `tensorflow-estimator` |
| Weights & Biases | `WeightsAndBiasesCallback` | `wandb` |
| XGBoost | `XGBoostPruningCallback` | `optuna-integration`, `xgboost` |

## Optional Dependency Probe

Use import probes before selecting integration code paths in generated examples, CLIs, or tests:

```python
import importlib.util

missing = [
    name
    for name in ["optuna_integration", "lightgbm"]
    if importlib.util.find_spec(name) is None
]
if missing:
    print("Missing optional dependencies:", ", ".join(missing))
    print("Falling back to plain Optuna objective without framework callback.")
else:
    from optuna.integration import LightGBMPruningCallback
```

This avoids turning an optional framework integration into a hard dependency for local artifact or core optimization workflows.

## Callback Pattern

Most pruning callbacks bridge the framework's evaluation loop to these Optuna trial methods:

- `trial.report(value, step)` records an intermediate metric.
- `trial.should_prune()` asks the study pruner whether to stop the trial.
- The callback raises `optuna.TrialPruned` or a framework-specific pruning signal when pruning should happen.

When a framework callback is unavailable, implement the same pattern manually inside the objective if the training loop exposes validation metrics:

```python
for step in range(num_steps):
    metric = train_one_step_and_evaluate(...)
    trial.report(metric, step)
    if trial.should_prune():
        raise optuna.TrialPruned()
```

## Service and Credential Boundaries

- MLflow, Weights & Biases, TensorBoard, Dask, S3, and GCS may contact local or remote services. Do not run service-backed examples unless the user has provided configuration and approval.
- Keep tokens, service URLs, and credentials outside committed code. Use environment variables or each tool's standard credential configuration.
- For fallback examples, show plain Optuna plus `FileSystemArtifactStore` rather than requiring external services.
- If the task asks for visualization or parameter importances rather than framework callbacks, route to `../analysis-visualization/SKILL.md`.

## Import Failure Triage

If `from optuna.integration import ...` fails:

1. Confirm whether `optuna-integration` is installed.
2. Confirm the target framework package is installed.
3. Check for deprecation warnings that recommend `optuna_integration.<module>` imports.
4. If optional dependencies are intentionally absent, replace the integration callback with manual `trial.report` / `trial.should_prune` logic or skip the integration-specific path.
