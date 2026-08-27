# Distributed execution troubleshooting

Use this checklist when StatsForecast local parallel or distributed DataFrame execution fails. For basic panel schema, model choice, or exogenous feature construction, route to the corresponding sub-skill first.

## First isolate the execution layer

Before debugging a Dask/Ray/Spark problem, prove the same data and model list work locally:

```python
from statsforecast import StatsForecast

local_pdf = distributed_df.compute() if hasattr(distributed_df, "compute") else sample_pdf
sf = StatsForecast(models=models, freq=freq, n_jobs=1, fallback_model=fallback_model)
local_result = sf.forecast(df=local_pdf, h=h, X_df=local_X_pdf)
```

Then compare against:

```python
from statsforecast.distributed.multiprocess import MultiprocessBackend

mp_result = MultiprocessBackend(n_jobs=1).forecast(
    df=local_pdf,
    models=models,
    freq=freq,
    h=h,
    X_df=local_X_pdf,
    fallback_model=fallback_model,
)
```

If both local checks pass, the remaining issue is likely optional dependency, runtime, serialization, partitioning, or materialization related.

## Missing optional backend packages

### Dask errors

Symptoms:

- `ModuleNotFoundError: No module named 'dask'`
- errors importing Fugue-Dask components;
- Dask DataFrame result lacks expected `.compute()` behavior.

Actions:

1. Confirm Dask and Fugue-Dask support are installed in the active environment.
2. Confirm the user is actually passing a Dask DataFrame, not a pandas DataFrame accidentally wrapped in another object.
3. Keep `df` and `X_df` as Dask DataFrames with compatible partitioning and schemas.
4. Materialize with `.compute()` before assertions or saving.

### Ray errors

Symptoms:

- `ModuleNotFoundError: No module named 'ray'`
- Ray runtime initialization failures;
- serialization errors from model objects or custom callables;
- Python-version compatibility messages from Ray.

Actions:

1. Confirm Ray and Fugue-Ray support are installed for the target Python version and platform.
2. Initialize or connect to Ray as required by the user's environment before calling StatsForecast.
3. Use picklable model objects and avoid lambdas or locally scoped custom classes in model/fallback objects.
4. Convert/collect a tiny sample to pandas and verify local StatsForecast output before escalating to Ray.

### Spark/PySpark/JVM errors

Symptoms:

- `ModuleNotFoundError: No module named 'pyspark'`
- Java gateway or JVM startup errors;
- Spark session creation failures;
- schema inference errors when creating a Spark DataFrame.

Actions:

1. Confirm PySpark/Fugue-Spark support is installed.
2. Confirm Java is installed and compatible with the Spark version.
3. Confirm a `SparkSession` can create and show a tiny DataFrame before introducing StatsForecast.
4. Cast `unique_id` to string and keep timestamp columns in a Spark-compatible type.
5. Materialize with `.show()`, `.collect()`, or `.toPandas()` depending on the user need.

## `unique_id` type and partitioning problems

Symptoms:

- missing or duplicated series in output;
- backend schema mismatch;
- unexpected repartitioning behavior;
- Spark or Arrow complains about mixed id types.

Guidance:

- Prefer `unique_id` as string for Dask/Ray/Spark workflows.
- Ensure each series id is stable and maps to exactly one logical time series.
- Do not mix integers, strings, `None`, and categorical values in the same id column.
- For custom columns, pass `id_col`, `time_col`, and `target_col` consistently to both `forecast` and `cross_validation`.
- Partitioning is by id. If a custom distributed transformation repartitions data before StatsForecast, it must not split a single logical id into inconsistent schemas or missing future rows.

Minimal cast pattern:

```python
panel_df = panel_df.assign(unique_id=panel_df["unique_id"].astype(str))
```

For Spark, cast before `spark.createDataFrame(...)` when possible.

## Lazy result materialization

StatsForecast distributed calls often return backend-native or Fugue-managed lazy results.

| Backend/result style | Typical action |
| --- | --- |
| Dask DataFrame | `result.compute()` |
| Spark DataFrame | `result.show()`, `result.collect()`, or `result.toPandas()` |
| Fugue abstraction | `fugue.api.as_pandas(result)` for bounded results |
| Ray/Fugue Ray result | Use the object-specific conversion in the target runtime; validate on a tiny sample first. |

Do not compare a lazy result directly to a pandas DataFrame. Materialize, sort by id/time (and `cutoff` for cross-validation), and align dtypes if strict equality is needed.

## Fitted values with distributed frames

For forecast fitted values:

```python
sf = StatsForecast(models=models, freq=freq)
forecast_result = sf.forecast(df=distributed_df, h=h, X_df=distributed_X_df, fitted=True)
fitted_result = sf.forecast_fitted_values()
```

Troubleshooting actions:

- Call `forecast(..., fitted=True)` before `forecast_fitted_values()`; otherwise StatsForecast raises that fitted values are unavailable.
- Materialize both `forecast_result` and `fitted_result` using the backend-specific method.
- Expect nullable or Arrow-backed dtypes from distributed/Fugue paths. For tests, sort rows and cast columns to the local pandas baseline dtypes before `assert_frame_equal`.
- Use the same `X_df` backend type as `df` when fitted forecasts need future exogenous values.
- Distributed cross-validation fitted value retrieval is not a minimum verified workflow. If the user asks for CV fitted values at scale, first prove the target backend behavior on a small dataset or run the CV fitted workflow on a bounded native pandas/polars sample.

## `n_jobs` surprises and local fallback

Symptoms:

- `n_jobs=8` is not faster than `n_jobs=1`;
- local multiprocessing hangs or is slow in a notebook/interactive environment;
- child process pickling errors;
- user expects `n_jobs` to start Dask/Ray/Spark.

Guidance:

- `n_jobs` is local CPU process parallelism for native pandas/polars execution. It does not provision a cluster.
- Actual local jobs are capped by the number of series groups. If there are only two series, asking for 32 jobs cannot create useful extra parallelism.
- Use `n_jobs=1` for debugging, deterministic error messages, and small panels.
- Use `n_jobs=2` or a small positive number for smoke tests; increase only after local correctness is proven.
- Avoid custom model classes defined inside functions when multiprocessing; use importable, picklable classes.
- In environments with process-spawn restrictions, fall back to `n_jobs=1` and explain that local parallelism is environment-limited.

## `fallback_model` does and does not help

Works for:

- a model object failing during `forecast` or `cross_validation` for one or more series;
- preserving output shape by substituting an alternate model such as `Naive()`.

Does not work for:

- missing Dask/Ray/Spark/PySpark packages;
- broken JVM/SparkSession/Ray/Dask runtime;
- invalid or missing id/time/target columns;
- missing future exogenous values in `X_df`;
- invalid frequency or unsorted/malformed timestamps;
- model alias collisions;
- insufficient history for prediction intervals.

When using `cross_validation(refit=False)` or integer `refit`, both the primary model and fallback model must support the forward-style behavior required by the rolling-window implementation. If unsure, use `refit=True`.

## Exogenous `X_df` in distributed execution

Symptoms:

- errors from Fugue cotransform/zip logic;
- missing future rows for some ids;
- forecast output has fewer rows than expected;
- schema mismatch between `df` and `X_df`.

Actions:

1. Verify locally with pandas first.
2. Ensure `X_df` contains every `id_col` and every future `time_col` value for the horizon.
3. Use the same id/time column names in `df` and `X_df`.
4. Convert `X_df` to the same distributed backend family as `df`.
5. For Spark, ensure `df` and `X_df` have compatible column types before creating distributed DataFrames.

## Prediction intervals and output columns

Symptoms:

- error says `level` must be specified when using `prediction_intervals`;
- interval columns are missing or ordered differently than expected;
- series are too short for conformal intervals.

Guidance:

- When passing `prediction_intervals`, also pass `level=[...]`.
- Interval columns are emitted per model, with lower columns for larger levels before smaller levels in the inspected implementation, followed by high columns for ascending levels.
- Conformal intervals require enough samples per series. If some series are short, remove them, reduce horizon/window requirements, or avoid conformal intervals for that run.

## Distributed simulation

Top-level `StatsForecast.simulate` is not a distributed workflow in the minimum evidence. When called with non-native distributed inputs, it warns and falls back to native execution behavior. For simulation at scale, first collect a bounded native sample and verify the required model behavior, then design backend-specific scaling separately.

## Quick diagnostic checklist

1. Can `StatsForecast(..., n_jobs=1).forecast(...)` run on a tiny pandas version of the data?
2. Can `MultiprocessBackend(n_jobs=1)` match that output?
3. Are `unique_id` values strings and non-null for distributed frames?
4. Are `df` and `X_df` the same backend family?
5. Are optional packages installed for Dask/Ray/Spark, and can the backend run a tiny non-StatsForecast DataFrame action?
6. Did you materialize the lazy output before comparing?
7. If fitted values are needed, did the call use `forecast(..., fitted=True)` first?
8. If using `fallback_model`, is the failure actually model-level rather than data/runtime-level?
