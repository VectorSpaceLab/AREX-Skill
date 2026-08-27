# DataFrame Troubleshooting

## Missing Dependencies

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: pandas` or dataframe import failure | DataFrame dependencies are not installed | Install Dask with dataframe dependencies or add pandas to the active environment. |
| `ModuleNotFoundError: pyarrow` when reading/writing Parquet or pyarrow strings | Parquet and pyarrow-backed strings require pyarrow | Install pyarrow, or use a format/backend that does not require it. |
| SQL reader import errors | SQLAlchemy or a database driver is missing | Install `sqlalchemy` plus the driver package for the URI scheme. |
| ORC/HDF errors | Optional format dependencies are missing or unsupported filesystem is used | Install the relevant optional dependency and verify storage constraints. |

Use the configuration/diagnostics sub-skill for generic environment inspection and CLI checks.

## PyArrow String Conversion Surprises

Symptoms:

- Object string columns become `string[pyarrow]` or pandas extension strings.
- Tests fail because expected dtype is `object`.
- A dependency-specific string operation behaves differently.

Fixes:

- Set `dataframe.convert-string` before importing `dask.dataframe` in a fresh process.
- In tests, compare values rather than exact string dtype unless dtype is the behavior under test.
- Pass explicit `meta` with intended dtypes when using custom partition functions.

## `dataframe.query-planning` Import-Time Config

The dataframe query-planning flag and related dataframe import behavior should be set before first importing `dask.dataframe`. Changing the config after dataframe modules are imported may not affect already-loaded classes or expression registration.

Pattern for deterministic scripts:

```python
import dask

dask.config.set({"dataframe.query-planning": True})
import dask.dataframe as dd
```

Use a new Python process when validating import-time dataframe config changes.

## Unknown Divisions

Symptoms:

- `df.divisions` is all `None`.
- Index `.loc` scans more data than expected.
- Index joins or groupby/apply are slower than expected.
- Operations complain about unknown divisions or sortedness.

Fixes:

- Use `dd.from_pandas(..., sort=True)` when starting from sorted pandas data.
- Use `set_index` to create sorted divisions, but recognize it may shuffle.
- Pass known `divisions` to `from_map`/`from_delayed` when your loader descriptors prove partition boundaries.
- For Parquet, use `index=` and `calculate_divisions=True` only when row-group statistics make metadata scanning affordable.
- Clear divisions after functions that reorder or replace the index unpredictably.

## Expensive Shuffle

Symptoms:

- `set_index`, non-index joins, `groupby.apply`, or explicit `shuffle` is slow or memory-heavy.
- Workers spill or disk/network use spikes.

Fixes:

- Avoid large-large non-index joins when possible; index one or both sides first if reused.
- Join a large Dask DataFrame with a small pandas DataFrame or single-partition Dask DataFrame when feasible.
- Filter and project columns before shuffling.
- Repartition to reasonable partition sizes before shuffle-heavy steps.
- Choose `dataframe.shuffle.method` or method-level `shuffle_method` deliberately for the scheduler context.
- Persist only after optimizer-friendly filtering/projection and after an expensive shuffle if the result will be reused.

## Metadata Inference Failures

Symptoms:

- Errors mention `meta`, metadata mismatch, columns not matching, or fake data execution.
- `map_partitions`/`apply` works on real data but fails during graph construction.
- Empty first partitions infer wrong dtypes.

Fixes:

- Provide `meta` as an empty pandas DataFrame/Series or an ordered dtype mapping.
- Ensure output column order exactly matches `meta`.
- Use top-level functions for partition functions if multiprocessing/distributed serialization is involved.
- Set `enforce_metadata=False` only when you intentionally accept looser runtime metadata; prefer fixing `meta` first.
- If the index changes unpredictably, clear divisions to avoid stale partition knowledge.

## Known And Unknown Categories

Symptoms:

- `.cat.categories` fails or returns placeholder categories.
- Parquet round trip loses known category state.
- Per-partition categorical values differ.

Fixes:

- Check `df[col].cat.known`.
- Use `df.categorize(columns=[...])` once for all columns that need known categories.
- Use dtype declarations in CSV readers for categorical columns, or pandas `CategoricalDtype` when known categories are available.
- After Parquet reads, restore known categories only if an operation requires them.

## Parquet Schema, Filters, And Metadata

Symptoms:

- Schema mismatch across files.
- `filters` do not prune data.
- `calculate_divisions=True` is slow or still gives unknown divisions.
- Reading remote Parquet metadata is slow.

Fixes:

- Write consistent schemas; cast columns before writing if upstream partitions differ.
- Pass `columns=` to minimize schema and IO surface.
- Use filters that match actual dataset columns, hive partition columns, or row-group statistics.
- Use `ignore_metadata_file=True` when a huge `_metadata` file is the bottleneck.
- Avoid `calculate_divisions=True` on large remote datasets unless a global metadata file and index statistics make it practical.
- Set `split_row_groups` and `blocksize` for oversized files or row groups.

## CSV Dtype And Parsing Problems

Symptoms:

- Later partitions fail because sampled rows inferred the wrong dtype.
- Integer columns with missing values fail.
- Quoted newlines break block parsing.

Fixes:

- Pass explicit `dtype=` for unstable columns.
- Use `assume_missing=True` for integer columns that may contain missing values.
- Increase `sample`/`sample_rows` if the header and representative rows are farther into the file.
- Use `blocksize=None` for files with complex quoted records that cannot be split safely.

## SQL Partitioning Problems

Symptoms:

- SQL readers require `index_col` or partition bounds.
- Connections cannot be serialized.
- Database receives too many expensive range queries.

Fixes:

- Pass a URI string, not a live SQLAlchemy engine/connection.
- Choose an indexed numeric or ordered `index_col`.
- Provide `npartitions`, `limits`, or explicit `divisions` based on database statistics.
- Use `from_map` for custom partition queries or APIs that SQLAlchemy cannot express cleanly.
