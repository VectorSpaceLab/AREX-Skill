# Distributed backend workflows

This reference covers only execution mechanics for `statsforecast`. It assumes the user already has a valid panel DataFrame and has chosen appropriate StatsForecast model instances.

## Core mental model

StatsForecast parallelizes over independent time series groups. A group is defined by `id_col` (default `unique_id`). Every row for a series must share the same id, and each group is processed independently by the selected model list.

Execution paths:

1. **Native local DataFrames** (`pandas.DataFrame` and `polars.DataFrame`) use the normal `StatsForecast` implementation. `n_jobs` controls local process parallelism after the DataFrame is grouped by series id.
2. **Explicit local backend** (`MultiprocessBackend`) calls the same underlying core methods with a specified local `n_jobs`; it is useful for parity checks and for code that wants a backend object directly.
3. **Generic backend** (`ParallelBackend`) is the base adapter that forwards to a normal one-job `_StatsForecast` execution. It is mostly useful for tests, fallback behavior, and custom wrappers.
4. **Fugue/distributed backend** (`FugueBackend`) uses Fugue transforms partitioned by id. Passing a Dask, Spark, Ray, or other Fugue-supported DataFrame to top-level `StatsForecast.forecast`/`cross_validation` triggers automatic execution-engine inference.

## Local execution with `n_jobs`

Use local `n_jobs` first unless the user already has a distributed DataFrame or a cluster-backed runtime.

```python
from statsforecast import StatsForecast
from statsforecast.models import Naive, SeasonalNaive

sf = StatsForecast(
    models=[Naive(), SeasonalNaive(season_length=7)],
    freq="D",
    n_jobs=2,             # use 1 for deterministic debugging; -1 for all cores
    fallback_model=Naive() # optional; model failure fallback for forecast/CV
)
forecast = sf.forecast(df=panel_df, h=7)
cv = sf.cross_validation(df=panel_df, h=7, n_windows=2)
```

Operational notes:

- `n_jobs=1` is easiest to debug and avoids process startup overhead.
- `n_jobs=-1` requests all available CPU cores, but the implementation caps actual jobs at the number of series groups.
- More jobs are not always faster. If there are few series, short histories, or expensive serialization, process overhead can dominate.
- The same data/model validation rules apply as in single-process execution: unique model names, valid frequency, future `X_df` for exogenous models, sufficient samples for intervals, and complete id/time/target columns.

## Explicit `MultiprocessBackend`

`MultiprocessBackend` is safe without Dask, Ray, Spark, Java, or a scheduler. It wraps core `forecast` and `cross_validation` by constructing an internal StatsForecast object with the requested `n_jobs`.

```python
from statsforecast.distributed.multiprocess import MultiprocessBackend
from statsforecast.models import Naive

backend = MultiprocessBackend(n_jobs=2)
forecast = backend.forecast(
    df=panel_df,
    models=[Naive()],
    freq="D",
    h=3,
    fallback_model=None,
)
cv = backend.cross_validation(
    df=panel_df,
    models=[Naive()],
    freq="D",
    h=3,
    n_windows=2,
)
```

Use it when:

- writing a smoke test that must compare backend output with normal `StatsForecast` output;
- isolating local parallel behavior from distributed DataFrame routing;
- verifying that `fallback_model` produces the same output as an equivalent healthy model list after a model-level failure.

Do not use it for cluster provisioning. It is local multiprocessing only.

## `ParallelBackend`

`ParallelBackend` is the base backend adapter. It accepts keyword-only parameters and calls the underlying core `forecast` or `cross_validation` path. It does not create a multiprocessing pool by itself.

```python
from statsforecast.core import ParallelBackend
from statsforecast.models import Naive

backend = ParallelBackend()
forecast = backend.forecast(
    df=panel_df,
    models=[Naive()],
    fallback_model=None,
    freq="D",
    h=3,
    X_df=None,
    level=None,
    fitted=False,
    prediction_intervals=None,
    id_col="unique_id",
    time_col="ds",
    target_col="y",
)
```

This is mostly useful for custom adapter code and for understanding the common backend contract. For normal user workflows prefer `StatsForecast(..., n_jobs=...)`, `MultiprocessBackend`, or automatic Fugue routing.

## Automatic routing for Dask, Spark, and Ray DataFrames

When the top-level package is imported, StatsForecast registers a Fugue backend. If `df` is not a native pandas/polars DataFrame, top-level `StatsForecast.forecast` and `StatsForecast.cross_validation` infer a Fugue execution engine from the input DataFrame and execute per-id transforms.

Dask-style sketch:

```python
import dask.dataframe as dd
from statsforecast import StatsForecast
from statsforecast.models import Naive

# Assumes Dask and Fugue-Dask extras are installed and a Dask runtime is available.
ddf = dd.from_pandas(panel_df.assign(unique_id=lambda x: x["unique_id"].astype(str)), npartitions=4)

sf = StatsForecast(models=[Naive()], freq="D")
forecast_ddf = sf.forecast(df=ddf, h=7)
forecast_pdf = forecast_ddf.compute()
```

Spark-style sketch:

```python
from statsforecast import StatsForecast
from statsforecast.models import Naive

# Assumes PySpark/JVM/SparkSession are already available.
sdf = spark.createDataFrame(panel_df.assign(unique_id=lambda x: x["unique_id"].astype(str)))

sf = StatsForecast(models=[Naive()], freq="D")
forecast_sdf = sf.forecast(df=sdf, h=7)
forecast_sdf.show()
```

Ray-style sketch:

```python
import ray
from statsforecast import StatsForecast
from statsforecast.models import Naive

# Assumes Ray and Fugue-Ray extras are installed and Ray runtime is initialized as needed.
rdf = ray.data.from_pandas(panel_df.assign(unique_id=lambda x: x["unique_id"].astype(str))).repartition(4)

sf = StatsForecast(models=[Naive()], freq="D")
forecast_rdf = sf.forecast(df=rdf, h=7)
# Materialization depends on the Ray/Fugue DataFrame object returned in the target version.
```

Important constraints:

- Prefer `unique_id` as a string column for Dask/Ray/Spark. This avoids schema inference and partitioning surprises.
- Results may be lazy. Use the backend's action (`.compute()`, `.show()`, `.collect()`, `.toPandas()`, or `fugue.api.as_pandas(...)`) before validating rows, columns, or values.
- The Dask/Ray/Spark examples are dependency-gated. The minimum verified environment covers base StatsForecast plus local multiprocessing, not these optional runtimes.
- Keep `X_df` in the same backend family as `df` when using exogenous models. Dask `df` with pandas `X_df`, for example, is a common source of transform/cotransform problems.

## Explicit `FugueBackend`

Use `FugueBackend` only when the caller already has a Fugue execution engine or wants to pass Fugue transform configuration.

```python
from statsforecast.distributed.fugue import FugueBackend
from statsforecast.models import Naive

backend = FugueBackend(engine=engine, conf=conf)
forecast = backend.forecast(
    df=distributed_df,
    models=[Naive()],
    fallback_model=None,
    freq="D",
    X_df=None,
    h=7,
    level=None,
    fitted=False,
    prediction_intervals=None,
    id_col="unique_id",
    time_col="ds",
    target_col="y",
)
```

`FugueBackend` partitions by `id_col`. Each partition is converted to pandas for the core StatsForecast work, then emitted back through Fugue with a schema constructed from id/time columns, model aliases, interval columns, and cross-validation columns when applicable.

## Optional dependency groups and runtime expectations

Base StatsForecast includes Fugue. Optional backend extras still need their own packages and runtimes:

| Backend | Package/runtime expectation | Materialization reminder | Verification status in minimum env |
| --- | --- | --- | --- |
| Dask | Dask plus Fugue-Dask support; a local or remote Dask scheduler if using distributed execution. | `.compute()` for Dask DataFrame results. | Not verified; dependency-gated. |
| Ray | Ray plus Fugue-Ray support; Ray runtime must be initialized or discoverable. Some test flows constrain Python versions, so confirm the target Ray release against the target Python. | Ray/Fugue result materialization depends on object type; convert to pandas only after execution. | Not verified; dependency-gated. |
| Spark | Fugue-Spark and PySpark/Spark runtime; Java/JVM and Spark session must work before calling StatsForecast. | `.show()`, `.collect()`, or `.toPandas()` for Spark DataFrame results. | Not verified; dependency-gated. |

Do not silently install or start these systems from a runtime script unless the user explicitly requested environment setup. In Researcher use, state the missing extra and provide a minimal install/runtime checklist.

## Fitted values with distributed frames

For `forecast` fitted values:

```python
sf = StatsForecast(models=[Naive()], freq="D")
forecast_result = sf.forecast(df=distributed_df, h=7, fitted=True)
fitted_result = sf.forecast_fitted_values()
```

Then materialize both results using the backend-specific method before comparing or saving. Fugue may return nullable or Arrow-backed dtypes; for strict equality checks, sort by id/time and align dtypes with the local pandas baseline.

For cross-validation fitted values, be conservative with distributed frames. Top-level distributed `cross_validation` returns forecast/CV rows through the backend, but portable retrieval of `cross_validation_fitted_values()` is not a minimum verified workflow. If CV fitted values are required, first prove the exact target backend/version behavior on a small dataset, or collect a bounded sample to pandas/polars and use the native workflow.

## Local parity and fallback behavior

A reliable local parity check compares the explicit backend to normal `StatsForecast` on a tiny multi-series panel:

```python
from statsforecast import StatsForecast
from statsforecast.distributed.multiprocess import MultiprocessBackend
from statsforecast.models import Naive

models = [Naive()]
expected = StatsForecast(models=models, freq="D").forecast(df=panel_df, h=2)
actual = MultiprocessBackend(n_jobs=1).forecast(df=panel_df, models=models, freq="D", h=2)
```

For `fallback_model`, remember:

- It catches model-level forecast/CV failures and substitutes the fallback model.
- It does not repair input schema, frequency, missing `X_df`, missing optional backend packages, or scheduler/JVM errors.
- If a fallback model is used with `cross_validation(refit=False)` or integer `refit`, the fallback model also needs the required forward-style behavior.
