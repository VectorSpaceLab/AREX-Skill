# `wren_core` Python Binding

## When to read

Read this for lower-level semantic-core use, local physical file registration,
or a PyO3-binding change.

## Verified construction and methods

```python
from wren_core import SessionContext

ctx = SessionContext(
    mdl_base64=None,
    remote_functions_path=None,
    properties=None,
    data_source=None,
)
```

The binding exposes `SessionContext` plus manifest helpers such as
`to_json_base64`, `to_manifest`, compatibility/migration helpers, RLAC
validation, and `cube_query_to_sql`.

Key context methods include:

```python
ctx.transform_sql(sql)
ctx.query(sql)                 # Arrow IPC bytes
ctx.dry_run(sql)
ctx.register_csv(name, path)
ctx.register_parquet(name, path)
ctx.load_mdl(mdl_base64)
ctx.list_tables()
ctx.get_available_functions()
ctx.pushdown_limit(sql, limit)
```

## Two-phase local file workflow

Register physical files before loading an MDL that refers to them:

```python
ctx = SessionContext()
ctx.register_parquet("orders", "orders.parquet")
ctx.load_mdl(base64_mdl_json)
result_ipc = ctx.query("SELECT * FROM orders")
```

Registered tables live in the default DataFusion catalog/schema. An MDL must
reference compatible physical names and columns. New top-level catalogs must
exist before MDL construction/transforms; registration after construction is
safe only for the existing shared catalog behavior.

## Concurrency rule

Calls on one context are serialized because MDL application and query paths
share catalog state. Do not call `load_mdl` concurrently with other operations
on the same context. Use separate contexts for independent workloads.

## Local-build note

The published binding uses a stable Python ABI. For repository changes, build
the local wheel with the module's Maturin/`just` workflow instead of assuming a
running Python environment uses local Rust source automatically.
