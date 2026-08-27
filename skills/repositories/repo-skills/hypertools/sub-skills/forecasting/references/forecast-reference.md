# Forecast reference

This sub-skill covers time-series forecasting with `hyp.predict` and missing-data filling with `hyp.impute`.

## Core signatures

```python
hyp.predict(data, model='Kalman', t=10, return_model=False, **kwargs)
hyp.impute(data, model='PPCA', return_model=False, **kwargs)
```

## Model spec forms

Both APIs accept the same model-spec patterns:

- string model name, matched case-insensitively;
- `predict` also accepts the alias `GP` for `GaussianProcess`;
- dict form `{'model': ..., 'params': {...}}` (deprecated, still accepted with a warning);
- dict form `{'model': ..., 'args': [...], 'kwargs': {...}}`;
- class object;
- already-constructed instance;
- already-fitted instance returned by `return_model=True`.

If you pass constructor kwargs to an already-constructed instance, HyperTools warns and ignores them.

## Input coercion and output shapes

- A 1-D NumPy array, a flat Python list of numbers, or a `pandas.Series` is treated as a univariate `(n, 1)` series.
- A tuple of datasets is treated exactly like a list.
- `hyp.predict` returns a `pandas.DataFrame` for one dataset and a list of DataFrames for a list input.
- `hyp.impute` returns the same shape as the input: one DataFrame for one dataset, or a list for a list input.
- `hyp.impute` preserves observed entries exactly and returns float64 values.
- `return_model=True` returns `(result, fitted_model)`.

## Forecast horizon rules

`t` controls the forecast horizon for `hyp.predict`.

- Integer `t` must be a positive integer.
- Float `t` is rejected.
- `t=None`, booleans, zero, and negatives are rejected.
- For `RangeIndex`, forecasting extends by step 1.
- For a numeric index, the step is the minimum non-zero spacing between sorted observations.
- For a `DatetimeIndex`, the step is the minimum non-zero timedelta between sorted observations.
- A datetime-like `t` requires a `DatetimeIndex`.
- A datetime-like `t` on a timezone-aware index is localized if `t` is tz-naive.
- A tz-aware `t` on a tz-naive index is rejected.
- If `t` is at or before the last observation, `hyp.predict` truncates the data up to `t` instead of forecasting.
- If `t` is before the first observation, `hyp.predict` raises `ValueError`.
- If `t` is after the last observation but less than one full step ahead, the forecast still advances by one step.
- If the index is descending, HyperTools warns and continues from the last row.
- If all timestamps are identical, step inference fails.

## Forecasting model families

### `Kalman`

- Base install: yes.
- Backend: `pykalman`.
- Constructor knobs: `n_iter=5`, `lags=None`.
- Behavior: delay-embedded linear-Gaussian state-space forecaster.
- Strengths: oscillatory and trending series; tolerant of NaNs.
- Reuse: learned transition/observation state is reused on new data.

### `GaussianProcess`

- Base install: yes.
- Backend: scikit-learn.
- Constructor knobs: `kernel=None`, `alpha=1e-10`, `normalize_y=True`.
- Default kernel: `DotProduct() + RBF(10.0) + WhiteKernel()`.
- Strengths: smooth trend extrapolation, good general-purpose base model.
- Limitation: does not accept NaNs; impute first.
- Reuse: the learned kernel is conditioned on the new series without re-optimizing.

### `AutoRegressor`

- Base install: yes.
- Backend: scikit-learn regressors over lagged features.
- Constructor knobs: `model='Ridge'`, `lags=10`, `model_kwargs=None`.
- Supported string regressors: `Ridge`, `Lasso`, `LinearRegression`, `RandomForestRegressor`, `GradientBoostingRegressor`, `SVR`, `KNeighborsRegressor`.
- Strengths: good for oscillatory or trend-following data; accepts a custom sklearn regressor.
- Limitation: does not accept NaNs; needs more than `lags` observations.
- Reuse: the fitted regressor is reused unchanged, with recursion reseeded from new data.

### `ARIMA`

- Base install: yes.
- Backend: `statsmodels`.
- Constructor knobs: `order=(1, 1, 1)` plus other `statsmodels.tsa.arima.model.ARIMA` kwargs.
- Behavior: independent univariate ARIMA per column.
- Strengths: works on NaNs and is a good drift/random-walk baseline.
- Limitation: the default order damps toward a near-constant forecast; use a custom order for trend or seasonality.
- Reuse: the fitted ARIMA results are applied to new data without re-estimating.

### `Laplace`

- Optional extra: `hypertools[predict]`.
- Backend: `skaters`.
- Constructor knobs: none.
- Behavior: online one-step-at-a-time Laplace forecaster per column.
- Strengths: okay for drifting/trending data.
- Limitations: slower for long horizons; not good for oscillatory data; does not tolerate NaNs.
- Reuse: there is no separate learned state to replay; new-series reuse means reconditioning on the new series.

### `Chronos`

- Optional extra: `hypertools[predict-hf]`.
- Backend: `chronos-forecasting` and `torch`.
- Constructor knobs: `model_name='amazon/chronos-t5-tiny'`, `device_map='cpu'`, `num_samples=None`, `temperature=None`, `top_k=None`, `top_p=None`.
- Behavior: sampled foundation-model forecasts per column; the point forecast is the median sample.
- Strengths: handles rich nonlinear sequences when the extra dependencies are available.
- Limitations: nondeterministic run-to-run; increase `num_samples` for a stabler median; no NaNs.
- Reuse: the pretrained pipeline is reloaded and the new series is conditioned directly.

## Imputation model families

### `PPCA`

- Base install: yes.
- Backend: vendored PPCA implementation.
- Constructor knobs: `d=None`, `min_obs=10`, `tol=1e-4`, `random_state=None`.
- Behavior: low-rank probabilistic PCA imputation.
- Strengths: good for low-rank structure and scattered missing values.
- Limitations: cannot reconstruct rows with no observed features; those rows remain NaN and trigger a warning.
- Special cases: all-missing or zero-variance columns are excluded from the fit and filled with the observed mean, or 0.0 when nothing was observed.
- Reuse: learned PPCA state is applied to new data without refitting.

### `SimpleImputer`

- Base install: yes.
- Backend: scikit-learn.
- Constructor knobs: `strategy='mean'`, `fill_value=None`.
- Behavior: fill each column with a statistic.
- Strengths: simple, fast, stable baseline.
- Special cases: empty features are kept and filled instead of being dropped.

### `KNNImputer`

- Base install: yes.
- Backend: scikit-learn.
- Constructor knobs: `n_neighbors=5`, `weights='uniform'`.
- Behavior: neighborhood-based imputation.
- Strengths: local structure, no model tuning.
- Special cases: empty features are kept and filled instead of being dropped.

### `IterativeImputer`

- Base install: yes, but sklearn's experimental import is enabled lazily inside the wrapper.
- Backend: scikit-learn iterative regression.
- Constructor knobs: `max_iter=10`, `random_state=None`.
- Behavior: multivariate round-robin regression imputation.
- Strengths: good when columns predict each other.
- Special cases: empty features are kept and filled instead of being dropped.

### `Kalman` imputer

- Base install: yes.
- Backend: `pykalman`.
- Constructor knobs: `n_iter=5`.
- Behavior: one univariate Kalman smoother per column.
- Strengths: fills fully missing rows from neighboring rows and smooths through time.
- Special cases: all-missing columns are filled with 0.0 and warned about.
- Reuse: per-column filters are applied to new data without rerunning EM.

## List inputs and shared columns

- `hyp.predict` fits one forecaster per dataset.
- `hyp.impute` stacks a list of datasets that share columns, fits one imputer jointly, and splits the result back into a list.
- If a list of datasets does not share columns, `hyp.impute` warns and imputes each dataset independently.
- If you pass a fitted imputer back to a list with mismatched columns, reuse fails; fit each dataset separately.

## Plot overlay contract

`hyp.plot(..., predict=..., t=...)` is a forecast overlay on top of a static plot.

- It draws one dashed, low-opacity tail per dataset.
- The forecast tail uses the same color as the source line.
- The forecast tail does not get its own legend entry.
- `predict=` is not supported together with `animate=`.
- `predict=` is not supported with MultiIndex expansion in this release.
- Styling, colors, and legend adjustments belong in `../visualization/`.
