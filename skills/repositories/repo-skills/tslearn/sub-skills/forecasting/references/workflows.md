# Forecasting Workflows

These workflows are intentionally small and copy-editable. They avoid plotting, downloads, and external datasets while preserving the `VARIMA` and `AutoVARIMA` contracts.

## 1. Known-order VARIMA on variable-length data

Use this when the ARIMA orders are already chosen.

```python
import numpy as np
from tslearn.forecasting import VARIMA
from tslearn.generators import random_walks

X = random_walks(n_ts=3, sz=5, d=1, std=0, random_state=0)
X[0, 4:, :] = np.nan  # real length 4
X[1, 3:, :] = np.nan  # real length 3
X[2, 2:, :] = np.nan  # real length 2

model = VARIMA(1, 0, 0, with_constant=False).fit(X)
forecast_from_fit_data = model.predict(n=2)

X_fresh = random_walks(n_ts=2, sz=4, d=1, std=0, random_state=1)
X_fresh[0, 3:, :] = np.nan  # real length 3
X_fresh[1, 2:, :] = np.nan  # real length 2
forecast_from_fresh_data = model.predict(X_fresh, n=2)
```

Expected shapes:

- `forecast_from_fit_data.shape == (3, 2, 1)`
- `forecast_from_fresh_data.shape == (2, 2, 1)`

The `VARIMA(1, 0, 0)` minimum is two real timestamps per series, so the `[4, 3, 2]` and `[3, 2]` inputs are deliberately tiny but valid.

## 2. `fit_predict` when you do not need separate fit and forecast steps

```python
from tslearn.forecasting import VARIMA

forecast = VARIMA(1, 0, 0, with_constant=False).fit_predict(X, n=2)
```

Use `fit(...).predict(...)` instead when you need to inspect fitted coefficients, reuse the same model against multiple fresh datasets, or catch fit-time and predict-time failures separately.

## 3. AutoVARIMA with a bounded search

Use `AutoVARIMA` when you want automatic differencing and order selection. On tiny data, keep the search bounded before widening it.

```python
import numpy as np
from tslearn.forecasting import AutoVARIMA
from tslearn.generators import random_walks

X = random_walks(n_ts=3, sz=8, d=1, std=0.1, random_state=2)
X[0, 7:, :] = np.nan  # real length 7
X[1, 6:, :] = np.nan  # real length 6
X[2, 5:, :] = np.nan  # real length 5

model = AutoVARIMA(
    max_p=1,
    max_q=1,
    max_d=1,
    default_d_for_non_stationarity=0,
).fit(X)

selected = model.best_estimator_
forecast = model.predict(n=2)
```

Inspect `selected.p`, `selected.d`, `selected.q`, `selected.with_constant`, and `selected.seasonal_period` before explaining the forecast.

## 4. Forecasting a fresh variable-length dataset

After fitting either estimator, use `predict(X_fresh, n=horizon)` when you want to forecast a new batch of series using the fitted model. Validate before calling predict:

1. `X_fresh` has shape `(n_ts_new, sz_new, d_fit)`.
2. Every series has enough real timestamps for the fitted model's minimum-length rule.
3. Variable-length padding is trailing `NaN`, not leading or internal missing values.

## 5. Seasonal-period workflow

Use `seasonal_period` only when each series is long enough to survive seasonal differencing.

```python
seasonal_model = AutoVARIMA(
    seasonal_period=2,
    max_p=1,
    max_q=1,
    max_d=1,
    default_d_for_non_stationarity=0,
).fit(X)
seasonal_forecast = seasonal_model.predict(n=2)
```

If a seasonal run fails on tiny data, first remove `seasonal_period` or lengthen the input. Then retry with a seasonal period much smaller than every real series length.

## Bundled smoke helper

Run:

```bash
python scripts/forecasting_smoke.py
```

The helper checks:

- `VARIMA.fit` on a constant random-walk variable-length dataset.
- `VARIMA.predict` on both fitted data and a second tiny variable-length dataset.
- `AutoVARIMA.fit` and `AutoVARIMA.predict` on low-noise random walks.
- Fit-time and predict-time minimum-length `ValueError` checks.
