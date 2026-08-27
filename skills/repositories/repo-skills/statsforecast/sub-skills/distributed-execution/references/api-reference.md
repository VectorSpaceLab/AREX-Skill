# Distributed execution API reference

This reference lists the StatsForecast execution APIs relevant to local and optional distributed execution. It intentionally omits model-selection details and data-schema fundamentals.

## Imports

```python
from statsforecast import StatsForecast
from statsforecast.core import ParallelBackend
from statsforecast.distributed.multiprocess import MultiprocessBackend
from statsforecast.distributed.fugue import FugueBackend
from statsforecast.models import Naive
```

The top-level `statsforecast` import registers the Fugue backend used for automatic routing of non-native DataFrame objects.

## `StatsForecast` constructor

```python
StatsForecast(
    models: list,
    freq: str | int,
    n_jobs: int = 1,
    fallback_model = None,
    verbose: bool = False,
)
```

Key execution parameters:

- `models`: instantiated StatsForecast model objects. Their display names must be unique; set `alias=` on models when needed.
- `freq`: pandas/polars-compatible frequency string such as `"D"`, `"H"`, `"MS"`, or an integer frequency for integer time indexes.
- `n_jobs`: local parallelism for native pandas/polars execution. `1` means single process; `-1` requests all available CPU cores and is capped by the number of series groups.
- `fallback_model`: optional instantiated model used only when a model fails inside `forecast` or `cross_validation`.
- `verbose`: progress bar for single-job native execution.

## `StatsForecast.forecast`

```python
sf.forecast(
    h: int,
    df,
    X_df = None,
    level: list[int] | None = None,
    fitted: bool = False,
    prediction_intervals = None,
    id_col: str = "unique_id",
    time_col: str = "ds",
    target_col: str = "y",
)
```

Execution behavior:

- Native pandas/polars input uses the local core implementation and honors `sf.n_jobs`.
- Dask/Spark/Ray/Fugue-supported input triggers backend inference and runs through the Fugue backend.
- `X_df` is required when selected models use future exogenous variables; keep it in the same backend family as `df` for distributed execution.
- `fitted=True` stores in-sample fitted values for later `sf.forecast_fitted_values()` retrieval.
- If `prediction_intervals` is supplied, `level` must also be supplied.

Native local example:

```python
sf = StatsForecast(models=[Naive()], freq="D", n_jobs=2)
forecast = sf.forecast(df=panel_df, h=7)
```

Distributed DataFrame example:

```python
sf = StatsForecast(models=[Naive()], freq="D")
result = sf.forecast(df=distributed_panel_df, h=7)
# Then materialize with the backend-specific method: compute/show/collect/toPandas/as_pandas.
```

## `StatsForecast.forecast_fitted_values`

```python
sf.forecast_fitted_values()
```

Call only after `sf.forecast(..., fitted=True)`. With native pandas/polars it returns a native DataFrame. With distributed inputs it delegates to the active backend and may return a backend-specific lazy DataFrame; materialize before comparing or exporting.

## `StatsForecast.cross_validation`

```python
sf.cross_validation(
    h: int,
    df,
    n_windows: int = 1,
    step_size: int = 1,
    test_size: int | None = None,
    input_size: int | None = None,
    level: list[int] | None = None,
    fitted: bool = False,
    refit: bool | int = True,
    prediction_intervals = None,
    id_col: str = "unique_id",
    time_col: str = "ds",
    target_col: str = "y",
)
```

Execution behavior:

- Native pandas/polars input uses the local core implementation and honors `sf.n_jobs`.
- Dask/Spark/Ray/Fugue-supported input routes through a Fugue backend.
- `refit=False` or integer `refit` requires models that implement forward-style prediction for the rolling windows; otherwise use `refit=True`.
- Distributed cross-validation returns CV forecast rows. Portable retrieval of CV fitted values for distributed frames is not part of the minimum verified workflow.

## `ParallelBackend`

```python
backend = ParallelBackend()
backend.forecast(
    *,
    models,
    fallback_model,
    freq,
    h,
    df,
    X_df,
    level,
    fitted,
    prediction_intervals,
    id_col,
    time_col,
    target_col,
)
backend.cross_validation(
    *,
    df,
    models,
    freq,
    fallback_model,
    h,
    n_windows,
    step_size,
    test_size,
    input_size,
    level,
    refit,
    fitted,
    prediction_intervals,
    id_col,
    time_col,
    target_col,
)
```

`ParallelBackend` is the common backend contract. It constructs an internal one-job StatsForecast runner and forwards to the core `forecast`/`cross_validation` implementations. Use it for custom backend wrappers or for verifying fallback behavior, not as a replacement for normal `StatsForecast(..., n_jobs=...)`.

## `MultiprocessBackend`

```python
MultiprocessBackend(n_jobs: int)
```

Methods:

```python
backend.forecast(df, models, freq, fallback_model=None, **kwargs)
backend.cross_validation(df, models, freq, fallback_model=None, **kwargs)
```

Accepted `**kwargs` are the corresponding core `forecast` or `cross_validation` keyword arguments, such as `h`, `X_df`, `level`, `fitted`, `prediction_intervals`, and custom column names.

Minimal parity check:

```python
from statsforecast import StatsForecast
from statsforecast.distributed.multiprocess import MultiprocessBackend
from statsforecast.models import Naive

models = [Naive()]
expected = StatsForecast(models=models, freq="D").forecast(df=panel_df, h=2)
actual = MultiprocessBackend(n_jobs=1).forecast(
    df=panel_df,
    models=models,
    freq="D",
    h=2,
)
```

## `FugueBackend`

```python
FugueBackend(engine=None, conf=None, **transform_kwargs)
```

Methods:

```python
backend.forecast(
    *,
    df,
    freq,
    models,
    fallback_model,
    X_df,
    h,
    level,
    fitted,
    prediction_intervals,
    id_col,
    time_col,
    target_col,
)
backend.forecast_fitted_values()
backend.cross_validation(
    *,
    df,
    freq,
    models,
    fallback_model,
    h,
    n_windows,
    step_size,
    test_size,
    input_size,
    level,
    refit,
    fitted,
    prediction_intervals,
    id_col,
    time_col,
    target_col,
)
```

Use cases:

- explicit Fugue engine injection;
- passing Fugue transform kwargs;
- controlled Dask/Spark/Ray execution once runtime dependencies are already installed.

Internals relevant for debugging:

- Partitioning is by `id_col`.
- Each partition uses a one-job local StatsForecast runner.
- Output schema is built from id/time columns plus model aliases and optional interval columns. Cross-validation output also includes `cutoff` and `target_col`.
- `forecast(..., fitted=True)` stores intermediate serialized forecast/fitted pairs and persists them to avoid recomputing fitted values.

## Expected output columns

Forecast without intervals:

```text
[id_col, time_col, <model_alias_1>, <model_alias_2>, ...]
```

Forecast with `level=[80, 90]`:

```text
[id_col, time_col,
 <model>, <model>-lo-90, <model>-hi-90, <model>-lo-80, <model>-hi-80, ...]
```

Cross-validation without intervals:

```text
[id_col, time_col, "cutoff", target_col, <model_alias_1>, <model_alias_2>, ...]
```

Exact column order can matter in parity checks. Sort rows by `id_col`, `time_col`, and `cutoff` when present before comparing values.

## Version and environment notes

- StatsForecast package inspection evidence covered version `2.1.1`.
- The minimum verified environment covered base package imports, Fugue import, and local `MultiprocessBackend` smoke behavior.
- Optional Dask, Ray, Spark, and PySpark/JVM runtime behavior must be verified in the target environment before treating distributed examples as runnable.
