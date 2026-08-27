# Evaluation workflows

This reference covers evaluation-specific workflows for NeuralProphet 1.0.0rc10. It assumes the dataframe is already prepared for the configured model: `ds` is datetime-like, `y` is the target, optional `ID` marks multiple series, and any configured regressors/events/seasonality conditions are present.

## Choosing an evaluation pattern

| Need | Use | Key caution |
| --- | --- | --- |
| Tune with a recent holdout | `split_df(...)` then `fit(..., validation_df=...)` | Keep validation later than training; metrics may be disabled by `minimal=True` or `metrics=False`. |
| Report final holdout metrics | `fit(train_df, ...)` then `test(test_df)` | Do not use the test set for hyperparameter decisions; refit on all available data before production forecasting if appropriate. |
| Rolling-origin backtest | `crossvalidation_split_df(...)` and fit a fresh model per fold | Folds reuse historical context for lagged inputs; high overlap is slower and less independent. |
| Separate validation and test folds | `double_crossvalidation_split_df(...)` | Only for a single time series; multiple `ID` dataframes are not supported by this helper. |
| Prediction intervals | `NeuralProphet(quantiles=[...])`, `conformal_predict(...)`, `uncertainty_evaluate(...)` | Use a held-out calibration set that is not used for fitting and is not the test set. |

## Holdout validation and test

A standard time-ordered split is the safest starting point. `split_df` returns earlier rows first and later rows second.

```python
from neuralprophet import NeuralProphet, set_random_seed

set_random_seed(0)
m = NeuralProphet(epochs=20, learning_rate=0.1)

train_df, val_df = m.split_df(df, freq="D", valid_p=0.2)
metrics = m.fit(
    train_df,
    freq="D",
    validation_df=val_df,
    deterministic=True,
    progress=None,
)
```

Validation notes:

- `valid_p` may be a fraction between 0 and 1. The holdout is the later portion of the series.
- `local_split=True` splits each `ID` independently; the default uses a shared time threshold for multi-series data.
- `fit(validation_df=...)` produces validation metrics during training when metrics are enabled. Common columns include training metrics such as `MAE`/`RMSE` and validation counterparts such as `MAE_val`/`RMSE_val`, plus loss columns.
- For reproducibility, call `set_random_seed(seed)` before model creation/fitting and pass `deterministic=True` to `fit`.

For a final holdout test, keep a separate later segment and call `test` after fitting:

```python
m = NeuralProphet(epochs=20, learning_rate=0.1)
train_df, test_df = m.split_df(df, freq="D", valid_p=0.2)
m.fit(train_df, freq="D", progress=None)
test_metrics = m.test(test_df, verbose=False)
```

If the final deliverable is a forecast rather than a benchmark, fit a fresh model on the data you are allowed to use for forecasting after evaluation is complete.

## Three-way train/calibration/test split

Conformal prediction needs a calibration holdout separate from both training and test data. Split sequentially so the temporal order is:

```text
train -> calibration -> test
```

One convenient pattern is:

```python
base = NeuralProphet(quantiles=[0.05, 0.95], epochs=20, learning_rate=0.1)
train_cal_df, test_df = base.split_df(df, freq="D", valid_p=0.2)
train_df, cal_df = base.split_df(train_cal_df, freq="D", valid_p=0.25)
```

With this example, the final 20% is test data, and the previous 20% is calibration data. The exact percentages can be adjusted, but the calibration rows should not be used in `fit`.

## Rolling time-series cross-validation

Use rolling-origin folds when one holdout is too sensitive to the chosen split point.

```python
params = {"seasonality_mode": "multiplicative", "learning_rate": 0.1, "epochs": 20}
folds = NeuralProphet(**params).crossvalidation_split_df(
    df,
    freq="MS",
    k=5,
    fold_pct=0.1,
    fold_overlap_pct=0.5,
    global_model_cv_type="global-time",
)

fold_rows = []
for fold_idx, (fold_train, fold_val) in enumerate(folds, start=1):
    m = NeuralProphet(**params)
    m.fit(fold_train, freq="MS", progress=None)
    metrics = m.test(fold_val, verbose=False)
    metrics.insert(0, "fold", fold_idx)
    fold_rows.append(metrics)
```

Parameter guidance:

- `k`: number of folds. More folds are slower because each fold trains a fresh model.
- `fold_pct`: fraction of available samples in each validation fold.
- `fold_overlap_pct`: fraction of validation samples reused between neighboring folds. Higher overlap gives smoother rolling diagnostics but more reuse and runtime.
- `global_model_cv_type="global-time"`: default for multiple `ID` dataframes; uses a common timestamp threshold and avoids time leakage, but validation sample counts can differ by ID.
- `global_model_cv_type="local"`: splits each ID locally; gives aligned per-ID counts but can create cross-series time leakage if IDs have different date ranges.
- `global_model_cv_type="intersect"`: uses only the time span shared by all IDs; avoids leakage and equalizes counts, but discards non-overlapping rows.

For lagged autoregression or lagged regressors, validation folds include enough earlier rows to provide lag inputs. This sharing is input overbleed, not target leakage, but it changes raw row counts and should be reported when interpreting fold sizes.

## Advanced validation/test cross-validation

For a single time series, `double_crossvalidation_split_df(df, k=..., valid_pct=..., test_pct=...)` returns two fold collections: validation folds and test folds. Use it when you need validation for tuning and a separate rolling test estimate.

```python
m = NeuralProphet(n_lags=2, epochs=20, learning_rate=0.1)
folds_val, folds_test = m.double_crossvalidation_split_df(
    df,
    freq="D",
    k=3,
    valid_pct=0.3,
    test_pct=0.15,
)
```

Do not use this helper with multi-`ID` data; select ordinary cross-validation with an explicit `global_model_cv_type` instead.

## Quantile regression and conformal intervals

Quantile regression is enabled at construction time. NeuralProphet always keeps the median quantile internally; user-provided `0.5` is not duplicated.

```python
from neuralprophet import NeuralProphet, uncertainty_evaluate

m = NeuralProphet(quantiles=[0.05, 0.95], epochs=20, learning_rate=0.1)
m.fit(train_df, freq="D", progress=None)

forecast = m.conformal_predict(
    test_df,
    calibration_df=cal_df,
    alpha=0.1,
    method="naive",
    show_all_PI=True,
    decompose=False,
)
interval_eval = uncertainty_evaluate(forecast)
```

Interpretation:

- `quantiles=[0.05, 0.95]` requests a 90% quantile interval around the median point forecast `yhat1`.
- `method="naive"` uses absolute residuals from the calibration set to widen point forecasts symmetrically.
- `method="cqr"` uses conformalized quantile regression and adjusts the lower/upper quantile forecasts.
- `alpha=0.1` targets roughly 90% marginal coverage. A tuple such as `(0.03, 0.07)` is an asymmetrical error allocation and is valid for `method="cqr"`, not for `method="naive"`.
- `show_all_PI=True` retains both conformal interval columns and the original quantile-regression interval columns. This is useful for debugging and interval comparison.
- `uncertainty_evaluate` summarizes `interval_width` and `miscoverage_rate` per forecast step after dropping rows without observed `y` or `yhat1`.

For future-only forecasts without observed `y`, you can still create intervals, but `uncertainty_evaluate` has no ground-truth target rows to score. Use an observed test dataframe for evaluation.
