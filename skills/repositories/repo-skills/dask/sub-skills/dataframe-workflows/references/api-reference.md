# Dask DataFrame API Reference

This reference summarizes the public `dask.dataframe` surfaces most often needed for tabular workflows. Prefer installed-package introspection for exact signatures in a target environment when compatibility is critical.

## Creation And Conversion

| API | Use When | Notes |
| --- | --- | --- |
| `dd.from_pandas(data, npartitions=None, sort=True, chunksize=None)` | Starting from an in-memory pandas DataFrame or Series | `sort=True` sorts by index and can create known divisions; `sort=False` preserves order but usually leaves divisions unknown. |
| `dd.from_map(func, *iterables, meta=..., divisions=..., label=..., enforce_metadata=...)` | Each partition can be produced by mapping a pure function over partition descriptors | Prefer this for custom readers when a simple map captures the layout; provide `meta` and `divisions` when known. |
| `dd.from_delayed(values, meta=..., divisions=..., prefix=..., verify_meta=True)` | Loading partitions from arbitrary delayed tasks | Use only when `from_map` is too restrictive; provide `meta` to avoid sampling surprises. |
| `dd.from_dask_array(x, columns=None, index=None, meta=None)` | Converting a Dask Array into a DataFrame or Series | Route array chunking issues to `array-workflows`; here focus on column/index metadata. |
| `DataFrame.to_dask_array(lengths=None, meta=None)` | Moving dataframe values to array workflows | Known partition lengths may be needed for concrete array chunks. |
| `DataFrame.to_bag`, `DataFrame.to_delayed`, `DataFrame.to_records` | Interop with bags, delayed, or record arrays | Use explicit metadata and avoid computing during graph construction. |

## IO Functions

| API | Core Parameters | Typical Use |
| --- | --- | --- |
| `dd.read_csv(urlpath, blocksize='default', sample=256000, assume_missing=False, storage_options=None, include_path_column=False, **kwargs)` | File glob/URL, partition blocksize, dtype inference controls | Ingest many CSV files or split large CSV files by byte block. |
| `dd.read_table`, `dd.read_fwf` | Similar to pandas text readers plus Dask partitioning | Delimited or fixed-width text. |
| `dd.read_json(url_path, blocksize=None, orient='records', lines=None, storage_options=None, **kwargs)` | Line-delimited JSON can be partitioned; non-line JSON is usually one partition per file | Semi-structured files when dataframe schema is regular enough. |
| `dd.read_parquet(path, columns=None, filters=None, categories=None, index=None, calculate_divisions=False, split_row_groups='infer', blocksize='default', filesystem='fsspec', **kwargs)` | Column pruning, row-group splitting, filter pushdown, optional division calculation | Preferred durable format for large tabular workflows. |
| `DataFrame.to_parquet(path, write_metadata_file=None, partition_on=None, name_function=None, storage_options=None, **kwargs)` | One file per partition by default | Repartition before writing when partitions are too small or too large. |
| `dd.read_sql_table`, `dd.read_sql_query`, `dd.read_sql` | SQLAlchemy URI string, `index_col`, `npartitions`/`divisions`/limits | Requires partitionable queries and database drivers. |

## DataFrame And Series Methods

| Method | Use When | Workflow Notes |
| --- | --- | --- |
| `.map_partitions(func, *args, meta=..., enforce_metadata=True, transform_divisions=True, clear_divisions=False, **kwargs)` | Applying a pandas-level function independently to each partition | Provide `meta`; clear divisions if the index ordering or values change unpredictably. |
| `.apply(func, axis=1, meta=..., **kwargs)` | Row-wise pandas-style logic that cannot be vectorized | Slower than vectorized operations; `axis=1` row apply requires `meta`. |
| `.assign`, `.astype`, `.rename`, `.drop`, `.fillna`, `.replace`, `.query`, `.eval` | Lazy pandas-like transformations | These compose well and are optimizer-friendly when projections can be pushed down. |
| `.loc` | Selecting by index ranges | Fast with known sorted divisions; unknown divisions may require scanning all partitions. |
| `.set_index(column, sorted=False, divisions=None, npartitions=None, shuffle_method=None, **kwargs)` | Creating a sorted index for repeated indexed operations | Expensive unless sorted/divisions are supplied; persist only after filters/projections that should optimize into IO. |
| `.repartition(npartitions=..., divisions=..., partition_size=..., freq=...)` | Resizing or redividing partitions | Use after large filters, before expensive shuffles, or before writing datasets. |
| `.shuffle(on, shuffle_method=None, npartitions=None, ignore_index=False, **kwargs)` | Explicitly repartitioning by one or more columns | Prefer higher-level `set_index`, merge, or groupby options unless explicit shuffle is intended. |
| `.merge`, `.join` | Combining tables | Index joins and large-to-small joins are cheaper than non-index large-large column joins. |
| `.groupby(...).agg`, `.sum`, `.mean`, `.nunique`, `.apply` | Split-apply-combine operations | Built-in reductions are efficient; arbitrary `apply` may shuffle unless grouped on known divisions/index. |
| `.categorize(columns=..., index=..., split_every=...)` | Converting unknown categoricals to known categoricals | Requires scanning data; use once for multiple columns instead of repeated `.cat.as_known()`. |
| `.memory_usage_per_partition()` | Sizing partitions | Useful before repartitioning or diagnosing memory-heavy workloads. |

## Groupby Aggregation

Use `dd.Aggregation(name, chunk, agg, finalize=None)` for custom reductions that can be expressed as partition-local chunks, tree aggregation, and optional finalization. The `name` must be unique enough to avoid collisions with existing reductions. Chunk and aggregate functions receive grouped pandas objects or grouped intermediate objects, not full Dask collections.

Use `split_out=` on high-cardinality groupby reductions when the output should remain partitioned. Some reductions choose a split-out default based on grouping keys; set it explicitly when output cardinality is known.

## Query Planning And Optimizer

Dask DataFrame uses logical query planning through the dataframe expression system. Common inspection methods are:

- `df.optimize(fuse=True)`: return an optimized DataFrame expression.
- `df.pprint()`: print a text representation of the current plan without Graphviz.
- `df.explain(stage='fused', format=None)`: render a query-plan graph; requires Graphviz support.
- `df.visualize()`: graph visualization for collection tasks; route graph internals to `core-graphs-schedulers`.

Optimizer behavior includes projection pushdown, filter pushdown, partition pruning, shuffle avoidance when partitioning knowledge is available, and automatic partition resizing around IO. Avoid early `persist()` before filters/projections that should be pushed into reads.

## Configuration Touchpoints

Set these through `dask.config.set` or YAML before importing `dask.dataframe` when import-time behavior matters:

| Config Key | Purpose |
| --- | --- |
| `dataframe.backend` | Select pandas or another registered dataframe backend for dispatchable creation functions. |
| `dataframe.shuffle.method` | Choose shuffle strategy such as disk, tasks, or peer-to-peer when available. |
| `dataframe.convert-string` | Control automatic conversion of object string columns to pyarrow-backed strings. |
| `dataframe.query-planning` | Control dataframe query-planning behavior; set before first dataframe import in deterministic scripts. |
| `dataframe.parquet.*` | Tune parquet metadata task sizing and related read behavior. |

For generic config files, CLI inspection, and environment variables, route to `configuration-diagnostics-cli`.
