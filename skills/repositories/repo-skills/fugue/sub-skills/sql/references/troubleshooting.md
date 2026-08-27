# SQL troubleshooting

## Parser dependency is missing

**Symptoms**
- `ImportError` for `fugue_sql_antlr`
- `SyntaxError` or parser errors before the workflow starts

**Likely cause**
- The `sql` extra is not installed.

**Fix**
- Install `pip install "fugue[sql]"` or `pip install "fugue[all]"`.
- If you need the faster parser variant, add `cpp_sql_parser` when the platform supports it.

## `fugue_sql(...)` and `YIELD` do not match

**Symptoms**
- A `YIELD` statement appears to be ignored or causes confusion
- Only one dataframe comes back from a query you expected to fan out

**Likely cause**
- `fugue_sql(...)` is the single-result helper, not the full workflow API.

**Fix**
- Move the query to `fugue_sql_flow(...)` or `FugueSQLWorkflow(...)`.

## Legacy wrapper warning

**Symptoms**
- A warning appears when importing `fugue_sql` as a package

**Likely cause**
- The compatibility wrapper is still present.

**Fix**
- Prefer `from fugue import fsql, FugueSQLWorkflow` or `import fugue.api as fa`.

## `raw_sql(...)` does less than expected

**Symptoms**
- A statement sequence fails unless it is a simple `SELECT`

**Likely cause**
- `raw_sql(...)` only supports direct `SELECT` statements on the engine.

**Fix**
- Use `fugue_sql_flow(...)` for full FugueSQL workflows.

## Dialect or case mismatch

**Symptoms**
- A query parses on one backend but not another
- Keywords or identifiers are interpreted with the wrong case sensitivity

**Likely cause**
- The parser defaults or SQL dialect do not match the backend.

**Fix**
- Try `fsql_ignore_case=True` first when case is the issue.
- Keep backend-specific SQL features isolated to the backend where they are known to work.

## Visual outputters are missing

**Symptoms**
- `viz:plot` or `sns:hist` is unrecognized

**Likely cause**
- The plotting dependencies are not installed.

**Fix**
- Install `matplotlib` and/or `seaborn` depending on the namespace outputter you want.
