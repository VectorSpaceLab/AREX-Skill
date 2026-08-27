# Engine API Reference

## Purpose

Read this when writing or debugging direct PyCaret 4.0 engine code. It records the verified OOP task-class signatures, high-value verbs, typed result fields, event logging surface, and `pycaret.api` introspection surface.

Evidence sources: `packages/engine/pyproject.toml`, `packages/engine/pycaret/`, `packages/engine/tests/test_e2e_oop.py`, session tests for persistence/predict/create/tune/compare/unsupervised/time-series/plots, and the bundled agent docs for typed results, event stream, and introspection.

## Package and dependency facts

- Distribution: `pycaret` version `4.0.0a8`.
- Python: `>=3.11`.
- Core runtime dependencies include NumPy, pandas, SciPy, scikit-learn, joblib, Plotly, tqdm, requests, Jinja2, and IPython.
- Optional extras:
  - `pycaret[anomaly]`: `pyod` and `numba` for anomaly detectors.
  - `pycaret[timeseries]`: `statsmodels`, `sktime`, and `pmdarima` for forecasting.
  - `pycaret[interpret]`: `shap` for `interpret_model` and SHAP plots.
  - `pycaret[export]`: `kaleido` for static Plotly image export.
  - `pycaret[notebook]`: notebook widgets/artifact rendering.
- Required backend for this skill is CPU. GPU-capable model IDs may be listed, but GPU stacks are optional and not required for smoke validation.

## Canonical task class imports

```python
from pycaret.tasks import (
    ClassificationExperiment,
    RegressionExperiment,
    ClusteringExperiment,
    AnomalyExperiment,
    TimeSeriesExperiment,
)
```

Compatibility class exports exist from `pycaret.classification`, `pycaret.regression`, `pycaret.clustering`, `pycaret.anomaly`, and `pycaret.time_series`, but the `pycaret.tasks` import is the clean 4.0 route.

## Verified constructor signatures

```python
ClassificationExperiment(
    *, target: str | None = None, session_id: int | None = None,
    train_size: float = 0.7, fold: int = 10,
    fold_strategy: str | object = "stratifiedkfold",
    preprocess: bool = True, normalize: bool = False,
    transformation: bool = False, remove_outliers: bool = False,
    feature_selection: bool = False, n_jobs: int = -1,
    use_gpu: bool = False, logger: BaseLogger | None = None,
    log_experiment: bool = False, verbose: bool = False,
)

RegressionExperiment(
    *, target: str | None = None, session_id: int | None = None,
    train_size: float = 0.7, fold: int = 10,
    fold_strategy: str | object = "kfold",
    preprocess: bool = True, normalize: bool = False,
    transformation: bool = False, remove_outliers: bool = False,
    feature_selection: bool = False, n_jobs: int = -1,
    use_gpu: bool = False, logger: BaseLogger | None = None,
    log_experiment: bool = False, verbose: bool = False,
)

ClusteringExperiment(
    *, session_id: int | None = None, preprocess: bool = True,
    normalize: bool = False, transformation: bool = False,
    feature_selection: bool = False, n_jobs: int = -1,
    use_gpu: bool = False, logger: BaseLogger | None = None,
    log_experiment: bool = False, verbose: bool = False,
)

AnomalyExperiment(
    *, session_id: int | None = None, preprocess: bool = True,
    normalize: bool = False, transformation: bool = False,
    feature_selection: bool = False, n_jobs: int = -1,
    use_gpu: bool = False, logger: BaseLogger | None = None,
    log_experiment: bool = False, verbose: bool = False,
)

TimeSeriesExperiment(
    *, target: str | None = None, fh: Any = 1, seasonal_period: Any = None,
    session_id: int | None = None, fold: int = 3,
    fold_strategy: str | object = "expanding", preprocess: bool = True,
    n_jobs: int = -1, use_gpu: bool = False,
    logger: BaseLogger | None = None,
    log_experiment: bool = False, verbose: bool = False,
)
```

Constructor rules:

- Construction stores configuration only; it does not fit or inspect data.
- `session_id` controls splits and estimator seeds where the underlying implementation supports them.
- `n_jobs=1` is safest for smoke tests; `-1` uses all available cores.
- `use_gpu=True` is optional and does not install GPU packages.

## Fit and setup contract

Tabular task fit signature:

```python
exp.fit(X, y=None, **setup_kwargs)
```

Time-series fit signature is also `fit(X, y=None, **setup_kwargs)`, but its accepted data shape differs.

Rules:

- Classification/regression accept either a DataFrame containing `target` or an `(X, y)` pair. If `y` is passed and `target` was not set, PyCaret uses `y.name` or `"target"`.
- Clustering/anomaly accept feature data only; there is no target.
- Time series accepts a univariate `Series`, a single-column DataFrame, or a DataFrame where `target` names the series and remaining columns are exogenous features.
- Passing arbitrary `setup_kwargs` into `.fit(...)` is unsupported in PyCaret 4.0 and raises `ConfigurationError`. Use constructor parameters such as `normalize=True`, `transformation=True`, `remove_outliers=True`, or `feature_selection=True` where available.
- `exp.__sklearn_is_fitted__()` returns whether `fit` completed.

## High-value verbs by task

### Shared tabular verbs

```python
exp.create_model(
    estimator, *, fold=None, cross_validation=True,
    fit_kwargs=None, round=4, verbose=False, **estimator_kwargs
) -> CreateResult

exp.predict_model(
    estimator, data=None, *, raw_score=False, round=4, verbose=False
) -> PredictResult

exp.plot_model(estimator, plot=None, *, save=False, **kwargs) -> Figure | str
exp.evaluate_model(estimator, **kwargs) -> dict[str, Figure]
exp.save_model(model, path, *, verbose=False) -> Path
exp.load_model(path, *, verbose=False) -> Any
```

### Classification/regression verbs

```python
exp.compare_models(
    *, include=None, exclude=None, fold=None, cross_validation=True,
    sort=None, n_select=1, turbo=True, errors="ignore",
    fit_kwargs=None, round=4, verbose=False
) -> CompareResult

exp.tune_model(
    estimator, *, fold=None, n_iter=10, custom_grid=None,
    optimize=None, fit_kwargs=None, round=4, verbose=False
) -> TuneResult

exp.ensemble_model(estimator, *, method="Bagging", n_estimators=10, fold=None, round=4, fit_kwargs=None, verbose=False) -> EnsembleResult
exp.blend_models(estimators, *, method="auto", weights=None, fold=None, round=4, fit_kwargs=None, verbose=False) -> BlendResult
exp.stack_models(estimators, *, meta_model=None, fold=None, round=4, fit_kwargs=None, verbose=False) -> StackResult
exp.calibrate_model(estimator, *, method="sigmoid", cv=None, fold=None, round=4, fit_kwargs=None, verbose=False) -> CalibrateResult
exp.finalize_model(estimator) -> FinalizeResult
exp.interpret_model(estimator, *, plot=None, observation=None, X_new=None, background_size=100) -> shap.Explanation
exp.automl(*, optimize=None, n_iter=10, turbo=True, fold=None, include=None, exclude=None, fit_kwargs=None, round=4, verbose=False) -> Pipeline
exp.get_leaderboard() -> pandas.DataFrame
```

Notes:

- `calibrate_model` is classification-only.
- `ensemble_model`, `blend_models`, `stack_models`, and supervised `finalize_model` are not for clustering/anomaly. Time series has its own `finalize_model`.
- `compare_models(sort=None)` defaults to `Accuracy` for classification and `R2` for regression.
- `turbo=True` skips known-slow supervised model IDs such as `rbfsvm`, `gpc`, and `mlp` unless explicitly disabled.

### Clustering/anomaly verbs

```python
exp.create_model(
    estimator, *, num_clusters=None, fraction=None,
    fit_kwargs=None, round=4, verbose=False, **estimator_kwargs
) -> CreateResult

exp.assign_model(estimator, *, transformation=False, score=True, verbose=False) -> pandas.DataFrame
```

Rules:

- Clustering `assign_model` adds a `Cluster` column.
- Anomaly `assign_model` adds `Anomaly` and, when `score=True`, `Anomaly_Score`.
- Unsupervised `CreateResult.metrics` is currently `None`.

### Time-series verbs

```python
exp.create_model(
    estimator, *, fold=None, cross_validation=True,
    fit_kwargs=None, round=4, verbose=False, **estimator_kwargs
) -> CreateResult

exp.predict_model(
    estimator, data=None, *, fh=None, X=None, return_pred_int=False,
    alpha=None, coverage=0.9, round=4, verbose=False
) -> PredictResult

exp.compare_models(
    *, include=None, exclude=None, fold=None, cross_validation=True,
    sort="MASE", n_select=1, turbo=True, errors="ignore",
    fit_kwargs=None, round=4, verbose=False
) -> CompareResult

exp.tune_model(
    estimator, *, fold=None, n_iter=10, custom_grid=None,
    optimize="MASE", search_algorithm="random", choose_better=True,
    fit_kwargs=None, round=4, verbose=False, return_tuner=False, **kwargs
) -> TuneResult | tuple[TuneResult, search]

exp.finalize_model(estimator, *, fit_kwargs=None) -> FinalizeResult
exp.check_stats(test="all", *, alpha=0.05, split="all") -> pandas.DataFrame
```

Rules:

- Forecast horizon `fh` can be an int/list-like relative horizon. `predict_model(..., fh=[1, 2, 3])` overrides the experiment default.
- `return_pred_int=True` includes `lower` and `upper` prediction interval columns when the forecaster supports them.
- Default comparison/tuning metric is `MASE`, where lower is better.
- `tune_model` expects a fitted forecaster/pipeline from `create_model`; passing a registry string directly raises `TypeError` for time series.
- There is no time-series `assign_model`; `assign_model` is an unsupervised verb.

## Typed result dataclasses

All result dataclasses live in `pycaret.core.results` and include an `events: list[Event]` field with a default empty list. Current engine calls may rely on the experiment logger for the full event trace; always read `exp.events` or the logger when you need all emitted events.

```python
CreateResult(
    pipeline,       # fitted sklearn Pipeline or sktime ForecastingPipeline
    model_id,       # registry id or estimator class name
    metrics,        # CV metrics DataFrame; None for no-CV or unsupervised
    params,         # estimator get_params(deep=False) where available
    events=[]
)

CompareResult(
    best,           # top fitted pipeline, or None if all candidates failed
    models,         # top N fitted pipelines
    leaderboard,    # DataFrame ranked by selected metric
    ranked_ids,     # model ids in leaderboard order
    events=[]
)

TuneResult(
    pipeline,       # tuned fitted pipeline
    best_params,    # winning hyperparameters
    search,         # RandomizedSearchCV / TS search object / None
    cv_results,     # search cv_results_ DataFrame or None/empty
    metrics,        # metrics DataFrame for chosen model
    events=[]
)

EnsembleResult(pipeline, method, metrics, events=[])
BlendResult(pipeline, metrics, events=[])
StackResult(pipeline, metrics, events=[])
CalibrateResult(pipeline, method, metrics, events=[])
FinalizeResult(pipeline, events=[])
PredictResult(predictions, metrics=None, events=[])
```

Common prediction output columns:

- Classification/regression: `prediction_label`; classification may also include `prediction_score` or `prediction_score_<class>` with `raw_score=True`.
- Clustering: `Cluster`.
- Anomaly: `Anomaly`, optionally `Anomaly_Score`.
- Time series: `y_pred`, optionally `lower` and `upper`.

## Data accessors and secondary APIs

After `fit`, these properties are available where meaningful:

```python
exp.X
exp.X_train
exp.X_test
exp.y
exp.y_train
exp.y_test
exp.preprocess_pipeline
exp.events
```

Unsupervised tasks do not have train/test/target data, so supervised-only slots can be `None`.

Useful secondary methods:

```python
exp.pull()                 # latest metrics/leaderboard DataFrame, or None
exp.models(internal=False) # runtime model registry as a DataFrame
exp.get_metrics()          # runtime metric registry as a DataFrame
exp.get_config(name=None)  # list available config keys or get a value
exp.set_config("n_jobs", 1) # only a small safe allowlist is mutable
```

`add_metric` and `remove_metric` are supported for classification and regression custom metrics. They are not currently native for clustering, anomaly, or time-series custom metrics.

## Persistence APIs

Top-level stateless helpers:

```python
from pycaret import save_model, load_model

path = save_model(pipeline, "artifacts/best")  # adds .pkl if missing
restored = load_model(path)
```

Experiment wrappers:

```python
written = exp.save_model(pipeline, "artifacts/best")
restored = exp.load_model("artifacts/best")
exp_path = exp.save_experiment("artifacts/experiment")
restored_exp = type(exp).load_experiment(exp_path)
```

Facts:

- `save_model` does not require the experiment itself to be fitted; it persists the passed object.
- `save_experiment` requires a fitted experiment and serializes fit state.
- The implementation uses joblib and writes `.pkl` when no suffix is supplied.

## Event logging API

Canonical imports:

```python
from pycaret.logging import BaseLogger, EventKind, MemoryLogger
```

`Event` fields:

```python
Event(
    kind: EventKind,
    message: str,
    payload: dict[str, Any],
    duration_ms: float | None,
    timestamp: float,
    experiment_id: str | None,
)
```

Core event kinds include:

- `experiment.started`, `experiment.fitted`, `experiment.finished`
- `preprocessor.started`, `preprocessor.fitted`, `data.split`
- `model.create.started`, `model.created`
- `model.compare.started`, `model.compared`, `model.compare.finished`
- `model.tune.started`, `model.tuned`
- `model.ensemble.started`, `model.ensembled`
- `model.blend.started`, `model.blended`
- `model.stack.started`, `model.stacked`
- `model.calibrate.started`, `model.calibrated`
- `model.finalized`, `model.predicted`, `model.saved`, `model.loaded`
- `warning`, `error`

Memory logger usage:

```python
from pycaret.logging import MemoryLogger
from pycaret.tasks import ClassificationExperiment

log = MemoryLogger(file="events.jsonl")
unsubscribe = log.subscribe(lambda event: print(event.kind.value, event.message))
try:
    exp = ClassificationExperiment(target="target", logger=log, session_id=42).fit(df)
    result = exp.compare_models(include=["lr", "dt"], verbose=False)
finally:
    unsubscribe()

jsonable = [event.to_dict() for event in log.events]
```

Subscriber guarantees:

- Subscribers are called synchronously in registration order.
- Subscriber exceptions are swallowed so one bad subscriber does not break training.
- `subscribe` returns an unsubscribe function; use it in long-running processes.
- `MemoryLogger.events` returns a snapshot copy.

## Introspection APIs

Static, side-effect-free APIs:

```python
from pycaret.api import (
    list_models,
    describe_model,
    list_metrics,
    describe_setup_params,
    list_available_models,
)

models = list_models("classification")
card = describe_model("classification", "lr")
metrics = list_metrics("regression")
schema = describe_setup_params("classification")
```

Runtime-aware model availability:

```python
from pycaret.api import list_available_models
from pycaret.tasks import RegressionExperiment

exp = RegressionExperiment(target="target")
cards = list_available_models(exp)
missing = [card.id for card in cards if not card.is_available]
```

Important current behavior:

- Static `list_models` is populated for classification and regression. For clustering, anomaly, and time-series, use a fitted experiment's `exp.models()` for the complete runtime registry.
- Static `list_metrics` is populated for classification and regression. Runtime `exp.get_metrics()` can expose task metric registries after fit.
- `describe_setup_params(task)` returns a `SetupParamSchema` for all five task strings: `classification`, `regression`, `clustering`, `anomaly`, and `time_series`.
- Task strings use `"time_series"`, not `"time-series"` or `"timeseries"`.

Dataclass fields:

```python
ModelCard(
    id, name, task, description, library,
    gpu_enabled, is_turbo, is_available,
    hyperparameters, tags,
)

MetricCard(
    id, name, task, greater_is_better,
    description, is_default, is_available,
)

ParameterCard(
    name, kind, default, description,
    choices, minimum, maximum, required, group,
)

SetupParamSchema(task, parameters, groups)
```

`ParameterKind` values: `bool`, `int`, `float`, `string`, `enum`, `list`, `column`, `columns`, `model_id`, `metric_id`, and `unknown`.

Every card/schema has `.to_dict()` for JSON serialization.

## Plot and interpretation APIs

`plot_model` returns a Plotly `Figure` by default. `save=True` writes `<plot>.png`; `save="path.png"` writes the provided path and requires `pycaret[export]` / kaleido.

Default plot kinds:

- Classification: `auc`; useful kinds include `auc`, `roc`, `pr`, `confusion_matrix`, `calibration`, `threshold`, `lift`, `gain`, `class_distribution`, `feature`, `permutation`, `pdp`, `ice`, `shap_summary`, `shap_beeswarm`.
- Regression: `residuals`; useful kinds include `residuals`, `residuals_distribution`, `prediction_error`, `learning`, `learning_curve`, `feature`, `permutation`, `pdp`, `ice`, `shap_summary`, `shap_beeswarm`.
- Clustering: `cluster`; useful kinds include `cluster`, `distribution`, `elbow`, `silhouette`, `silhouette_plot`, `embedding`.
- Anomaly: `score`; useful kinds include `score`, `anomaly_map`, `feature_anomaly`, `score_vs_feature`.
- Time series: `forecast`; useful kinds include `forecast`, `decomposition`, `decomp`, `acf`, `pacf`, `diagnostics`, `residuals`, `cv`.

`evaluate_model(estimator)` returns a dictionary of curated Plotly figures and skips individual plots that fail, for example because SHAP is missing or an estimator lacks feature importances.

`interpret_model(estimator)` requires `pycaret[interpret]` and returns a `shap.Explanation`; optional `plot` values are `summary`/`beeswarm`, `bar`, and `waterfall`.
