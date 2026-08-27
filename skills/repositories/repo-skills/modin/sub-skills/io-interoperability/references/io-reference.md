# Modin I/O reference

## Stable reader guidance

Modin exposes pandas-style readers through `modin.pandas`. Some are distributed, some are partially supported, and some default to pandas internally before distributing the result.

| Reader | Modin status | Notes |
| --- | --- | --- |
| `read_csv`, `read_table`, `read_fwf` | distributed | Also covered by `MODIN_ASYNC_READ_MODE`. Use explicit `dtype`, `parse_dates`, and `usecols` for reproducibility. |
| `read_parquet` | partial | Parameters such as `filters` and `storage_options` are supported; other kwargs and nullable-dtype behavior can be limited. Requires a parquet engine such as pyarrow or fastparquet. |
| `read_json` | partial | Distributed path is focused on JSON-lines use cases. Other modes may default to pandas. |
| `read_sql` | distributed path exists | Use `partition_column`, `lower_bound`, `upper_bound`, and `max_sessions` when you need distributed reads. The partition column must be integer-like. |
| `read_feather` | distributed | Requires the matching optional parser stack. |
| `read_html`, `read_excel`, `read_hdf`, `read_pickle`, `read_xml`, `read_stata`, `read_sas`, `read_clipboard` | default-to-pandas or dependency-sensitive | Acceptable for small data; treat warnings as performance/materialization signals. |

## Async read mode

`MODIN_ASYNC_READ_MODE=True` can apply to `read_csv`, `read_fwf`, `read_table`, and experimental `read_custom_text`. Some parameter combinations still run synchronously. Use a small fixture to verify behavior and correctness before assuming a performance win.

## Experimental glob I/O

Use `modin.experimental.pandas` for multi-file glob APIs. These APIs are engine-gated: Ray, Dask, and Unidist are the expected execution engines.

| API | Purpose | Important caveats |
| --- | --- | --- |
| `read_csv_glob(pattern, **read_csv_kwargs)` | Read multiple CSV files matched by a glob pattern | Reset or sort indexes before comparing to pandas concatenation. Supports `nrows` in native tests. |
| `read_pickle_glob(pattern)` / `DataFrame.modin.to_pickle_glob(pattern)` | Read/write partitioned pickle files | Pattern should describe the partitioned output set. |
| `read_parquet_glob(pattern)` / `DataFrame.modin.to_parquet_glob(pattern)` | Read/write partitioned parquet | Requires pyarrow or fastparquet; only string paths are supported. |
| `read_json_glob(pattern)` / `DataFrame.modin.to_json_glob(pattern)` | Read/write partitioned JSON | `read_json_glob` does not support `nrows` other than `None`. |
| `read_xml_glob(pattern)` / `DataFrame.modin.to_xml_glob(pattern)` | Read/write partitioned XML | Requires XML parser support and may need index reset after concat-like reads. |
| `read_custom_text(path, columns, custom_parser, ...)` | Parse custom text chunks into pandas DataFrames | `custom_parser` receives a file-like input and must return a pandas DataFrame with the expected columns. |

## Distributed SQL

For `modin.experimental.pandas.read_sql`, the partition parameters are Spark-like:

```python
import modin.experimental.pandas as pd

orders = pd.read_sql(
    "SELECT order_id, customer_id, total FROM orders",
    con=engine,
    partition_column="order_id",
    lower_bound=0,
    upper_bound=10_000_000,
    max_sessions=8,
)
```

Use an integer partition column. Keep database credentials in the connection configuration, not in generated scripts or logs. Make sure `max_sessions` is acceptable to the database.

## Safe local glob smoke

The bundled `io_glob_smoke.py` creates temporary local files, reads them through experimental glob APIs, and compares to pandas. It does not use network storage, SQL credentials, or repository fixtures.
