# Model and Task Overview

## Purpose

Read this before choosing a PyCaret task class, model ID, metric, optional extra, or backend plan for direct engine work. For exact signatures, see [api-reference.md](api-reference.md). For runnable recipes, see [workflows.md](workflows.md).

## Task selection table

| User intent | Task class | Required target? | Primary verbs | Prediction/assignment output |
| --- | --- | --- | --- | --- |
| Predict a class label or probability | `ClassificationExperiment` | Yes | `fit`, `create_model`, `compare_models`, `tune_model`, `predict_model`, `calibrate_model`, `plot_model` | `prediction_label`, usually `prediction_score` |
| Predict a continuous value | `RegressionExperiment` | Yes | `fit`, `create_model`, `compare_models`, `tune_model`, `predict_model`, `finalize_model`, `plot_model` | `prediction_label` |
| Group unlabeled rows | `ClusteringExperiment` | No | `fit`, `create_model`, `assign_model`, `predict_model`, `plot_model` | `Cluster` |
| Detect outlier rows | `AnomalyExperiment` | No | `fit`, `create_model`, `assign_model`, `predict_model`, `plot_model` | `Anomaly`, optionally `Anomaly_Score` |
| Forecast a time-indexed series | `TimeSeriesExperiment` | Optional for univariate input; required for multicolumn DataFrame | `fit`, `create_model`, `compare_models`, `tune_model`, `predict_model`, `finalize_model`, `check_stats`, `plot_model` | `y_pred`, optionally `lower`, `upper` |

Task strings accepted by `pycaret.api`: `classification`, `regression`, `clustering`, `anomaly`, `time_series`.

## Required and optional dependencies

Minimum install for verified CPU tabular engine workflows:

```bash
pip install pycaret
```

Task or feature extras:

```bash
pip install "pycaret[anomaly]"      # PyOD anomaly detectors
pip install "pycaret[timeseries]"   # sktime/statsmodels/pmdarima forecasting
pip install "pycaret[interpret]"    # SHAP explanations
pip install "pycaret[export]"       # kaleido static Plotly export
pip install "pycaret[notebook]"     # notebook widget/artifact helpers
```

Backend facts:

- CPU is the required backend for this generated skill and is enough for all smoke workflows here.
- CUDA hardware may be present on a host, but optional GPU model stacks were not selected for required verification.
- `use_gpu=True` does not install GPU packages. Treat GPU-enabled model cards as optional acceleration candidates that require explicit package/backend validation.
- Anomaly and time-series extras are required for their task families even on CPU.

## OOP-only API boundary

PyCaret 4.0 direct engine usage is OOP-only:

```python
from pycaret.tasks import ClassificationExperiment
exp = ClassificationExperiment(target="label").fit(df)
result = exp.compare_models()
```

Do not write PyCaret 3.x functional code or import removed helper functions such as module-level `setup`, `compare_models`, or a global `pull`. Translate those requests immediately into an OOP experiment object and instance methods.

`pull()` still exists as `exp.pull()` for recent metrics/leaderboards, but typed result fields are the primary API:

```python
compare = exp.compare_models()
leaderboard = compare.leaderboard
best = compare.best
```

## Model IDs: practical starting points

Use `exp.models()` after `fit` for the authoritative runtime registry. Use `pycaret.api.list_models(task)` for static classification/regression context.

### Classification

Common model IDs:

- Linear/probabilistic: `lr`, `ridge`, `lda`, `qda`, `nb`.
- Neighbors/kernel/neural: `knn`, `svm`, `rbfsvm`, `gpc`, `mlp`.
- Trees/ensembles: `dt`, `rf`, `et`, `ada`, `gbc`.
- Optional boosted libraries: `xgboost`, `lightgbm`, `catboost`.
- Baseline: `dummy`.

Guidance:

- Start smoke tests with `include=["lr", "dt"]` and `fold=3`.
- `turbo=True` skips known-slow IDs such as `rbfsvm`, `gpc`, and `mlp` in default supervised comparison.
- Use `raw_score=True` in `predict_model` when you need one probability column per class.
- Use `calibrate_model` only for classification.

### Regression

Common model IDs:

- Linear/regularized: `lr`, `lasso`, `ridge`, `en`, `lar`, `llar`, `omp`, `br`, `ard`, `par`.
- Robust/kernel/neighbors: `ransac`, `tr`, `huber`, `kr`, `svm`, `knn`.
- Trees/ensembles: `dt`, `rf`, `et`, `ada`, `gbr`.
- Optional boosted libraries: `xgboost`, `lightgbm`, `catboost`.
- Neural/baseline: `mlp`, `dummy`.

Guidance:

- Start smoke tests with `include=["lr", "ridge"]` and `fold=3`.
- Default comparison sort is `R2` descending. Error metrics such as `MAE`, `MSE`, and `RMSE` sort ascending.
- Regression predictions do not include `prediction_score`.

### Clustering

Runtime registry model IDs include:

- `kmeans`, `ap`, `meanshift`, `sc`, `hclust`, `dbscan`, `optics`, `birch`, `kmodes`.

Guidance:

- Start with `kmeans` and an explicit `num_clusters` on small data.
- `assign_model` is the primary training-row labeling verb and returns a DataFrame with `Cluster`.
- Some clustering algorithms cannot predict new rows. If `predict_model` fails, use a model that supports `.predict` or restrict the task to assigning labels on the fitted dataset.

### Anomaly detection

Requires `pycaret[anomaly]`. Runtime registry model IDs include:

- `abod`, `cluster`, `cof`, `iforest`, `histogram`, `knn`, `lof`, `svm`, `pca`, `mcd`, `sod`, `sos`.

Guidance:

- Start with `iforest` and an explicit `fraction` matching the expected contamination rate.
- `assign_model(..., score=True)` returns `Anomaly` and usually `Anomaly_Score`.
- The `cluster` anomaly model has a retry path for degenerate cluster separation but can still fail on pathological data; try `iforest` or adjust data scaling/feature selection.

### Time series

Requires `pycaret[timeseries]`. Runtime registry model IDs include:

- Baselines/classical: `naive`, `grand_means`, `snaive`, `polytrend`, `arima`, `auto_arima`, `exp_smooth`, `ets`, `theta`, `stlf`, `croston`, `bats`, `tbats`, `prophet`.
- Reduced regression forecasters: `lr_cds_dt`, `en_cds_dt`, `ridge_cds_dt`, `lasso_cds_dt`, `llar_cds_dt`, `br_cds_dt`, `huber_cds_dt`, `omp_cds_dt`, `knn_cds_dt`, `dt_cds_dt`, `rf_cds_dt`, `et_cds_dt`, `gbr_cds_dt`, `ada_cds_dt`, `xgboost_cds_dt`, `lightgbm_cds_dt`, `catboost_cds_dt`.

Guidance:

- Start with `naive`, `snaive`, or `polytrend` for smoke tests.
- Pass `fh` at experiment construction and optionally override it in `predict_model`.
- Set `seasonal_period` explicitly when known; otherwise PyCaret attempts seasonality detection from index frequency.
- Avoid broad `compare_models()` over all time-series models in smoke tests; some classical/optional forecasters are slow or dependency-sensitive.

## Metrics overview

Use static `pycaret.api.list_metrics` for classification/regression, and use `exp.get_metrics()` after fit for runtime registries.

Classification metrics commonly include:

- `Accuracy` (default), `AUC`, `Recall`, `Prec.`, `F1`, `Kappa`, `MCC`.

Regression metrics commonly include:

- `MAE`, `MSE`, `RMSE` (default card), `R2`, `RMSLE`, `MAPE`.

Clustering runtime metrics include:

- `silhouette`, `chs` (Calinski-Harabasz), `db` (Davies-Bouldin), and optional ground-truth metrics such as homogeneity/ARI/completeness when labels are available.

Time-series metrics include:

- `MASE`, `RMSSE`, `MAE`, `RMSE`, `MAPE`, `SMAPE`, `R2`, and `COVERAGE`.

Metric sorting rules:

- Higher is better for scores such as `Accuracy`, `AUC`, `F1`, `R2`, and `COVERAGE`.
- Lower is better for error metrics such as `MAE`, `MSE`, `RMSE`, `MAPE`, `MASE`, `RMSSE`, and `SMAPE`.
- PyCaret supervised comparison automatically treats common error metrics as ascending.
- Time-series comparison defaults to `MASE` ascending.

## Introspection decision tree

1. Need a static JSON summary for a UI/LLM prompt?

   ```python
   from pycaret.api import list_models, list_metrics, describe_setup_params
   payload = {
       "models": [m.to_dict() for m in list_models("classification")],
       "metrics": [m.to_dict() for m in list_metrics("classification")],
       "setup": describe_setup_params("classification").to_dict(),
   }
   ```

2. Need to know what is actually available in the current environment?

   ```python
   from pycaret.api import list_available_models
   cards = list_available_models(exp)
   missing = [m.id for m in cards if not m.is_available]
   ```

3. Need the full runtime registry for clustering/anomaly/time-series?

   ```python
   exp = ClusteringExperiment().fit(df)
   models_df = exp.models()
   metrics_df = exp.get_metrics()
   ```

4. Need machine-readable setup form options for all task families?

   ```bash
   python scripts/introspection_snapshot.py --task all --include-setup-params --indent 2
   ```

## Data assumptions

- Supervised tabular input must be pandas-compatible with a named target column or an explicit `(X, y)` pair.
- Native setup handles numeric/bool and categorical columns with imputation and ordinal encoding; optional `normalize`, `transformation`, `remove_outliers`, and `feature_selection` are constructor flags for classification/regression.
- Unsupervised input is feature-only; do not include labels unless they are meant to be model features.
- Time-series input should have an ordered time index. Period or datetime indexes with recognizable frequency help seasonality and split behavior.
- `pycaret.datasets.get_data(...)` may use network; prefer sklearn toy data or inline frames for deterministic no-network examples.

## Plot selection guide

- Classification first-look: `plot_model(model, plot="confusion_matrix")` or default `auc` for probability-capable binary/multiclass classifiers.
- Regression first-look: default `residuals`, plus `prediction_error`.
- Clustering first-look: `silhouette_plot` or `cluster`.
- Anomaly first-look: `score` or `anomaly_map`.
- Time series first-look: `forecast`, plus `acf`, `pacf`, `decomposition`, and `diagnostics`.

If `plot_model(..., save=...)` fails with a kaleido message, install `pycaret[export]` or return the Plotly figure without static export.

## Backend and budget guidance

- For small validation tasks, set `fold=2` or `fold=3`, `n_jobs=1`, and restrict `include` to two or three fast model IDs.
- Avoid `compare_models()` over all time-series models unless the user explicitly wants a broad search and accepts runtime/dependency cost.
- Use `errors="raise"` during debugging to surface the first failing model; use `errors="ignore"` when broad comparison should skip incompatible candidates.
- Do not install `pycaret[full]` automatically for a narrow workflow. Install only the extra that matches the selected task or feature.
