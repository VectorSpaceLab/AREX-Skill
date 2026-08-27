# DataFrame IO And Data Formats

Dask DataFrame IO mirrors pandas where possible, but every reader must also decide partitioning, metadata, filesystem access, and lazy task construction.

## Format Selection

| Format | Choose It For | Watch For |
| --- | --- | --- |
| Parquet | Durable large tabular datasets, column selection, schema preservation, partitioned datasets, predicate/filter pushdown | Requires `pyarrow`; global `_metadata` can be helpful or too large; divisions are not calculated by default. |
| CSV/Text | Ingesting common delimited files, many-file globs, simple interchange | Dtype inference from samples can be wrong; quoted newlines can defeat block splitting; compression limits splitting. |
| JSON | Line-delimited records with regular schema | Non-line JSON is hard to split; heterogeneous records need explicit `meta` or post-cleaning. |
| SQL | Partitionable database tables or SQLAlchemy select expressions | Requires URI strings, drivers, indexed `index_col`, and partitioning information. |
| ORC/HDF | Existing ecosystem formats | Optional dependencies and filesystem constraints apply; HDF is local/POSIX oriented. |
| Bag/Delayed/Map | Custom files, APIs, or records before tabular normalization | Prefer `from_map` over many delayed partitions when layout is regular. |

## CSV And Text

Use `dd.read_csv('path/*.csv')` for many files or a large file. Important options:

- `blocksize`: controls byte-block partitioning for splittable files. Smaller blocks create more partitions; larger blocks reduce scheduler overhead.
- `sample` and `sample_rows`: drive dtype/header inference. Increase them or pass `dtype=` when early rows are not representative.
- `assume_missing=True`: treats inferred integer columns as floats when later missing values may appear.
- `enforce=True`: enforces column consistency across partitions.
- `storage_options`: passes credentials and filesystem options to fsspec for `s3://`, `gcs://`, `abfs://`, and other URLs.
- `include_path_column`: adds the source path, useful for lineage or partition extraction.

Compression is inferred by default. Typical gzip/bz2/xz streams are not safely splittable, so expect one or fewer partitions per compressed file unless the compression format supports random access.

## Parquet Reads

Use `dd.read_parquet(path, columns=..., filters=..., index=..., calculate_divisions=...)` for columnar reads.

Practical guidance:

- Pass `columns` whenever possible. Projection pushdown reduces IO, memory use, and downstream tasks.
- Pass `filters` for row-group or partition pruning when the dataset has useful statistics or hive partitioning.
- Use `index='timestamp'` with `calculate_divisions=True` only when row-group statistics are present and metadata scanning is affordable.
- Use `ignore_metadata_file=True` for very large datasets whose `_metadata` file is too large for a single process.
- Use `split_row_groups='adaptive'` and `blocksize=` when files contain oversized row groups or files should be split into manageable partitions.
- Use `filesystem='fsspec'` unless a workflow explicitly needs an alternative filesystem implementation.

Dask may resize partitions based on selected columns during optimization. This is useful, but early `persist()` can block the optimizer from pushing projections and filters into the read.

## Parquet Writes

Use `df.to_parquet(path, partition_on=..., write_metadata_file=..., name_function=...)`.

Practical guidance:

- Aim for roughly 100-300 MiB in-memory per partition before writing. Use `df.memory_usage_per_partition()` and `df.repartition(...)` to tune.
- `partition_on=[...]` writes hive-style directories such as `year=2026/month=06`; use for low-cardinality filtering columns, not high-cardinality IDs.
- `write_metadata_file=True` can improve later reads for small/medium datasets but may be memory-heavy at scale.
- `name_function(partition_index)` must produce names that sort in partition order.
- Writing one tiny file per partition creates small-file overhead; coalesce partitions first.

## JSON

Use line-delimited JSON for partitionable reads. If records are heterogeneous, normalize with a bag workflow first or provide explicit metadata after loading. Route bag-first malformed-record cleanup to `bag-bytes-workflows`, then return here for dataframe analytics.

## SQL

Dask SQL readers use pandas/SQLAlchemy concepts with Dask-specific partitioning constraints:

- The connection argument must be a URI string, not an engine or live connection.
- `index_col` is required for partitioning and should be indexed in the database.
- Use `npartitions` with numeric min/max bounds, or explicit `divisions` for known ranges/categories.
- `read_sql_query` accepts SQLAlchemy select expressions; arbitrary text queries are not the same as pandas chunked reads.
- Use `from_map` for custom database APIs, manual query partitioning, or cases where SQLAlchemy inference is too limiting.

## Cloud And Remote Storage

Dask delegates URL handling to filesystem libraries such as fsspec implementations. Prefer external credential configuration when possible; otherwise pass `storage_options` to readers/writers. Do not embed secrets in reusable scripts or skill content.

Common patterns:

```python
df = dd.read_csv("s3://bucket/events-*.csv", storage_options={"anon": True})
df = dd.read_parquet("gcs://bucket/table", columns=["id", "amount"])
df.to_parquet("abfs://container/out", storage_options={"account_name": "..."})
```

## Backend Dispatch

Dask DataFrame can dispatch some creation functions through `dataframe.backend`, including `from_dict`, `read_parquet`, `read_json`, `read_orc`, `read_csv`, and `read_hdf`. Backend dispatch is experimental. Use `DataFrame.to_backend()` to move an existing collection when the backend supports it. Route generic backend configuration mechanics to `configuration-diagnostics-cli`.
