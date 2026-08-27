# Engine Workflow Recipes

## Purpose

Use these recipes to complete common PyCaret 4.0 engine tasks without reopening the original repository. Examples are OOP-only and avoid network by default. They use sklearn toy data or inline frames instead of `pycaret.datasets.get_data(...)`.

For signatures and result fields, read [api-reference.md](api-reference.md). For failures, read [troubleshooting.md](troubleshooting.md).

## Validate the local engine first

From this sub-skill directory:

```bash
python scripts/engine_smoke.py --help
python scripts/engine_smoke.py --task classification --list-models
python scripts/engine_smoke.py --task all
python scripts/introspection_snapshot.py --task classification --task regression
```

Expected signals:

- `engine_smoke.py` prints one JSON object per selected task with `status: "ok"`.
- For classification/regression it reports prediction columns that include `prediction_label`.
- For clustering it reports `Cluster`.
- For anomaly it reports `Anomaly` and usually `Anomaly_Score`; if `pyod` is missing, install `pycaret[anomaly]`.
- For time series it reports prediction columns containing `y_pred`; if `sktime`/`statsmodels`/`pmdarima` are missing, install `pycaret[timeseries]`.

## Classification recipe

Use this for binary or multiclass target prediction.

```python
import pandas as pd
from sklearn.datasets import load_breast_cancer

from pycaret.tasks import ClassificationExperiment
from pycaret.logging import MemoryLogger

raw = load_breast_cancer(as_frame=True)
df = raw.frame.rename(columns={"target": "label"})

logger = MemoryLogger(file="classification-events.jsonl")
exp = ClassificationExperiment(
    target="label",
    session_id=42,
    fold=3,
    n_jobs=1,
    logger=logger,
).fit(df)

created = exp.create_model("lr", verbose=False)
assert created.model_id == "lr"
assert created.pipeline is not None
assert created.metrics is not None

compare = exp.compare_models(include=["lr", "dt"], n_select=2, verbose=False)
best = compare.best
leaderboard = compare.leaderboard
ranked_ids = compare.ranked_ids

# Tune the selected pipeline. Keep n_iter small in examples and CI.
tuned = exp.tune_model(best, n_iter=3, optimize="Accuracy", verbose=False)

# Holdout predictions because data=None.
preds = exp.predict_model(tuned.pipeline, verbose=False)
print(preds.predictions[["prediction_label"]].head())
print(preds.metrics)

# Per-class probabilities for binary or multiclass classification.
raw_scores = exp.predict_model(tuned.pipeline, raw_score=True, verbose=False).predictions
score_cols = [c for c in raw_scores.columns if c.startswith("prediction_score_")]

# Plotly figure; call fig.show() only in notebooks or interactive sessions.
fig = exp.plot_model(tuned.pipeline, plot="confusion_matrix")
fig_dict = fig.to_dict()

# Event trace for a UI or audit log.
event_payloads = [event.to_dict() for event in logger.events]
```

Validation checklist:

- `created` is `CreateResult`; `compare` is `CompareResult`; `tuned` is `TuneResult`; `preds` is `PredictResult`.
- `compare.leaderboard` has a `Model` column and metric columns such as `Accuracy` and `AUC`.
- `preds.predictions` includes `prediction_label`; binary classifiers with probability support include `prediction_score` by default.
- `logger.events` includes `experiment.started`, `experiment.fitted`, and model operation events.

Common variants:

```python
# Use (X, y) instead of a target column.
X = df.drop(columns=["label"])
y = df["label"].rename("label")
exp = ClassificationExperiment(session_id=42, fold=3, n_jobs=1).fit(X, y)

# Preserve more candidates; turbo=False includes slower models.
compare = exp.compare_models(include=["lr", "dt", "knn", "rbfsvm"], turbo=False)

# Probability calibration is classification-only.
calibrated = exp.calibrate_model(created.pipeline, method="sigmoid")

# Full-data refit after evaluation.
final = exp.finalize_model(tuned.pipeline).pipeline
```

## Regression recipe

Use this for continuous targets.

```python
import pandas as pd
from sklearn.datasets import load_diabetes

from pycaret.tasks import RegressionExperiment

raw = load_diabetes(as_frame=True)
df = raw.frame.rename(columns={"target": "y"})

exp = RegressionExperiment(
    target="y",
    session_id=42,
    fold=3,
    n_jobs=1,
    normalize=True,
).fit(df)

created = exp.create_model("lr", verbose=False)
compare = exp.compare_models(include=["lr", "ridge", "dt"], sort="R2", n_select=2, verbose=False)
tuned = exp.tune_model(compare.best, n_iter=3, optimize="R2", verbose=False)
preds = exp.predict_model(tuned.pipeline, verbose=False)

print(compare.leaderboard)
print(preds.predictions[["prediction_label"]].head())
print(preds.metrics)

figs = exp.evaluate_model(tuned.pipeline)
# figs is a dict such as {"residuals": Figure, "prediction_error": Figure, ...}
```

Validation checklist:

- `compare.leaderboard` is sorted descending by `R2` unless you pass an error metric such as `MAE`, which sorts ascending.
- Regression predictions include `prediction_label` and do not include `prediction_score`.
- `plot_model(..., plot="residuals")`, `plot_model(..., plot="prediction_error")`, and `evaluate_model(...)` return Plotly figures.

Common variants:

```python
# Rank by lower-is-better metric.
compare = exp.compare_models(include=["lr", "ridge"], sort="MAE", verbose=False)

# Custom grid with un-prefixed sklearn estimator parameter names.
tuned = exp.tune_model(created.pipeline, custom_grid={"fit_intercept": [True, False]}, n_iter=2)

# Finalize before persistence or deployment.
final = exp.finalize_model(tuned.pipeline).pipeline
```

## Clustering recipe

Use this for unsupervised row grouping. There is no target column.

```python
import pandas as pd
from sklearn.datasets import make_blobs

from pycaret.tasks import ClusteringExperiment

X, _ = make_blobs(n_samples=90, centers=3, n_features=4, random_state=42)
df = pd.DataFrame(X, columns=["f0", "f1", "f2", "f3"])

exp = ClusteringExperiment(session_id=42, normalize=True, n_jobs=1).fit(df)

created = exp.create_model("kmeans", num_clusters=3, verbose=False)
labelled = exp.assign_model(created.pipeline)
new_preds = exp.predict_model(created.pipeline, data=df.head(5)).predictions

print(labelled[["Cluster"]].head())
print(new_preds[["Cluster"]])

fig = exp.plot_model(created.pipeline, plot="silhouette_plot")
```

Validation checklist:

- `created` is `CreateResult` and `created.metrics` is `None` for unsupervised v1.
- `assign_model` returns the original rows plus a `Cluster` column.
- `predict_model` on new data returns a `PredictResult` whose `predictions` include `Cluster`.
- Some clustering estimators do not support prediction on new data; use `assign_model` for training rows when in doubt.

Common variants:

```python
# Review runtime model registry after fit.
models_df = exp.models()

# Return transformed features plus cluster labels for debugging preprocessing.
transformed_labelled = exp.assign_model(created.pipeline, transformation=True)
```

## Anomaly detection recipe

Requires `pycaret[anomaly]` because the task registry uses PyOD.

```python
import numpy as np
import pandas as pd

from pycaret.tasks import AnomalyExperiment

rng = np.random.default_rng(42)
normal = rng.normal(0, 1, size=(80, 3))
outliers = rng.normal(7, 0.5, size=(5, 3))
df = pd.DataFrame(np.vstack([normal, outliers]), columns=["x0", "x1", "x2"])

exp = AnomalyExperiment(session_id=42, normalize=True, n_jobs=1).fit(df)
created = exp.create_model("iforest", fraction=0.06, verbose=False)
labelled = exp.assign_model(created.pipeline, score=True)

print(labelled[["Anomaly", "Anomaly_Score"]].tail())

# On new data, predict_model uses the fitted pipeline.
probe = pd.DataFrame([[0.1, -0.2, 0.0], [8.0, 7.5, 7.2]], columns=df.columns)
pred = exp.predict_model(created.pipeline, data=probe).predictions
print(pred)
```

Validation checklist:

- `assign_model(..., score=True)` includes `Anomaly` and `Anomaly_Score` when the estimator exposes scores.
- `Anomaly` labels are expected to be 0/1 for PyOD-backed models.
- If imports fail for PyOD or numba, install `pycaret[anomaly]` instead of changing the API shape.

Common variants:

```python
# Hide score column when it is not needed.
labelled = exp.assign_model(created.pipeline, score=False)

# Try other registered PyOD IDs after inspecting exp.models().
print(exp.models().index.tolist())
```

## Time-series forecasting recipe

Requires `pycaret[timeseries]` because the task uses sktime/statsmodels/pmdarima.

```python
import numpy as np
import pandas as pd

from pycaret.tasks import TimeSeriesExperiment

idx = pd.period_range("2020-01", periods=48, freq="M")
y = pd.Series(
    20 + 0.5 * np.arange(48) + 2 * np.sin(np.arange(48) * 2 * np.pi / 12),
    index=idx,
    name="value",
)

exp = TimeSeriesExperiment(fh=6, seasonal_period=12, fold=2, session_id=42, n_jobs=1).fit(y)

created = exp.create_model("naive", verbose=False)
forecast = exp.predict_model(created.pipeline)
print(forecast.predictions.head())
print(forecast.metrics)

compare = exp.compare_models(include=["naive", "snaive", "polytrend"], n_select=2, verbose=False)
print(compare.leaderboard)

# Tune a created pipeline; do not pass a registry string directly for TS tune_model.
tuned = exp.tune_model(created.pipeline, n_iter=2, verbose=False)

# Refit on full y before future forecasting.
final = exp.finalize_model(tuned.pipeline).pipeline
future = exp.predict_model(final, fh=[1, 2, 3], return_pred_int=False).predictions

# Statistical diagnostics.
stats = exp.check_stats(test="stationarity", split="train")
```

Validation checklist:

- `CreateResult.pipeline` is an sktime `ForecastingPipeline`.
- Forecast predictions include `y_pred`; with `return_pred_int=True`, include `lower` and `upper` when supported.
- Default leaderboard sorting is ascending by `MASE`.
- `check_stats` returns rows with columns such as `Test`, `Test Name`, `Data`, `Property`, `Setting`, and `Value`.

Time-series with exogenous variables:

```python
df = pd.DataFrame({
    "target": y,
    "promo": (np.arange(len(y)) % 6 == 0).astype(int),
}, index=idx)

exp = TimeSeriesExperiment(target="target", fh=6, seasonal_period=12, fold=2).fit(df)
model = exp.create_model("naive", verbose=False).pipeline
# For exogenous forecasting, pass future exogenous rows as X= or data=.
```

## Persistence workflow

Use top-level helpers for stateless model persistence:

```python
from pycaret import save_model, load_model

final_pipeline = exp.finalize_model(tuned.pipeline).pipeline
path = save_model(final_pipeline, "artifacts/final_model")
restored = load_model(path)

preds = exp.predict_model(restored, data=some_dataframe).predictions
```

Use experiment persistence only when you intentionally need fit state, split information, model registry snapshots, and logger state:

```python
exp_path = exp.save_experiment("artifacts/experiment_state")
restored_exp = type(exp).load_experiment(exp_path)
print(restored_exp.__sklearn_is_fitted__())
```

Validation checklist:

- `save_model` adds `.pkl` if missing and returns an absolute `Path`.
- A restored pipeline should produce predictions matching the original pipeline for the same input.
- `save_experiment` raises `NotFittedError` if called before `fit`.

## Event capture workflow

Use `MemoryLogger` when a workflow needs progress telemetry or later replay.

```python
from pycaret.logging import MemoryLogger
from pycaret.tasks import RegressionExperiment

log = MemoryLogger(file="run-events.jsonl")
received = []
unsubscribe = log.subscribe(received.append)
try:
    exp = RegressionExperiment(target="y", logger=log, session_id=42, fold=3, n_jobs=1).fit(df)
    result = exp.compare_models(include=["lr", "ridge"], verbose=False)
finally:
    unsubscribe()

# In-memory replay.
events = [event.to_dict() for event in log.events]

# Typical checks.
kinds = {event["kind"] for event in events}
assert "experiment.started" in kinds
assert "experiment.fitted" in kinds
assert "model.compare.finished" in kinds
```

Tips:

- Subscribers are synchronous. Keep callbacks lightweight.
- Always call the unsubscribe function in long-lived processes.
- `log_experiment=True` installs a `MemoryLogger` only when no explicit logger is passed; passing your own `MemoryLogger` is clearer.

## Introspection workflow

Use `pycaret.api` for static UI/agent context and fitted experiment methods for runtime registry details.

```python
import json

from pycaret.api import list_models, list_metrics, describe_model, describe_setup_params

context = {
    "models": [m.to_dict() for m in list_models("classification")],
    "metrics": [m.to_dict() for m in list_metrics("classification")],
    "setup_params": describe_setup_params("classification").to_dict(),
    "lr": describe_model("classification", "lr").to_dict(),
}
print(json.dumps(context, indent=2))
```

Runtime registry for task families whose static `list_models` is not populated:

```python
from pycaret.tasks import ClusteringExperiment

exp = ClusteringExperiment(session_id=42).fit(df)
models_df = exp.models()
metrics_df = exp.get_metrics()
```

Bundled script equivalent:

```bash
python scripts/introspection_snapshot.py --task classification --task regression --indent 2
python scripts/introspection_snapshot.py --task all --include-setup-params
```

## Sample data options

Recommended no-network options:

- sklearn toy data: `load_breast_cancer`, `load_diabetes`, `load_iris`, `make_blobs`, `make_regression`, `make_classification`.
- Tiny inline pandas DataFrames/Series for smoke tests.
- Project-owned CSV files only when the user explicitly provides a path.

`pycaret.datasets.get_data(name)` is still available, but it may read from the network unless a same-named CSV is present in the current working directory. Avoid it in public smoke examples unless network access is explicitly allowed.

## Final pre-handoff validation

Before telling a user a workflow is complete:

1. Confirm the object is fitted: `exp.__sklearn_is_fitted__()`.
2. Confirm the expected typed result class and key fields.
3. Confirm task-specific prediction columns.
4. Confirm metrics/leaderboard shape when the selected verb should produce metrics.
5. If persistence was used, load the artifact and run at least one prediction.
6. If event logging was required, inspect `event.to_dict()` records and check the relevant event kinds.
7. If an optional dependency path was used, record the required extra (`[anomaly]`, `[timeseries]`, `[interpret]`, or `[export]`).
