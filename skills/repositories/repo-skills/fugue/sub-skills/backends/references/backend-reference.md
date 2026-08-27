# Backend reference

## Engine resolution order

`make_execution_engine(...)` resolves the engine in this order:

1. Use the current context engine if one is active.
2. Use the global execution engine if one has been set.
3. Infer the engine from `infer_by` if possible.
4. Fall back to the default registered engine.
5. Parse the provided engine object, string alias, tuple, or class.
6. Attach the SQL engine and merge the config.

`engine=None`, `engine=''`, and `engine='native'` all resolve to `NativeExecutionEngine` in the verified package.

## Backend matrix

| Backend | Install extra | Main imports | Alias / registration notes |
| --- | --- | --- | --- |
| Native | base install | `fugue.execution.native_execution_engine.NativeExecutionEngine` | Default engine when `engine` is empty or `native` |
| DuckDB | `fugue[duckdb]` or `fugue[sql]` | `fugue_duckdb.DuckExecutionEngine`, `fugue_duckdb.DuckDBEngine`, `fugue_duckdb.DuckDataFrame` | Registers `duck` and `duckdb`; optional `duckdask`, `duckdbdask`, `dd` if the extra Dask bridge is present |
| Dask | `fugue[dask]` | `fugue_dask.DaskExecutionEngine`, `fugue_dask.DaskDataFrame` | Registers `dask`; inference prefers Dask clients or Dask dataframes |
| Spark | `fugue[spark]` | `fugue_spark.SparkExecutionEngine`, `fugue_spark.SparkDataFrame` | Registers `spark`; also accepts `SparkSession` and `SparkConnectSession` when available |
| Ray | `fugue[ray]` | `fugue_ray.RayExecutionEngine`, `fugue_ray.RayDataFrame` | Registers `ray`; SQL engine remains separate from the map engine |
| Ibis | `fugue[ibis]` | `fugue_ibis.IbisExecutionEngine`, `fugue_ibis.IbisDataFrame` | Registers the Ibis integration for workflow and SQL-compatible access |
| Polars | `fugue[polars]` | `fugue_polars.PolarsDataFrame` | Dataframe conversion and integration support; SQL still commonly runs through DuckDB |
| Notebook | `fugue[notebook]` | `fugue_notebook.setup`, `fugue_notebook.NotebookSetup` | Jupyter/IPython extension support, not an execution engine |

## Engine and SQL-engine registration helpers

| Helper | Use |
| --- | --- |
| `register_execution_engine(name_or_type, func, on_dup='overwrite')` | Register a named engine alias or type-based engine parser |
| `register_sql_engine(name, func, on_dup='overwrite')` | Register a named SQL engine for an execution engine |
| `register_default_execution_engine(func, on_dup='overwrite')` | Change the default engine factory |
| `register_default_sql_engine(func, on_dup='overwrite')` | Change the default SQL engine factory |
| `infer_execution_engine(objs)` | Extend the inference heuristics for new dataframe/object types |

## Inference heuristics that are already wired

- Spark: `SparkSession`, `pyspark.sql.DataFrame`, `SparkDataFrame`, and Spark SQL namespace inputs
- Dask: `dask.distributed.Client`, `dask.dataframe.DataFrame`, and `DaskDataFrame`
- DuckDB: `duckdb.DuckDBPyConnection`, `duckdb.DuckDBPyRelation`, and `DuckDataFrame`
- Ray: `ray.data.Dataset` and `RayDataFrame`
- Ibis: `IbisDataFrame`-style integration through the package registration
- Polars: `PolarsDataFrame` integration for dataframe conversion and SQL-adjacent workflows

## Useful engine shorthand

- `engine_context("duckdb")` or `run("duckdb")` for DuckDB execution
- `engine_context(("dask", "duckdb"))` when the execution engine and SQL engine should differ
- `engine_context("native")` when you want the base in-process engine

## Read next

- `references/troubleshooting.md`
- `scripts/smoke_backends.py`
