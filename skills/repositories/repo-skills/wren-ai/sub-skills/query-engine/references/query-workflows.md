# Governed Query Workflows

## Basic query

```bash
wren query \
  --sql 'SELECT customer_id, SUM(total) AS revenue FROM orders GROUP BY 1' \
  --limit 100 \
  --output table
```

`table`, `csv`, and `json` are supported output modes. SQL targets models,
views, and calculated fields defined by the project MDL.

## Plan before execution

Use a dry plan when a query contains joins, CTEs, calculated fields, a nontrivial
filter, or a costly database operation:

```bash
wren dry-plan --sql 'SELECT ...'
```

The result is target-dialect SQL after semantic expansion. Check that it uses
the intended models/columns and that join/CTE behavior matches the project
before using an execution command.

## Failure-layer diagnosis

| Observation | Likely layer | Next action |
| --- | --- | --- |
| `dry-plan` fails | model name, column, relationship, policy, MDL, or SQL planning | inspect context, correct one issue, rerun dry-plan |
| plan succeeds but query fails | credentials, connector, DB dialect, permissions, or query cost | inspect planned SQL and profile/connector |
| dry-run fails | live database validation | fix database-level error before a result query |

For model/column errors, use memory/schema context rather than guessing. For
ambiguous columns, qualify with the intended model name. For missing join paths,
confirm a relationship before inventing a manual join condition.

## Python embedding

```python
from wren.engine import WrenEngine
from wren.model.data_source import DataSource

engine = WrenEngine(
    manifest_str=base64_mdl_json,
    data_source=DataSource.postgres,
    connection_info={"host": "...", "database": "..."},
)
planned = engine.dry_plan('SELECT * FROM orders')
result = engine.query('SELECT * FROM orders', limit=100)
```

Wrap `WrenEngine` in a context manager when it owns a connector so `close()` is
called. An empty connection mapping is valid for transpile-only planning; it is
not enough for query or dry-run execution.

## Planning behavior to remember

Wren scopes the manifest to referenced models/views where possible, expands
semantic definitions through the Rust core, rewrites model SQL as CTEs, then
transpiles to the selected datasource dialect. The current core has a known
limitation resolving outer-column references inside correlated subqueries;
prefer a rewrite that avoids that form when the plan cannot resolve it.
