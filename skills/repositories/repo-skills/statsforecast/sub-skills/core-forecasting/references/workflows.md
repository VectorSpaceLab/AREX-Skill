# Core Forecasting Workflows

These recipes are self-contained patterns for native pandas/polars `StatsForecast` use. They deliberately use simple models; route to `model-selection` when the user needs an actual model-family decision.

## 1. Memory-efficient forecast

Use `forecast` when the user needs point forecasts and does not need to keep fitted model objects.

```python
import pandas as pd
from statsforecast import StatsForecast
from statsforecast.models import Naive, SeasonalNaive

panel = pd.DataFrame(
    {
        "unique_id": ["a"] * 8 + ["b"] * 8,
        "ds": list(pd.date_range("2024-01-01", periods=8, freq="D")) * 2,
        "y": [10, 11, 12, 11, 13, 14, 15, 16, 20, 21, 21, 22, 23, 24, 24, 25],
    }
)

sf = StatsForecast(
    models=[Naive(), SeasonalNaive(season_length=3, alias="SeasonalNaive3")],
    freq="D",
    n_jobs=1,
)
fcst = sf.forecast(df=panel, h=3)
```

Expected future columns: `unique_id`, `ds`, `Naive`, and `SeasonalNaive3`.

## 2. Keep fitted models with `fit`/`predict`

Use `fit`/`predict` when the fitted object will be reused.

```python
sf = StatsForecast(models=[Naive()], freq="D")
sf.fit(df=panel)
pred_1 = sf.predict(h=3)
pred_2 = sf.predict(h=7)  # reuse stored fitted models
```

If the fitted data contained exogenous columns and the selected model uses them, every `predict` call needs a matching future `X_df`.

## 3. Single-call fit and predict

Use `fit_predict` when the user wants forecasts now and also wants the object to retain fitted models.

```python
sf = StatsForecast(models=[Naive()], freq="D")
fcst = sf.fit_predict(df=panel, h=3)
# sf now has fitted models and can be used with predict(...)
```

If fitted objects are not needed, prefer `forecast` for lower memory use.

## 4. Fitted values from forecast

```python
sf = StatsForecast(models=[Naive()], freq="D")
future = sf.forecast(df=panel, h=3, fitted=True)
insample = sf.forecast_fitted_values()
```

Use this for residual inspection, anomaly review, and plot overlays. Fetch `insample` before another `forecast` call that may clear or replace the stored fitted-value payload.

## 5. Temporal cross-validation

```python
sf = StatsForecast(models=[Naive()], freq="D")
cv = sf.cross_validation(
    df=panel,
    h=2,
    n_windows=3,
    step_size=1,
    fitted=True,
)
cv_fitted = sf.cross_validation_fitted_values()
```

Interpretation:

- Each `(unique_id, cutoff)` defines one validation window.
- The output has `h` rows per window per id.
- `step_size=1` makes adjacent windows overlap; larger values separate windows.
- `input_size=None` uses expanding windows; set an integer to use rolling windows.
- Use `test_size` instead of `n_windows` when the user wants to define the total held-out period.

## 6. Prediction intervals

### Native/analytic intervals

```python
sf = StatsForecast(models=[Naive()], freq="D")
fcst = sf.forecast(df=panel, h=3, level=[80, 95])
```

Check for columns such as `Naive-lo-80`, `Naive-hi-80`, `Naive-lo-95`, and `Naive-hi-95`.

### Conformal intervals through the orchestrator

```python
from statsforecast.utils import ConformalIntervals

intervals = ConformalIntervals(n_windows=2, h=3)
sf = StatsForecast(models=[SeasonalNaive(season_length=3)], freq="D")
fcst = sf.forecast(df=panel, h=3, level=[80], prediction_intervals=intervals)
```

Before running conformal intervals, ensure every series has at least `2 * h + 1` historical samples. Requested settings with `n_windows` need `n_windows * h + 1` samples to use all requested windows.

## 7. Exogenous future data

Choose an exogenous-capable model in `model-selection`. The core data contract is the same regardless of model family: training data has extra columns; future `X_df` has id/time plus those extra columns and no target.

```python
import pandas as pd
from statsforecast import StatsForecast
from statsforecast.models import AutoARIMA

train = panel.copy()
train["promo"] = [0, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0]

future_x = pd.DataFrame(
    {
        "unique_id": ["a", "a", "a", "b", "b", "b"],
        "ds": list(pd.date_range("2024-01-09", periods=3, freq="D")) * 2,
        "promo": [0, 1, 0, 1, 0, 0],
    }
)

sf = StatsForecast(models=[AutoARIMA(season_length=3)], freq="D")
fcst = sf.forecast(df=train, h=3, X_df=future_x)
```

If `future_x` is missing, has too few rows, omits `promo`, or uses the wrong id/time names, fix `X_df` rather than changing the core workflow.

## 8. Custom column names

```python
custom = panel.rename(
    columns={"unique_id": "item_id", "ds": "timestamp", "y": "target"}
)

sf = StatsForecast(models=[Naive()], freq="D")
fcst = sf.forecast(
    df=custom,
    h=3,
    fitted=True,
    id_col="item_id",
    time_col="timestamp",
    target_col="target",
)
fitted = sf.forecast_fitted_values()
```

`fcst` uses `item_id` and `timestamp`. `fitted` uses `item_id`, `timestamp`, and `target`.

## 9. Save, load, and predict later

```python
sf = StatsForecast(models=[Naive()], freq="D")
sf.fit(df=panel)
sf.save("sf.pkl", max_size="100MB", trim=True)

loaded = StatsForecast.load("sf.pkl")
pred = loaded.predict(h=3)
```

Use `trim=True` to reduce pickle size when stored fitted-value helper payloads are not needed. If the saved object was fitted with exogenous features and exogenous-capable models, future `predict` still needs `X_df`.

## 10. Plot basics

```python
fcst = StatsForecast(models=[Naive()], freq="D").forecast(df=panel, h=3, level=[80])
fig = StatsForecast.plot(
    df=panel,
    forecasts_df=fcst,
    unique_ids=["a"],
    level=[80],
    max_insample_length=20,
    engine="matplotlib",
)
```

Use `level` as a list. Available plot engines depend on optional plotting dependencies in the user's environment.

## 11. Local `n_jobs` and `fallback_model`

```python
from statsforecast.models import Naive, AutoARIMA

sf = StatsForecast(
    models=[AutoARIMA(season_length=7)],
    freq="D",
    n_jobs=-1,
    fallback_model=Naive(alias="fallback"),
)
fcst = sf.forecast(df=panel, h=7)
```

Guidance:

- `n_jobs=1` is the safest first run, easiest to debug, and often fastest for tiny panels.
- `n_jobs=-1` can help large panels with many independent series, but process overhead and model serialization matter.
- The effective worker count is capped at the number of series.
- Use `fallback_model` to keep a batch forecast running when a primary model fails on some series. Inspect errors later; fallback output columns still use the primary model names.
- For cross-validation with `refit=False` or integer `refit`, make sure both primary and fallback models implement `forward`.
