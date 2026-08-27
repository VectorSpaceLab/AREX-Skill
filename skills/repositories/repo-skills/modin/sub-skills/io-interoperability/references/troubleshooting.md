# I/O and interoperability troubleshooting

## Glob API unavailable

Experimental glob APIs are expected on Ray, Dask, or Unidist engines. If `read_csv_glob` or a glob writer is missing or reports an unsupported engine, set `MODIN_ENGINE=Ray` or `MODIN_ENGINE=Dask` before importing `modin.experimental.pandas` and retry from a fresh process.

## Parser dependencies

- Parquet requires pyarrow or fastparquet.
- XML workflows may require lxml or another compatible parser.
- Excel, HDF, feather, and SQL require their respective pandas-compatible optional dependencies.
- If a reader defaults to pandas, correctness can still be fine for small data, but performance and memory behavior change.

## CSV and JSON edge cases

- Give `dtype`, `parse_dates`, `usecols`, and `index_col` explicitly when exact schema matters.
- Reset or sort indexes after glob reads before comparing to pandas concatenation.
- `read_json_glob` does not support `nrows` other than `None`; use a bounded fixture or write smaller input files instead.
- JSON and XML glob reads may need `check_dtype=False` comparisons because parser dtypes differ.

## SQL safety

Distributed SQL reading needs a good integer `partition_column`, realistic `lower_bound`/`upper_bound`, and a `max_sessions` value that will not overwhelm the database. Keep credentials in environment/connection configuration and do not print connection URLs that contain passwords.

## Custom text parser failures

`read_custom_text` expects the parser to accept a file-like chunk and return a pandas DataFrame with declared columns. Keep the parser top-level and deterministic. If it relies on a nonstandard JSON or CSV parser, check that dependency in the same runtime environment.

## Ray/Dask conversion mismatches

`to_ray` / `from_ray` require Ray engine. `to_dask` / `from_dask` require Dask engine. If the conversion fails with an engine mismatch, it is not a data-format bug; restart the interpreter with the matching engine.

## Direct partition caveats

`unwrap_partitions` and `from_partitions` expose internal partition objects. They are powerful for custom integrations but brittle. Prefer public readers and conversion helpers unless the task explicitly needs partition references, node IP metadata, or custom partition assembly.

## Materialization surprises

`to_pandas()`, `to_numpy()`, Ray Dataset `.to_pandas()`, and Dask `.compute()` can collect all data on the driver. For large data, validate schema, row count, and aggregates on bounded samples instead of materializing the full object.
