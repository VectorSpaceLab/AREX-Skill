# Troubleshooting: forecasting and imputation

Use this checklist when `hyp.predict`, `hyp.impute`, or forecast overlays misbehave.

## Scalar, empty, or 1-D input

Symptoms:

- `cannot forecast from a single scalar observation`
- `cannot impute a single scalar observation`
- `input has no observations`
- a flat list or 1-D array looks like one row instead of one series

Action:

1. Treat a 1-D array, a flat list of numbers, or a `Series` as a univariate `(n, 1)` column.
2. Use at least 2 rows for forecasting and at least 1 row for imputation.
3. Make sure the input is not empty after filtering or slicing.

## Datetime horizon problems

Symptoms:

- `t (forecast horizon) must be a positive integer or a target datetime`
- `the target time ... is before the first observation`
- `timezone-naive but t=... is timezone-aware`
- `the dataset index is not sorted in ascending order`

Action:

1. Use a positive integer for numeric horizons.
2. Use a `DatetimeIndex` when passing a calendar target.
3. Sort newest-first data before forecasting: `df = df.sort_index()`.
4. For timezone-aware indices, pass a matching timezone or let a naive target localize to the data timezone.
5. If the target is inside the observed range, expect truncation instead of forecasting.

## Duplicate timestamps

Symptoms:

- `cannot infer a timestep: all observations share one timestamp`
- weird or collapsed datetime spacing

Action:

1. Deduplicate or aggregate the timestamps before forecasting.
2. If the timestamps are intentionally repeated, make sure the target horizon is still meaningful after sorting.
3. For a completely repeated `DatetimeIndex`, forecasting cannot infer a step size.

## Unknown kwargs

Symptoms:

- `TypeError` from a model constructor
- `ignoring keyword argument(s) ... model= is already a constructed instance`

Action:

1. Check the model-specific kwargs in `references/forecast-reference.md`.
2. Remember that model instances cannot absorb constructor kwargs; pass the class or a string/dict spec instead.
3. If you are using a dict spec, prefer `{'model': ..., 'kwargs': {...}}` over the deprecated `params` shape.

Common kwargs to check:

- `Kalman` forecaster: `n_iter`, `lags`
- `GaussianProcess`: `kernel`, `alpha`, `normalize_y`
- `AutoRegressor`: `model`, `lags`, `model_kwargs`
- `ARIMA`: `order`
- `PPCA`: `d`, `min_obs`, `tol`, `random_state`
- `SimpleImputer`: `strategy`, `fill_value`
- `KNNImputer`: `n_neighbors`, `weights`
- `IterativeImputer`: `max_iter`, `random_state`
- `Kalman` imputer: `n_iter`
- `Chronos`: `model_name`, `device_map`, `num_samples`, `temperature`, `top_k`, `top_p`

## All-missing rows or columns

Symptoms:

- `input is entirely missing`
- `PPCA cannot fill ... row(s) with no observed features at all`
- warnings about columns with no observed values
- a dead sensor gets filled with 0.0

Action:

1. If the whole input is missing, there is nothing to impute from; collect data first.
2. If only some rows are fully missing, use `model='Kalman'` instead of `PPCA`.
3. If a column is all missing, consider dropping it; the Kalman and PPCA imputers fill such columns with 0.0 and warn.
4. For a single row, use `SimpleImputer` or `KNNImputer`; Kalman imputation needs at least 2 rows.

## Optional extras missing

Symptoms:

- `skaters is required for the Laplace forecaster`
- `chronos-forecasting and torch are required for the Chronos forecaster`

Action:

1. Install the needed extra: `pip install "hypertools[predict]"` for Laplace or `pip install "hypertools[predict-hf]"` for Chronos.
2. If you do not need the optional model, switch to a base-install model (`Kalman`, `GaussianProcess`, `AutoRegressor`, or `ARIMA`).
3. For Chronos, increase `num_samples` if the sampled forecast is too noisy.

## Forecast overlay limits

Symptoms:

- `predict= is not yet supported with animate`
- `predict= is not supported with MultiIndex expansion`
- the overlay styling is wrong even though the data are fine

Action:

1. Use static plots only when forecasting overlays are enabled.
2. Reset a MultiIndex before forecasting overlays if you need the plot path to work.
3. If the problem is colors, dashes, alpha, or legend placement, switch to `../visualization/`.

## Reuse on new data

Symptoms:

- a reused model complains about feature counts or columns
- `predict_new` or `transform` fails after `return_model=True`

Action:

1. Reuse fitted predict models only on new data with the same number of columns.
2. Reuse fitted imputers only on data with the same column layout they were fit on.
3. For list imputations, datasets must share columns if you want a joint fit.
