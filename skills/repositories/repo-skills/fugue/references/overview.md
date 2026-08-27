# Fugue overview

Fugue is a unified interface for distributed computing. It lets you write dataframe and SQL workflows once and run them on pandas, Spark, Dask, Ray, DuckDB, Ibis, or Polars-backed execution paths.

## Package facts

- Package: `fugue`
- Version: `0.9.7`
- Python: `>=3.10`
- Core dependencies: `triad>=1.0.1`, `adagio>=0.2.6`, `pandas<3`
- Useful extras:
  - `sql` for FugueSQL support
  - `spark`, `dask`, `ray`, `duckdb`, `ibis`, `polars`, `notebook`
  - `all` for the broad runtime set
  - `cpp_sql_parser` for the faster SQL parser variant

## Top-level API map

### Workflow and dataframe helpers

- `transform(...)` and `out_transform(...)` for one-shot dataframe transforms
- `load(...)` and `save(...)` for file IO
- `select(...)`, `join(...)`, `union(...)`, `intersect(...)`, `subtract(...)`
- `aggregate(...)`, `assign(...)`, `sample(...)`, `dropna(...)`, `fillna(...)`
- `broadcast(...)`, `persist(...)`, `repartition(...)`, `run_engine_function(...)`
- `as_fugue_df(...)`, `as_fugue_dataset(...)`, `as_pandas(...)`, `as_array(...)`, `as_dicts(...)`, `as_arrow(...)`
- `get_schema(...)`, `get_column_names(...)`, `normalize_column_names(...)`, `alter_columns(...)`, `drop_columns(...)`, `select_columns(...)`

### SQL entry points

- `fugue_sql(...)` for the simple single-result FugueSQL path
- `fugue_sql_flow(...)` for full multi-output FugueSQL workflows
- `fsql(...)` is the convenience alias exported by `fugue` for `fugue_sql_flow(...)`
- `raw_sql(...)` for direct `SELECT` statements on the execution engine

### Engine selection and registration

- `engine_context(...)`
- `make_execution_engine(...)`
- `register_execution_engine(...)`
- `register_sql_engine(...)`
- `register_default_execution_engine(...)`
- `register_default_sql_engine(...)`
- `infer_execution_engine(...)`

## Verified signatures worth remembering

| API | Signature shape | Use |
| --- | --- | --- |
| `transform` | `transform(df, using, schema=None, params=None, partition=None, callback=None, ignore_errors=None, persist=False, as_local=False, save_path=None, checkpoint=False, engine=None, engine_conf=None, as_fugue=False)` | One-shot dataframe transforms |
| `out_transform` | `out_transform(df, using, params=None, partition=None, callback=None, ignore_errors=None, engine=None, engine_conf=None)` | One-shot side-effect transforms |
| `fugue_sql` | `fugue_sql(query, *args, fsql_ignore_case=None, fsql_dialect=None, engine=None, engine_conf=None, as_fugue=False, as_local=False, **kwargs)` | Single-result FugueSQL |
| `fugue_sql_flow` | `fugue_sql_flow(query, *args, fsql_ignore_case=None, fsql_dialect=None, **kwargs)` | Full FugueSQL DAG |
| `make_execution_engine` | `make_execution_engine(engine=None, conf=None, infer_by=None, **kwargs)` | Resolve engine aliases, instances, and tuples |
| `engine_context` | `engine_context(engine=None, engine_conf=None, infer_by=None)` | Temporary default engine context |

## Installed plugin entry points

The package exposes these `fugue.plugins` entry points when the corresponding backend packages are installed: `ibis`, `duckdb`, `spark`, `dask`, `ray`, and `polars`.

## Where to go next

- Read `sub-skills/workflow/references/workflow-reference.md` for DAG and DataFrame details.
- Read `sub-skills/sql/references/sql-reference.md` for FugueSQL syntax and workflow translation.
- Read `sub-skills/backends/references/backend-reference.md` for backend selection and registration.
- Read `sub-skills/notebook/references/notebook-reference.md` for notebook magics and setup.
