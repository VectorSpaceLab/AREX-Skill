# Core Forecasting Workflows

## Purpose

Read this when building the main NeuralProphet dataframe-to-forecast loop. It distills the package quickstart, tutorials, source signatures, and safe smoke checks into checkout-independent operating steps.

## Dataframe contract

NeuralProphet expects pandas dataframes with these columns:

| Column | Required | Meaning |
| --- | --- | --- |
| `ds` | yes | Datestamps parseable by pandas. Sort ascending before fitting. |
| `y` | yes for training/testing | Numeric target values. Future-only rows may omit or contain missing `y`. |
| `ID` | optional | Series identifier for global/local multi-series models. Use one row per timestamp and ID. |
| extra columns | when configured | Lagged regressors, future regressors, event indicator columns, or conditional seasonality flags. |

Use `scripts/validate_neuralprophet_dataframe.py data.csv` or `scripts/validate_neuralprophet_dataframe.py --input-file data.csv` to catch missing columns, duplicate timestamps, parse failures, and frequency warnings before fitting user data.

## Minimal CPU fit/predict

```python
import pandas as pd
from neuralprophet import NeuralProphet, set_log_level, set_random_seed

set_log_level("ERROR")
set_random_seed(42)

df = pd.DataFrame({
    "ds": pd.date_range("2022-01-01", periods=80, freq="D"),
    "y": [float(i % 7) for i in range(80)],
})

m = NeuralProphet(
    n_changepoints=0,
    yearly_seasonality=False,
    weekly_seasonality=False,
    daily_seasonality=False,
    epochs=1,
    batch_size=16,
    learning_rate=0.1,
    accelerator="cpu",
)
metrics = m.fit(df, freq="D", progress=None)
forecast = m.predict(df)
print([c for c in forecast.columns if c.startswith("yhat")])
```

`metrics` is a dataframe when metrics are collected. It may be `None` when metrics are disabled by constructor or fit options, so check before indexing it.

## Forecasting future periods

Use `make_future_dataframe` after a model has been fitted:

```python
m = NeuralProphet(epochs=1, batch_size=16, learning_rate=0.1, accelerator="cpu")
m.fit(df, freq="D", progress=None)
future = m.make_future_dataframe(df, periods=30, n_historic_predictions=True)
forecast = m.predict(future)
```

Important decisions:

- `periods` controls how many future timestamps are appended.
- `n_historic_predictions=True` includes all history in the returned dataframe; an integer includes that many historical rows.
- If the model uses future regressors or events, pass `regressors_df` and/or `events_df` to `make_future_dataframe`; otherwise prediction may fail because required future columns are missing.
- If `n_lags > 0`, predictions need historical context. Keep enough rows before the forecast boundary and read troubleshooting notes for `auto_extend` and historic predictions.

## Choosing `freq`

Prefer explicit frequencies such as `"D"`, `"H"`, `"MS"`, or `"5min"` for repeatable behavior. `freq="auto"` calls NeuralProphet frequency inference and can be confused by irregular series, duplicate dates, or too few samples.

## Basic output expectations

A forecast dataframe includes the original `ds` and `y` context plus one or more forecast columns:

- `yhat1`: one-step-ahead forecast.
- `yhat2`, `yhat3`, ...: additional horizons when `n_forecasts > 1`.
- Component columns appear when `predict(..., decompose=True)` and components are active.

When only a tiny smoke test is needed, run:

```bash
python scripts/smoke_forecast.py --epochs 1 --periods 3
```

from this sub-skill directory or invoke the script by path from any working directory.
