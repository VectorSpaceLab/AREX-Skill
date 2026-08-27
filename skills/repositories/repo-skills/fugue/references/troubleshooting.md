# Fugue troubleshooting

## Missing SQL dependencies

**Symptoms**
- `ImportError` for `fugue_sql_antlr`, `sqlglot`, or `jinja2`
- `fugue_sql` or `fugue_sql_flow` fails before parsing

**Likely cause**
- The `sql` extra is missing.

**Fix**
- Install `pip install "fugue[sql]"` or `pip install "fugue[all]"`.
- If you only need the parser speedup, add `cpp_sql_parser` when the platform supports it.

## Legacy `fugue_sql` wrapper warning

**Symptoms**
- A warning like `fsql and FugueSQLWorkflow now should be imported directly from fugue`

**Likely cause**
- The compatibility package `fugue_sql` was imported directly.

**Fix**
- Prefer `from fugue import fsql, FugueSQLWorkflow` or `import fugue.api as fa`.
- Keep `fugue_sql` only for legacy compatibility checks.

## Engine not recognized

**Symptoms**
- `FuguePluginsRegistrationError: Fugue execution engine is not recognized`
- `make_execution_engine(...)` cannot resolve a backend alias or object

**Likely cause**
- The backend package has not been imported or installed, or the alias is wrong.

**Fix**
- Install the matching extra and import the backend package so its registration side effects run.
- Use `engine_context(...)` or `make_execution_engine(...)` only after the backend package is available.

## `transform` and `out_transform` path limitations

**Symptoms**
- `FugueInterfacelessError` when passing a string path to `transform(...)` or `out_transform(...)`
- CSV or JSON paths are rejected in the one-shot helpers

**Likely cause**
- The express helpers only accept parquet paths as strings.

**Fix**
- Use a real dataframe object instead of a string path.
- Or use `FugueWorkflow.load(...)` / `save(...)` when you need other file formats.

## SQL workflow confusion

**Symptoms**
- `YIELD` does not behave as expected
- `fugue_sql(...)` only returns one dataframe

**Likely cause**
- `fugue_sql(...)` is the single-result helper; `fugue_sql_flow(...)` owns the full workflow.

**Fix**
- Use `fugue_sql_flow(...)` when you need multiple outputs or workflow-style statements.
- Use `raw_sql(...)` only for direct `SELECT` statements.

## Case and dialect mismatches

**Symptoms**
- A query parses on one backend but fails on another
- Case-sensitive identifiers behave differently than expected

**Likely cause**
- FugueSQL dialect differences or case handling defaults.

**Fix**
- Try `fsql_ignore_case=True` when the case policy is the problem.
- Keep backend-specific SQL features isolated and prefer backend-neutral Fugue extensions when possible.
