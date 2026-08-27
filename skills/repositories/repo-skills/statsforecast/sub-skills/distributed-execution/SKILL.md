---
name: distributed-execution
description: "Use local parallel and optional Dask/Ray/Spark StatsForecast
  execution safely with n_jobs, MultiprocessBackend, ParallelBackend,
  FugueBackend, routing, fallback, and materialization guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# distributed-execution

Use this sub-skill when the task is about running `statsforecast` locally in parallel or through optional distributed DataFrame backends. It is an operating router for execution choices; it does not choose forecasting models, prepare panel schema from scratch, provision clusters, or run benchmarks.

## Route first

- Data schema, required `unique_id`/`ds`/`y` columns, custom column names, `X_df`, prediction intervals, persistence, and normal pandas/polars workflows: route to `core-forecasting`.
- Model-family choice, model aliases, fallback model selection, and model-specific exogenous/interval support: route to `model-selection`.
- Feature construction for future exogenous values, MSTL components, or generated synthetic data: route to `feature-engineering`.
- Cluster creation, scheduler sizing, Spark security, Ray cluster lifecycle, Dask deployment, or benchmark experiments: out of scope; use this skill only to write StatsForecast-side code that can run once the backend exists.

## Execution decision table

| User need | Prefer | Why |
| --- | --- | --- |
| Small/medium pandas or polars DataFrame | `StatsForecast(..., n_jobs=1)` | Simplest and most deterministic; avoids process overhead. |
| Many independent series on one machine | `StatsForecast(..., n_jobs=k)` | Built-in local multiprocessing across series groups. Use `k <= number_of_series`; `-1` means all available CPU cores but is still capped by series count. |
| Explicit backend parity or smoke tests | `MultiprocessBackend(n_jobs=1 or 2)` | Wraps the same core `forecast`/`cross_validation` paths and is safe without a cluster. |
| Dask, Spark, or Ray DataFrame already exists | `StatsForecast.forecast`/`cross_validation` on that DataFrame | The top-level package registers a Fugue backend and routes non-native DataFrames through Fugue. Materialize results with the backend's normal action. |
| A custom Fugue execution engine is already configured | `FugueBackend(engine=..., conf=...)` | Useful when the caller controls a Fugue engine or needs transform kwargs; not needed for normal pandas/polars. |

## Minimum safe pattern

```python
import pandas as pd
from statsforecast import StatsForecast
from statsforecast.models import Naive

panel = pd.DataFrame({
    "unique_id": ["s0"] * 8 + ["s1"] * 8,
    "ds": list(pd.date_range("2024-01-01", periods=8, freq="D")) * 2,
    "y": [1, 2, 3, 4, 5, 6, 7, 8, 10, 9, 8, 7, 6, 5, 4, 3],
})

sf = StatsForecast(models=[Naive()], freq="D", n_jobs=1)
forecast = sf.forecast(df=panel, h=2)
```

For local parallel parity checks, use the bundled smoke script:

```bash
python scripts/distributed_smoke.py --help
python scripts/distributed_smoke.py --n-jobs 1
python scripts/distributed_smoke.py --n-jobs 2
```

## References and bundled script

- [Distributed backend workflows](references/distributed-backends.md): local `n_jobs`, `MultiprocessBackend`, `ParallelBackend`, `FugueBackend`, automatic Dask/Ray/Spark routing, optional dependencies, and materialization patterns.
- [API reference](references/api-reference.md): imports, signatures, parameter contracts, and concise examples for the distributed execution surface.
- [Troubleshooting](references/troubleshooting.md): missing optional dependencies, JVM/Spark issues, `unique_id` string guidance, materialization, fitted values, `n_jobs`, and fallback behavior.
- [Smoke script](scripts/distributed_smoke.py): no-cluster local check that compares `MultiprocessBackend` output with normal `StatsForecast` output.

## Operating cautions

- Distributed execution partitions by series id. Keep each complete time series in one `unique_id`, and prefer string ids for Dask/Ray/Spark/Spark-like engines.
- Optional Dask/Ray/Spark integrations are dependency-gated and were not part of the minimum verified environment. Treat them as code guidance until the target environment proves the extra dependencies and runtime.
- Distributed results can be lazy. Use `.compute()` for Dask-like results, `.show()`/`.toPandas()` for Spark-like results, or `fugue.api.as_pandas(...)` when a Fugue DataFrame abstraction is returned.
- `forecast(..., fitted=True)` can be followed by `forecast_fitted_values()`. For distributed DataFrames, materialize both the forecast and fitted output before comparing or exporting.
- `fallback_model` only handles model failures inside `forecast` and `cross_validation`; it does not fix malformed data, missing future exogenous values, missing optional backends, or cluster startup failures.
