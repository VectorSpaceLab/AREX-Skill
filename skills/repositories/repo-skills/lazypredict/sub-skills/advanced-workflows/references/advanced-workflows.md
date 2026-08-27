# Advanced Lazy Predict Workflows

## Tuning after supervised benchmarking

`LazyClassifier` and `LazyRegressor` accept tuning parameters directly:

```python
clf = LazyClassifier(
    classifiers=[LogisticRegression, RandomForestClassifier],
    tune=True,
    tune_top_k=2,
    tune_trials=20,
    tune_timeout=60,
    tune_backend='optuna',  # 'optuna', 'sklearn', or 'flaml'
)
scores, _ = clf.fit(X_train, X_test, y_train, y_test)
print(clf.tuned_scores_)
```

Use `tune_backend='sklearn'` when avoiding optional Optuna/FLAML dependencies.
Use `flaml` only when the FLAML package is installed and the user explicitly
wants that backend. Keep `tune_top_k` and `tune_trials` small for exploratory
runs.

The direct supervised tuning helpers live in `lazypredict.tuning`:

- `tune_supervised_optuna(...)`
- `tune_supervised_sklearn(...)`
- `tune_supervised_flaml(...)`
- `tune_top_k(...)`

Prefer constructor-level tuning unless the task specifically asks to manipulate
search spaces or tune one model outside the Lazy Predict fit loop.

## Tuning time-series forecasters

```python
fcst = LazyForecaster(
    forecasters=['Naive', 'Ridge_TS', 'RandomForestRegressor_TS'],
    tune=True,
    tune_top_k=2,
    tune_trials=20,
    tune_metric='RMSE',
    tune_timeout=60,
)
scores, _ = fcst.fit(y_train, y_test)
print(fcst.tuned_scores_)
```

`LazyForecaster` tuning validates `tune_metric`; use forecast metrics such as
`RMSE`, `MAE`, `MAPE`, `SMAPE`, or `MASE`. `tune_seasonal=True` can search over
seasonality choices and may increase runtime.

Direct time-series helpers include:

- `lazypredict.ts_tuning.tune_forecaster_optuna`
- `lazypredict.ts_tuning.tune_top_k_forecasters`

## Search-space registries

Use the registries to decide whether Lazy Predict has a built-in tuning search
space for a model:

```python
from lazypredict.search_spaces import get_search_space
from lazypredict.ts_search_spaces import get_ts_search_space

rf_space = get_search_space('RandomForestClassifier')
sarimax_space = get_ts_search_space('SARIMAX')
```

The tests verify that common models such as `RandomForestClassifier`,
`XGBRegressor`, `SARIMAX`, and `RandomForestRegressor_TS` have registered
spaces, while trivial baselines such as `DummyClassifier` or `Naive` may return
`None`.

## Explainability

### Permutation importance

Permutation importance works with base dependencies after supervised models are
fitted:

```python
clf = LazyClassifier(max_models=3, verbose=0)
scores, _ = clf.fit(X_train, X_test, y_train, y_test)
importance = clf.explain(X_test, y_test, method='permutation', n_repeats=5)
```

The result is a DataFrame with input features as rows and fitted model names as
columns.

### SHAP

SHAP requires the optional explain dependency and model compatibility:

```python
importance = clf.explain(X_test, y_test, method='shap', max_samples=100)
```

Use SHAP only after checking that `shap` is installed and the fitted model can
be explained. Fall back to permutation importance for a dependency-light answer.

### InterpretML EBM models

When the `interpret` package is installed, Lazy Predict adds
`ExplainableBoostingClassifier` and `ExplainableBoostingRegressor` to its model
lists. This changes available estimators; it does not require a separate API.

## Visualization pointers

Time-series plotting lives on `LazyForecaster.plot_results()` and optional
helpers in `lazypredict.ts_visualization`. Install the visualization extra when
the task needs figures. Otherwise use the returned `scores` and predictions
DataFrames for text-only reporting.

## Safety defaults for agents

- Never start expensive tuning with `forecasters='all'` or `classifiers='all'`
  unless the user explicitly approves the runtime.
- Prefer `top_k <= 3`, `n_trials <= 20`, and a per-model timeout for exploratory
  guidance.
- Check optional modules before promising a backend-specific advanced workflow.
- Preserve the initial untuned leaderboard so the user can compare whether
  tuning improved the result.
