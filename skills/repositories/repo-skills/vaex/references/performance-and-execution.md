# Vaex Performance and Execution Notes

Use this reference for cross-cutting Vaex behavior that affects DataFrame, IO, analytics, plotting, ML, server, and CLI workflows.

## Lazy out-of-core mental model

Vaex DataFrames are designed for larger-than-memory tabular data. They keep data in files or Arrow-like buffers where possible and delay computation until a result is requested.

Practical consequences:

- Derived columns should usually be virtual columns: `df['z'] = df.x + df.y`.
- Filtering and selections are shallow/lazy masks rather than eager row copies.
- Aggregations return compact results such as scalars, group tables, or grids.
- Full `.values`, `to_pandas_df`, large `evaluate`, or NumPy conversion can materialize data and should be deliberate.
- For previews and validation, use bounded `evaluate(..., i1=0, i2=...)`, `head`, `count`, or chunked iterators.

## Memory-mapped formats

Vaex is strongest when repeated analysis uses memory-mappable HDF5 or Arrow-family files. CSV is convenient for interchange but usually not ideal for repeated large scans.

Workflow pattern:

1. Open or ingest source data.
2. Convert to HDF5/Arrow/Parquet when repeated queries are expected.
3. Validate row count, columns, and at least one aggregate.
4. Reopen the converted file for analysis.

Route concrete file conversion to [../sub-skills/io-conversion/SKILL.md](../sub-skills/io-conversion/SKILL.md).

## Execution controls

Vaex exposes runtime controls through `vaex.settings` and `VAEX_*` variables. The most common performance-related controls are:

| Area | Setting examples | Notes |
| --- | --- | --- |
| Threads | `VAEX_NUM_THREADS`, `VAEX_NUM_THREADS_IO`, `vaex.settings.main.thread_count` | Set before import/process startup for reproducibility. |
| Chunking | `VAEX_CHUNK_SIZE`, `VAEX_CHUNK_SIZE_MIN`, `VAEX_CHUNK_SIZE_MAX` | Smaller chunks can reduce memory pressure; larger chunks can improve throughput. |
| Memory mapping | `VAEX_MMAP` | Usually leave enabled. Disable only for a specific filesystem/runtime reason. |
| Cache | `VAEX_CACHE`, `VAEX_CACHE_MEMORY_SIZE_LIMIT`, `VAEX_CACHE_DISK_SIZE_LIMIT`, `VAEX_CACHE_PATH` | Plan cache paths for services and remote files. |
| Data/cache directories | `VAEX_DATA_PATH`, `VAEX_FS_PATH`, `VAEX_HOME` | Important when example datasets, cloud cache, or server imports would otherwise use a default home directory. |
| Progress | `VAEX_PROGRESS`, `vaex.progress` helpers | Use simple/rich/widget progress according to terminal vs notebook context. |

For CLI/settings details, read [../sub-skills/cli-settings/SKILL.md](../sub-skills/cli-settings/SKILL.md).

## Validation before expensive work

Before running a large scan, conversion, groupby, plot, ML fit, or service endpoint:

- Confirm the DataFrame columns and dtypes.
- Evaluate a small bounded slice for derived expressions.
- Count rows or a selection.
- Check cardinality for groupby or join keys.
- For conversion, dry-run/list columns and keep failed-output cleanup explicit.
- For plotting, aggregate rather than scatter if row count is large.
- For sklearn-like ML wrappers, remember that fit/predict copies selected features into memory; transform can remain lazy.
- For servers, use loopback/TestClient-style checks before binding public interfaces.

## Common performance anti-patterns

| Anti-pattern | Better pattern |
| --- | --- |
| `df.to_pandas_df()` on a huge file to compute a scalar | `df.mean`, `df.sum`, `df.count`, or `df.groupby(...).agg(...)` |
| `df['new'] = numpy_array` for a large derived feature | `df['new'] = df.x * 2 + df.y` virtual expression |
| Scatter plotting millions of rows | `df.viz.heatmap` or histogram with limits/shape |
| Large CSV repeatedly opened for analytics | Convert once to HDF5/Arrow/Parquet and reopen |
| Broad `vaex test` or benchmarks as health checks | Focused smoke scripts and selected native candidates |
| Starting `vaex server` on `0.0.0.0` for a quick check | In-process/default server smoke or loopback listener |

## When to stop and ask

Ask before deleting conversion outputs, mutating global settings/aliases, installing broad optional extras, exposing private data through a listener, running benchmark-scale jobs, or contacting cloud/TAP/public services that require credentials or network trust.
