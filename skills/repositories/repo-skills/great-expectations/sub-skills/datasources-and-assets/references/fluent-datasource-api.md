# Fluent Datasource API

GX Core uses a fluent datasource API under `context.data_sources`. A datasource names a backend connection, a data asset names a logical dataset within that backend, and a batch definition describes how GX should retrieve one or more batches from that asset.

## DataSourceManager Pattern

Create a context with `gx.get_context(...)`, then use `context.data_sources`:

```python
import great_expectations as gx

context = gx.get_context(mode="ephemeral")
datasource = context.data_sources.add_pandas_filesystem(
    name="local_files",
    base_directory="data",
)
```

Core manager operations include:

| Operation | Use |
| --- | --- |
| `context.data_sources.add_*` | Create a datasource and fail if a duplicate or invalid config is rejected. |
| `context.data_sources.add_or_update_*` | Create or replace a datasource by name, useful for idempotent setup. |
| `context.data_sources.update_*` | Update an existing datasource of a known family. |
| `context.data_sources.delete(name)` / `delete_*` | Remove a datasource by name. |
| `context.data_sources.get(name)` | Retrieve one datasource and then call asset methods on it. |
| `context.data_sources.all()` | Inspect all configured datasources. |

The verified public factories include local/base families such as `add_pandas`, `add_pandas_filesystem`, `add_sqlite`, `add_sql`, `add_spark`, plus optional factory families for S3/GCS/Azure/DBFS file stores and warehouses such as Postgres, Redshift, Snowflake, BigQuery, Databricks SQL, SQL Server, Alloy, Aurora, Citus, Fabric, Fabric Power BI, and Neon. Matching `add_or_update_*`, `update_*`, and `delete_*` methods are available for the same families.

## Pandas Dataframe Datasource

Use `add_pandas` for in-memory pandas dataframes supplied at runtime.

```python
import pandas as pd
import great_expectations as gx

context = gx.get_context(mode="ephemeral")
datasource = context.data_sources.add_pandas(name="runtime_pandas")
asset = datasource.add_dataframe_asset(name="orders_dataframe")
batch_definition = asset.add_batch_definition_whole_dataframe(name="whole_dataframe")

batch = batch_definition.get_batch(
    batch_parameters={"dataframe": pd.DataFrame({"id": [1, 2], "amount": [10, 20]})}
)
```

Verified signatures:

- `context.data_sources.add_pandas(name_or_datasource=None, *, name: str, id=None) -> PandasDatasource`
- `PandasDatasource.add_dataframe_asset(name: str, batch_metadata: dict | None = None) -> DataFrameAsset`
- Dataframe batch parameters must be exactly `{"dataframe": pandas_dataframe}`.

`PandasDatasource` also exposes reader-backed assets for many pandas readers, but use `add_pandas_filesystem` for reusable local or networked file assets because it stores a base directory and discovers files through path assets.

## Local or Networked Filesystem Datasource

Use `add_pandas_filesystem` when files are reachable from the Python process through a local path or mounted/networked filesystem.

```python
context = gx.get_context(mode="ephemeral")
datasource = context.data_sources.add_pandas_filesystem(
    name="local_files",
    base_directory="data",
)
asset = datasource.add_csv_asset(name="orders_csv")
batch_definition = asset.add_batch_definition_monthly(
    name="monthly_orders",
    regex=r"orders_(?P<year>\\d{4})_(?P<month>\\d{2})\\.csv",
)
```

Verified signature:

- `context.data_sources.add_pandas_filesystem(name_or_datasource=None, *, name: str, id=None, base_directory: pathlib.Path, data_context_root_directory: pathlib.Path | None = None) -> PandasFilesystemDatasource`

Common filesystem asset factories include:

| Method | Typical use |
| --- | --- |
| `add_csv_asset(name, **pandas_read_csv_options)` | CSV files. Supports reader options such as `sep`, `header`, `names`, `dtype`, `parse_dates`, `encoding`, `compression`, `storage_options`, and related pandas CSV options. |
| `add_excel_asset(name, **pandas_read_excel_options)` | Excel files. Requires a compatible pandas Excel engine dependency for the file format. |
| `add_parquet_asset(name, **pandas_read_parquet_options)` | Parquet files. Requires a compatible parquet engine such as `pyarrow` or `fastparquet`. |

Filesystem assets use files under the datasource `base_directory` unless the asset type has backend-specific path or prefix arguments. Keep `base_directory` stable for persistent contexts because batch definitions store relative discovery behavior.

## SQLite Datasource

Use `add_sqlite` for local SQLite databases through SQLAlchemy connection strings.

```python
context = gx.get_context(mode="ephemeral")
datasource = context.data_sources.add_sqlite(
    name="local_sqlite",
    connection_string="sqlite:///analytics.db",
)
table_asset = datasource.add_table_asset(name="orders_table", table_name="orders")
query_asset = datasource.add_query_asset(
    name="recent_orders",
    query="SELECT id, amount, created_at FROM orders WHERE amount IS NOT NULL",
)
```

Verified signature:

- `context.data_sources.add_sqlite(name_or_datasource=None, *, name: str, id=None, connection_string: str, create_temp_table: bool = False, kwargs: dict = {}) -> SqliteDatasource`
- `SqliteDatasource.add_table_asset(name: str, table_name: str = "", schema_name=None, batch_metadata: dict | None = None)`
- `SqliteDatasource.add_query_asset(name: str, query: str, batch_metadata: dict | None = None)`

SQLite table and query assets support the same whole-table and date-column batch definition helpers as generic SQL assets.

## Generic SQL and Warehouses

Use `add_sql` for SQLAlchemy-compatible engines when no specialized factory is needed; use a specialized factory when GX exposes one for the target warehouse.

```python
datasource = context.data_sources.add_sql(
    name="warehouse",
    connection_string="dialect+driver://user:pass@host:5432/database",
)
asset = datasource.add_table_asset(name="orders", table_name="orders")
```

Verified model signature:

- `SQLDatasource(name: str, connection_string: str, create_temp_table: bool = False, kwargs: dict = {})`
- `SQLDatasource.add_table_asset(name: str, table_name: str = "", schema_name=None, batch_metadata: dict | None = None)`
- `SQLDatasource.add_query_asset(name: str, query: str, batch_metadata: dict | None = None)`

For specialized factories such as `add_postgres`, `add_redshift`, `add_snowflake`, `add_bigquery`, `add_databricks_sql`, or `add_sql_server`, expect backend-specific connection arguments and dependencies. Read `optional-backends.md` before assuming those packages are present.

## Table Asset vs Query Asset

Use a table asset when GX should validate a real table or view and can partition by a date/datetime column. Use a query asset when the validated dataset is a `SELECT` statement, such as a join, filter, or projection.

Rules of thumb:

- `add_table_asset(name="orders", table_name="orders")` is better for stable production validation and table metadata.
- `add_query_asset(name="recent_orders", query="SELECT ...")` must begin with `SELECT`; invalid query strings are rejected.
- Do not pass arbitrary DDL/DML statements to query assets. They should read data, not mutate data.
- For schema handling, prefer configuring schema in the datasource connection when supported; `schema_name` on assets is retained for compatibility but may be deprecated for some paths.

## Asset Retrieval and Naming

After creation, retrieve assets from their datasource:

```python
datasource = context.data_sources.get("local_files")
asset = datasource.get_asset("orders_csv")
batch_definition = asset.get_batch_definition("monthly_orders")
```

Use stable lowercase or snake-case names in generated code. Batch definitions must be unique within an asset, datasource names must be unique in a context, and asset names must be unique within a datasource.
