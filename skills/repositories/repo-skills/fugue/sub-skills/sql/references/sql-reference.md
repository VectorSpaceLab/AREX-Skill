# SQL reference

## Helper entry points

The package also exports `fsql` as the convenience alias for `fugue_sql_flow(...)`.

| API | Signature shape | When to use |
| --- | --- | --- |
| `fugue_sql` | `fugue_sql(query, *args, fsql_ignore_case=None, fsql_dialect=None, engine=None, engine_conf=None, as_fugue=False, as_local=False, **kwargs)` | Run a single-result FugueSQL string |
| `fugue_sql_flow` | `fugue_sql_flow(query, *args, fsql_ignore_case=None, fsql_dialect=None, **kwargs)` | Build a full FugueSQL workflow with multiple outputs |
| `raw_sql` | `raw_sql(*statements, engine=None, engine_conf=None, as_fugue=False, as_local=False)` | Run direct `SELECT` statements on an execution engine |
| `FugueSQLWorkflow` | `FugueSQLWorkflow(compile_conf=None)` | Stateful SQL workflow builder |

## The most important semantic split

- Use `fugue_sql(...)` when you want one final dataframe back.
- Use `fugue_sql_flow(...)` or `FugueSQLWorkflow(...)` when you need `YIELD`, multiple outputs, or a workflow you can keep adding SQL blocks to.
- Do **not** use `YIELD` with `fugue_sql(...)`.

## Common SQL shapes

### Simple helper query

```python
import pandas as pd
import fugue.api as fa

pdf = pd.DataFrame({"a": [0, 1], "b": [2, 3]})
res = fa.fugue_sql(
    "SELECT a, b FROM pdf WHERE a < {{limit}}",
    pdf=pdf,
    limit=1,
    as_fugue=True,
)
print(res.as_array())
```

### Full FugueSQL workflow

```python
import fugue.api as fa

flow = fa.fugue_sql_flow(
    """
    CREATE [[0], [1]] SCHEMA a:int
    YIELD DATAFRAME AS result
    """
)
res = flow.run("native")
print(res["result"].as_array())
```

### Direct SQL on an engine

```python
import pandas as pd
import fugue.api as fa

pdf = pd.DataFrame({"a": [0, 1]})
res = fa.raw_sql("SELECT * FROM", pdf, "WHERE a < 1", as_fugue=True)
print(res.as_array())
```

## Query constructs to remember

- `CREATE [[...]] SCHEMA ...` for inline data
- `SELECT ... FROM ...` for regular selection
- `TRANSFORM USING <callable> SCHEMA ...` to call Python code from FugueSQL
- `OUTPUT USING <outputter>` for side-effect outputters
- `PRINT` to display a dataframe in the workflow
- `YIELD DATAFRAME AS name` or `YIELD FILE AS name` to expose outputs from a full workflow
- `PREPARTITION BY`, `PRESORT`, and `ROWCOUNT` controls when the workflow needs explicit partitioning

## Variable and dataframe lookup

- FugueSQL can resolve external values from explicit keyword arguments.
- It can also infer dataframes from caller variables, but explicit kwargs are clearer and easier to review.
- `FugueSQLWorkflow.sql_vars` stores SQL variables that were created inside the workflow.
- The `__call__` API lets you append more SQL blocks to the same workflow object.

## Case and dialect knobs

- `fsql_ignore_case=True` makes the parser treat keywords case-insensitively.
- `fsql_dialect` and the workflow config control the dialect path when backend-specific syntax matters.
- Different SQL engines still have dialect differences, so keep backend-specific SQL isolated when possible.

## Namespace outputters

The repo ships namespace outputters such as `viz:plot` and `sns:hist` when the plotting dependencies are installed. They are convenient for quick visual checks inside FugueSQL, but they still depend on the matching plotting stack.

## Read next

- `references/troubleshooting.md`
- `scripts/sql_smoke.py`
