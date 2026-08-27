---
name: time-series-forecasting
description: "Use Lazy Predict LazyForecaster for time-series model
  benchmarking, exogenous forecasting, seasonal detection, forecasting metrics,
  horizon strategies, ensembles, diagnostics, plotting, and optional forecasting
  dependencies."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Time-series Forecasting

Use this sub-skill when the task asks for Lazy Predict forecasting with
`LazyForecaster`, including baseline and sklearn lag-feature forecasters,
statistical or deep optional forecasters, exogenous variables, time-series
metrics, horizon strategies, ensembles, diagnostics, or plotting.

## Start here

1. Confirm the user has ordered numeric observations split into `y_train` and
   `y_test`. Lazy Predict forecasts a future horizon of `len(y_test)`.
2. Start with a bounded CPU-safe model list such as `['Naive', 'Ridge_TS']`.
3. Add optional statistical, boosting, deep-learning, or foundation models only
   when dependencies and runtime budget are available.
4. Run the bundled smoke helper when the environment or basic contract is in
   doubt:

   ```bash
   python scripts/smoke_forecasting.py --predictions --exogenous
   ```

## Main API

Read [references/api-reference.md](references/api-reference.md) for the verified
`LazyForecaster` signature, model categories, helper functions, and result
columns.

Typical bounded workflow:

```python
from lazypredict.TimeSeriesForecasting import LazyForecaster

fcst = LazyForecaster(
    forecasters=['Naive', 'Ridge_TS'],
    predictions=True,
    n_lags=5,
    verbose=0,
    ignore_warnings=True,
)
scores, predictions = fcst.fit(y_train, y_test)
```

For exogenous features, pass matrices aligned with the train and forecast
periods:

```python
scores, predictions = fcst.fit(y_train, y_test, X_train, X_test)
```

## Workflows

Read [references/workflows.md](references/workflows.md) for quick starts,
exogenous variables, model subsets, cross-validation, custom metrics, horizon
strategies, ensembles, diagnostics, visualization, save/load, and forecasting
from loaded models.

## Troubleshooting

Read [references/troubleshooting.md](references/troubleshooting.md) for too-short
series, lag/window errors, exogenous shape mismatches, missing optional
forecasting dependencies, invalid sort/tuning metrics, TimesFM local weight
issues, GPU fallback, and plotting failures.

## Route elsewhere

- Use [supervised-benchmarking](../supervised-benchmarking/SKILL.md) for
  `LazyClassifier` or `LazyRegressor` tabular supervised tasks.
- Use [advanced-workflows](../advanced-workflows/SKILL.md) for detailed tuning,
  search-space, SHAP, and optional advanced-dependency choices.
- Use [cli-and-integrations](../cli-and-integrations/SKILL.md) for package
  install checks, MLflow integration, Spark, Dask/PySpark, and the supervised
  CSV CLI. The CLI does not provide the `LazyForecaster` workflow.
