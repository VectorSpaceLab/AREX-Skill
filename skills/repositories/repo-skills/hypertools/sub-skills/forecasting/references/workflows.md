# Workflows: forecasting and imputation

Route line styling and legend changes to `../visualization/`, file I/O to `../io/`, and generic pipeline-order questions to `../pipeline/`.

## 1. Forecast a single series

Use a DataFrame with one row per time step and one column per feature.

```python
import numpy as np
import pandas as pd
import hypertools as hyp

t = np.linspace(0, 4 * np.pi, 48)
train = pd.DataFrame({'signal': np.sin(t)})

forecast = hyp.predict(train, model='Kalman', t=6)
print(forecast.shape)          # (6, 1)
print(forecast.index[0])       # 48 for a RangeIndex
```

Expected result:

- one `DataFrame` back;
- exactly 6 forecast rows;
- same column names as the input;
- finite numeric output.

If you want a different family, swap `model=`:

- `model='GaussianProcess'` for smooth trend extrapolation;
- `model='AutoRegressor'` for lagged sklearn regression;
- `model='ARIMA'` for a per-column statistical baseline;
- `model='Laplace'` or `model='Chronos'` only when the optional extras are installed.

## 2. Forecast to a datetime target

Use a `DatetimeIndex` when you want a calendar target instead of a fixed row count.

```python
idx = pd.date_range('2024-01-01', periods=40, freq='D')
train = pd.DataFrame({'signal': np.sin(np.linspace(0, 3 * np.pi, 40))}, index=idx)

forecast = hyp.predict(train, model='GaussianProcess', t=idx[-1] + pd.Timedelta(days=5))
print(forecast.index[:2])
```

Expected result:

- a `DatetimeIndex` continuation when the target is in the future;
- a truncated slice when the target is inside the observed range;
- a `ValueError` if the target is before the first timestamp.

## 3. Add a forecast overlay to a static plot

```python
fig = hyp.plot([train], predict='Kalman', t=6, ndims=2, show=False)
```

Expected result:

- a static figure with one dashed forecast tail per dataset;
- the overlay uses the same color as the source trace;
- no separate legend entry for the forecast tail.

Important limits:

- do not combine `predict=` with `animate=`;
- do not expect `predict=` to work with MultiIndex expansion in this release;
- if the issue is styling, go to `../visualization/`.

## 4. Fill missing values with the default imputer

`PPCA` is the default model and a strong first choice for low-rank data.

```python
rng = np.random.default_rng(0)
grid = np.linspace(-1.0, 1.0, 40)
damaged = pd.DataFrame({
    'a': grid,
    'b': 2.0 * grid + 1.0,
    'c': -0.5 * grid + 0.25,
})
damaged.loc[5, 'b'] = np.nan
damaged.loc[12, 'c'] = np.nan
damaged.loc[25, 'a'] = np.nan

filled = hyp.impute(damaged, model='PPCA', random_state=0)
print(filled.shape)            # (40, 3)
print(bool(filled.isna().any().any()))
```

Expected result:

- same shape as the input;
- no missing values left at the imputed cells;
- observed values preserved exactly.

If the data are time-ordered and you need to fill a fully-missing row, switch to `model='Kalman'`.

## 5. Reuse a fitted model on new data

`return_model=True` returns the fitted object alongside the forecast/imputation result.

```python
train = pd.DataFrame({'signal': np.sin(np.linspace(0, 4 * np.pi, 48))})
forecast, fitted_forecaster = hyp.predict(
    train, model='AutoRegressor', t=6, return_model=True, lags=8,
)

new_train = pd.DataFrame({'signal': np.sin(np.linspace(0, 4 * np.pi, 32) + 0.3)})
reused_forecast = hyp.predict(new_train, model=fitted_forecaster, t=6)

print(forecast.shape)          # (6, 1)
print(reused_forecast.shape)   # (6, 1)
```

For imputers:

```python
filled, fitted_imputer = hyp.impute(damaged, model='KNNImputer', return_model=True, n_neighbors=3)
reused_fill = hyp.impute(damaged.copy(), model=fitted_imputer)
```

Reuse notes:

- `Kalman`, `GaussianProcess`, `AutoRegressor`, and `ARIMA` reuse learned forecasting state;
- `Laplace` and `Chronos` have no replayable learned state, so reuse means reconditioning on the new series;
- imputer reuse requires the same column layout as the fit-time data.

## 6. Validate the sub-skill locally

```bash
python scripts/smoke_forecasting.py
```

Expected result:

- the script exits with status 0;
- it prints `forecasting smoke passed`.
