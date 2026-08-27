---
name: statsforecast
description: "Use Nixtla StatsForecast for statistical time-series forecasting,
  model selection, exogenous regressors, prediction intervals, cross-validation,
  feature engineering, and optional distributed execution."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# StatsForecast repo skill

Use this skill when the task is about the Python package `statsforecast`: fast statistical forecasting over many time series, ARIMA/ETS/CES/Theta/Croston/baseline models, exogenous regressors, prediction intervals, temporal cross-validation, MSTL feature workflows, or local/Dask/Ray/Spark-style distributed execution.

## First checks

For a new runtime, install and verify the package before writing forecasting code:

```bash
python -m pip install statsforecast
python scripts/check_statsforecast_env.py --json
python scripts/statsforecast_quick_smoke.py --json
```

If the package comes from a source checkout, read [installation and environment](references/installation-and-environment.md) before editable installs because the compiled extension needs Eigen headers and a working C++ build path.

## Route by user task

| User asks for | Read |
| --- | --- |
| A normal pandas/polars forecast, `forecast`, `fit`/`predict`, `fit_predict`, fitted values, intervals, `X_df`, custom columns, cross-validation, persistence, plotting, or fallback behavior | [core-forecasting](sub-skills/core-forecasting/SKILL.md) |
| Which model class to use, constructor knobs, direct `model.fit(y)` / `model.forecast(y, h)` calls, aliases, AutoARIMA/ETS/CES/Theta, Croston, MSTL/MFLES/TBATS, GARCH/ARCH, or `SklearnModel` | [model-selection](sub-skills/model-selection/SKILL.md) |
| Synthetic panels, AirPassengers fixtures, static/exogenous features, `mstl_decomposition`, trend/seasonal future regressors, pandas-vs-polars feature validation | [feature-engineering](sub-skills/feature-engineering/SKILL.md) |
| `n_jobs`, `ParallelBackend`, `MultiprocessBackend`, Fugue, Dask, Ray, Spark, distributed materialization, local parallel parity, or optional backend dependency issues | [distributed-execution](sub-skills/distributed-execution/SKILL.md) |
| Import/build failures, optional dependencies, cross-skill error triage | [troubleshooting](references/troubleshooting.md) and [installation and environment](references/installation-and-environment.md) |
| Staleness or whether this skill matches the source evidence | [repo provenance](references/repo-provenance.md) |

## Core package facts

- Main import: `from statsforecast import StatsForecast`.
- Model import surface: `from statsforecast.models import Naive, SeasonalNaive, AutoARIMA, ...`.
- Built-in toy data: `statsforecast.utils.AirPassengersDF`, `AirPassengers`, and `generate_series`.
- Standard panel schema: one row per observation with id, time, target columns (`unique_id`, `ds`, `y` by default) plus optional exogenous/static columns.
- Future exogenous dataframe: `X_df` must provide one future row per id and forecast horizon for models that use time-varying regressors.
- Fast one-shot forecasting: `StatsForecast(...).forecast(df=panel_df, h=h, ...)`.
- Stateful workflow: `fit(df=...)`, then `predict(h=..., X_df=...)`, then optional `forecast_fitted_values()`.
- Backtesting: `cross_validation(df=..., h=..., n_windows=..., step_size=...)`.
- Intervals: pass `level=[80, 95]`; use `ConformalIntervals` when conformal intervals are needed and enough history exists.

## Minimal examples

### One-shot forecast

```python
from statsforecast import StatsForecast
from statsforecast.models import AutoARIMA, SeasonalNaive
from statsforecast.utils import AirPassengersDF

sf = StatsForecast(
    models=[AutoARIMA(season_length=12), SeasonalNaive(season_length=12)],
    freq="ME",
    n_jobs=1,
)
forecast_df = sf.forecast(df=AirPassengersDF, h=12, level=[80, 95])
```

### Cross-validation

```python
from statsforecast import StatsForecast
from statsforecast.models import Naive
from statsforecast.utils import generate_series

panel = generate_series(n_series=5, freq="D", equal_ends=True)
sf = StatsForecast(models=[Naive()], freq="D")
cv_df = sf.cross_validation(df=panel, h=7, n_windows=3, step_size=7)
```

## Bundled scripts

- [scripts/check_statsforecast_env.py](scripts/check_statsforecast_env.py): check installed package, core modules, and optional backend imports without modifying data.
- [scripts/statsforecast_quick_smoke.py](scripts/statsforecast_quick_smoke.py): run a tiny deterministic package-level forecast and cross-validation smoke.
- Sub-skills also provide focused smoke/catalog scripts for core forecasting, model catalogs, MSTL features, and distributed execution.

## Decision rules

- Start with `core-forecasting` for most user code, then route to `model-selection` only when choosing or configuring model classes becomes the blocker.
- Use `forecast` for memory-efficient production predictions; use `fit`/`predict` when later reuse, persistence, fitted values, or iterative inspection is needed.
- Keep model aliases unique whenever two models would share the same display name.
- Treat Dask/Ray/Spark/Prophet/sklearn/polars as dependency-gated surfaces. Do not claim an optional backend is available until the environment check or import proves it.
- Do not rely on original repository notebooks, tests, or scripts at runtime. Use the bundled references and scripts in this skill tree.
