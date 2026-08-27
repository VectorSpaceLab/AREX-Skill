# Engine Workflow Troubleshooting

## Purpose

Use this when a direct PyCaret 4.0 engine workflow fails. Keep the OOP API shape unless the error proves the selected task, data, model ID, or optional dependency is wrong.

## Quick triage

1. Confirm the code is OOP-only:

   ```python
   from pycaret.tasks import ClassificationExperiment
   exp = ClassificationExperiment(target="label").fit(df)
   result = exp.compare_models()
   ```

2. Confirm the experiment was fitted before model verbs:

   ```python
   assert exp.__sklearn_is_fitted__()
   ```

3. Confirm the task class matches the data shape:

   - Classification/regression: target column or `(X, y)` pair.
   - Clustering/anomaly: feature-only data.
   - Time series: univariate `Series`/single-column frame or `target=` in a multicolumn frame.

4. Confirm optional extras:

   ```bash
   python scripts/engine_smoke.py --task anomaly
   python scripts/engine_smoke.py --task time-series
   python scripts/introspection_snapshot.py --task all
   ```

5. For unknown models, inspect runtime choices after fit:

   ```python
   print(exp.models().index.tolist())
   ```

## Symptom-to-fix table

| Symptom or error fragment | Likely cause | Fix |
| --- | --- | --- |
| `ImportError`, `cannot import name setup`, missing `setup`/functional helper | PyCaret 3.x functional API pattern in a PyCaret 4.0 engine workflow | Rewrite to OOP task classes: `ClassificationExperiment(target=...).fit(df)`, then `exp.compare_models()` and typed result fields. |
| `NameError: setup is not defined` or `compare_models` not found | User copied a 3.x notebook cell | Use [workflows.md](workflows.md) recipes; do not add module-level current-experiment state. |
| `Experiment is not fitted. Call .fit(data) first.` | A model verb ran before `.fit(...)` | Call `.fit` and confirm `exp.__sklearn_is_fitted__()` before `create_model`, `compare_models`, `predict_model`, `assign_model`, or plots. |
| ``target` must be set` or `target column ... not found` | Supervised task missing target config or target not in DataFrame | Pass `target="column_name"`, include that column in `df`, or call `exp.fit(X, y)` with named `y`. |
| `setup_kwargs are not supported in PyCaret 4.0` | Caller passed legacy setup kwargs into `.fit(...)` | Move supported knobs to constructor (`normalize`, `transformation`, `remove_outliers`, `feature_selection`, `fold`, etc.) or explain that the removed setup escape hatch requires PyCaret 3.x / a new first-class parameter request. |
| `Unknown model id ... Call Experiment.list_models()` | Model ID not in the runtime registry for this task or optional library missing | Run `exp.models()` after fit. For classification/regression static context, run `python scripts/introspection_snapshot.py --task classification`. Use valid IDs for the selected task. |
| `Unknown TS model id` | Time-series model ID not registered | Use `exp.models()` after `TimeSeriesExperiment.fit(...)`; start with `naive`, `snaive`, `polytrend`, or `theta`. |
| `Unknown task: 'time-series'` | Wrong task string for `pycaret.api` | Use `time_series` for API introspection; the bundled scripts accept CLI alias `time-series` and translate it. |
| `No module named pyod` | Anomaly extra missing | Install `pip install "pycaret[anomaly]"` and rerun `python scripts/engine_smoke.py --task anomaly`. |
| `No module named sktime`, `statsmodels`, or `pmdarima` | Time-series extra missing | Install `pip install "pycaret[timeseries]"` and rerun `python scripts/engine_smoke.py --task time-series`. |
| SHAP import error or message mentioning `pycaret[interpret]` | `interpret_model` or SHAP plot requested without optional SHAP extra | Install `pip install "pycaret[interpret]"` or use non-SHAP `plot_model` diagnostics. |
| Static image export fails and mentions `kaleido` | `plot_model(save=...)` needs export extra | Install `pip install "pycaret[export]"`, or call `plot_model(..., save=False)` and use the returned Plotly figure. |
| Classification `calibration` plot raises binary/multiclass error | Calibration curve implementation expects binary classification | Use `confusion_matrix`, `auc`, `pr`, or class-specific diagnostics for multiclass tasks. |
| `calibrate_model is only valid for classification` | Calibration requested for regression or another task | Use regression diagnostics such as `residuals`/`prediction_error`, or skip calibration. |
| `tune_model expects a fitted forecaster or pipeline` for time series | Time-series `tune_model` was called with a string model ID | First call `created = exp.create_model("naive")`, then `exp.tune_model(created.pipeline, ...)`. |
| Time-series predictions have unexpected horizon length | `fh` at construction or prediction override does not match expectation | Check `TimeSeriesExperiment(fh=...)` and `predict_model(..., fh=[...])`. Passing `fh=` to prediction overrides experiment default. |
| `predict_model expects a fitted estimator with a .predict method` | Passed a result object, model ID string, unfitted estimator, or non-estimator | Pass `result.pipeline`, `compare.best`, or a fitted sklearn/sktime pipeline. Do not pass `CreateResult` itself. |
| `object has no attribute labels_` in `assign_model` | Unsupervised estimator was not fitted on experiment data or does not expose labels | Use `created = exp.create_model(...)` then `exp.assign_model(created.pipeline)`. |
| `Could not form valid cluster separation` for anomaly `cluster` model | CBLOF/cluster anomaly detector failed on data geometry | Try `iforest`, scale features (`normalize=True`), adjust contamination/fraction, or inspect feature distributions. |
| `compare_models` returns empty result with `errors="ignore"` | Every candidate failed and errors were swallowed | Rerun with `errors="raise"` on a small `include` list to surface the first exception. |
| Long runtime or memory pressure | Broad comparison, large folds, slow model IDs, or time-series model set too large | Use `fold=2`/`3`, `n_jobs=1`, restrict `include`, keep `n_iter` small, and avoid all-model time-series comparison for smoke tests. |
| GPU expected but CPU used | GPU stacks are optional and not installed by this skill | Treat CPU as required path. If the user explicitly requires GPU acceleration, verify optional packages/backends separately before claiming GPU support. |

## OOP-only migrations from 3.x snippets

Use this translation pattern. Treat the left column as legacy text to replace, not code to run.

| Legacy 3.x request shape | PyCaret 4.0 OOP replacement |
| --- | --- |
| Import classification setup/compare helpers | `from pycaret.tasks import ClassificationExperiment` |
| Run setup on a DataFrame with target `"label"` | `exp = ClassificationExperiment(target="label").fit(df)` |
| Compare models and get the best model | `compare = exp.compare_models(); best = compare.best` |
| Pull the leaderboard | `compare.leaderboard` or `exp.pull()` after an instance verb |
| Tune the best model | `exp.tune_model(best).pipeline` |
| Predict on new data | `exp.predict_model(best, data=new_df).predictions` |
| Save the fitted pipeline | `from pycaret import save_model; save_model(best, "path")` |

Do not emulate 3.x global current-experiment behavior. Do not create a custom global variable to stand in for setup.

## Data validation failures

### Supervised target problems

Symptoms:

- `target column '...' not found`.
- Fit succeeds but predictions/metrics are wrong because target was accidentally included in features or missing from new data.

Checks:

```python
assert target in df.columns
assert df[target].notna().any()
X = df.drop(columns=[target])
y = df[target]
```

Fixes:

- For a full DataFrame workflow, construct with `target=...` and pass the full DataFrame to `fit`.
- For separate arrays, call `ClassificationExperiment(...).fit(X, y.rename("target"))` or set `target` in the constructor.
- For `predict_model(..., data=new_df)`, include the target column only when you want metrics computed on labeled data.

### Unsupervised data problems

Symptoms:

- Model treats a label column as a feature.
- Clustering/anomaly output is dominated by a non-feature identifier.

Checks and fixes:

```python
feature_df = df.drop(columns=["known_label", "id"], errors="ignore")
exp = ClusteringExperiment(normalize=True, session_id=42).fit(feature_df)
```

Unsupervised experiments do not know which columns are labels. Remove non-features before `.fit(...)`.

### Time-series data problems

Symptoms:

- Forecast horizon is wrong.
- Seasonality detection falls back to `sp=1`.
- Exogenous data shape errors.

Checks:

```python
print(type(y.index), getattr(y.index, "freq", None), getattr(y.index, "freqstr", None))
print(len(y), y.isna().sum())
```

Fixes:

- Use a `PeriodIndex` or `DatetimeIndex` with frequency when possible.
- Pass `seasonal_period=12` or another known period instead of relying on auto-detection.
- For multicolumn time-series DataFrames, set `target="target_col"` and provide future exogenous rows through `predict_model(..., X=future_X)` when required.

## Model ID and registry troubleshooting

Use runtime registry when the exact environment matters:

```python
exp = ClassificationExperiment(target="label", fold=3, n_jobs=1).fit(df)
models_df = exp.models()
print(models_df[["Name", "Reference", "Turbo"]])
```

Use static API for classification/regression UI context:

```python
from pycaret.api import list_models, describe_model
print([m.id for m in list_models("classification")])
print(describe_model("classification", "lr").to_dict())
```

Important distinction:

- `pycaret.api.list_models("clustering")`, `list_models("anomaly")`, and `list_models("time_series")` may return empty static lists. This is expected in the current engine; use `exp.models()` after fit for these tasks.
- Optional-library model cards such as `xgboost`, `lightgbm`, and `catboost` can appear in static classification/regression lists even if unavailable. Use `list_available_models(exp)` or `exp.models()` for runtime availability.

## Optional dependency troubleshooting

Run minimal probes:

```bash
python - <<'PY'
import importlib.util
for name in ["pyod", "sktime", "statsmodels", "pmdarima", "shap", "kaleido"]:
    print(name, bool(importlib.util.find_spec(name)))
PY
```

Install narrowly:

- Anomaly task: `pip install "pycaret[anomaly]"`.
- Time series task: `pip install "pycaret[timeseries]"`.
- SHAP interpretation: `pip install "pycaret[interpret]"`.
- Static plot export: `pip install "pycaret[export]"`.

Avoid installing `pycaret[full]` unless the user explicitly asks for broad optional coverage.

## Plotting and evaluation failures

Facts:

- `plot_model` returns a Plotly `Figure` unless `save` is truthy.
- `evaluate_model` returns a dict of figures and skips individual failing plots.
- Static image export requires `kaleido`; interactive figure objects do not.

Debug pattern:

```python
try:
    fig = exp.plot_model(model, plot="feature")
except ValueError as exc:
    print(exc)  # often lists valid plot kinds
except RuntimeError as exc:
    if "kaleido" in str(exc).lower():
        print("Install pycaret[export] or do not use save=")
```

If feature importance fails, the estimator may not expose `feature_importances_` or `coef_`. Use `permutation`, `pdp`, `ice`, or a different estimator.

## Event logging troubleshooting

Symptoms:

- `exp.events` is empty.
- Subscriber did not receive events.
- JSONL file was not written.

Causes and fixes:

- By default, experiments use `NullLogger` unless `log_experiment=True` or a `logger` is passed.
- Prefer passing an explicit `MemoryLogger(file="events.jsonl")` when you need events.
- Capture the unsubscribe function returned by `subscribe` and call it after the run.
- Subscriber callbacks should not do slow work; exceptions are swallowed by design.

Minimal check:

```python
from pycaret.logging import MemoryLogger

log = MemoryLogger(file="events.jsonl")
exp = ClassificationExperiment(target="label", logger=log).fit(df)
exp.create_model("lr", verbose=False)
print([e.kind.value for e in log.events])
```

## Persistence troubleshooting

Symptoms and fixes:

- File has no suffix: `save_model` adds `.pkl` automatically.
- `load_experiment` says file was not a PyCaret Experiment: use `load_model` for plain pipelines.
- Loaded model predicts on raw features only if the saved object is the full PyCaret pipeline. Save `CreateResult.pipeline`, `CompareResult.best`, `TuneResult.pipeline`, or `FinalizeResult.pipeline`, not a bare inner estimator unless you intentionally manage preprocessing separately.

Validation:

```python
from pycaret import save_model, load_model
path = save_model(pipeline, "artifact/best")
restored = load_model(path)
assert hasattr(restored, "predict")
```

## When to stop and ask for clarification

Ask before proceeding when:

- The user asks for GPU acceleration or a specific optional backend but no backend/install permission is given.
- The task type is ambiguous, for example the dataset has a target-like column but the user asks for clustering.
- The user wants to port 3.x functional code and may need compatibility with PyCaret 3.x rather than 4.0 OOP-only code.
- A workflow requires network datasets, large model comparisons, or installing broad extras beyond the narrow task need.
