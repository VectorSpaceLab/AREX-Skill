# Python Query API

## When to read

Read this when embedding Wren in Python rather than driving the CLI.

## Verified public signatures

```python
WrenEngine(
    manifest_str,
    data_source,
    connection_info,
    function_path=None,
    *,
    fallback=True,
    config=None,
)

engine.query(sql, limit=None, properties=None)  # -> pyarrow.Table
engine.dry_plan(sql, properties=None)           # -> str
engine.dry_run(sql, properties=None)            # -> None
engine.close()
```

`data_source` accepts a `DataSource` member or a matching string. The public
values include `athena`, `bigquery`, `canner`, `clickhouse`, `datafusion`,
`mssql`, `mysql`, `doris`, `oracle`, `postgres`, `redshift`, `snowflake`,
`trino`, `local_file`, `s3_file`, `minio_file`, `gcs_file`, `duckdb`, `spark`,
and `databricks`.

## Result and errors

`query()` returns a PyArrow table. Convert only as needed:

```python
rows = result.to_pylist()
frame = result.to_pandas()
```

Planning/execution failures are surfaced as Wren errors with a phase such as
SQL planning, execution, or dry-run. Preserve the planned SQL when debugging;
it is the concrete statement the connector would run.

## Policy behavior

A `WrenConfig` can enable strict mode or deny functions. Under policy checks,
references outside the modeled names and blocked functions should fail before
execution. Do not weaken the policy to make an exploratory query pass; correct
the model or get an explicit policy decision.

## Connection lifecycle

`WrenEngine` creates a connector lazily and reuses it during the engine lifetime.
Use a `with` block when a request owns the engine:

```python
with WrenEngine(manifest_str, "duckdb", connection_info) as engine:
    planned = engine.dry_plan(sql)
```

Use an agent framework toolkit instead of manually caching engine/connector
objects when the task is LangChain, LangGraph, or Pydantic AI integration.
