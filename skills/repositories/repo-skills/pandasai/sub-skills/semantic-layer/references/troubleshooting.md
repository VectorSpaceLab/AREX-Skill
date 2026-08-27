# Semantic Layer Troubleshooting

## Invalid dataset path

**Symptom**: `Path must be in format 'organization/dataset'`, organization name
format error, or dataset path name format error.

**Cause**: Path is missing a slash, has uppercase letters, underscores, spaces,
or starts/ends with a hyphen.

**Fix**: Use lowercase hyphenated slugs such as `acme-corp/sales-data`.

## Dataset already exists

**Symptom**: `Dataset already exists at path: ...`.

**Cause**: A dataset directory and `schema.yaml` already exist.

**Fix**: Choose a new dataset path, intentionally remove the old dataset, or
load the existing dataset with `pai.load` instead of creating it again.

## `df must be a PandasAI DataFrame`

**Symptom**: `ValueError: df must be a PandasAI DataFrame`.

**Cause**: `pai.create` received a raw pandas DataFrame.

**Fix**:

```python
import pandasai as pai
raw = pai.read_csv("data.csv")       # already a PandasAI DataFrame
# or: raw = pai.DataFrame(pandas_df)
pai.create("org/dataset", df=raw)
```

## Source/view validation errors

| Symptom | Cause | Fix |
| --- | --- | --- |
| `Either 'source' or 'view' must be defined` | Schema lacks both source and view | Provide a local/remote `source` or set `view: true`. |
| `Only one of 'source' or 'view' can be defined` | Schema declares both | Remove one. Tables use `source`; views use `view: true`. |
| `For local source type ... 'path' must be defined` | `csv`/`parquet` source missing path | Add `path: data.parquet` or `path: data.csv`. |
| `For remote source type ... connection/table must be defined` | Remote source missing connection or table | Add both fields and install the matching connector extension. |

## View relation errors

**Symptoms**:

- `All columns in a view must be in the format '[dataset_name].[column_name]'`
- `All params 'from' and 'to' in the relations must be in the format ...`
- `No relations provided for the following tables ...`

**Fix**:

1. Use underscore table names and `table.column` format for all view columns.
2. Add at least one relation connecting each extra table.
3. Create or load dependency datasets before loading the view.
4. Check that dependency sources are compatible.

## `group_by` validation errors

**Symptom**: a column must either be in `group_by` or have an aggregation
expression, or an expression column cannot be in `group_by`.

**Fix**: Put every dimension/non-aggregated column in `group_by` and omit every
metric/aggregation expression column.

## Missing connector extension

**Symptom**: `Postgres connector not found`, `Mysql connector not found`, or
`Please install the pandasai_sql[...] library`.

**Cause**: The base `pandasai` package does not install database-specific
connectors.

**Fix**: Install only the needed connector, for example:

```bash
pip install "pandasai-sql[postgres]"
pip install "pandasai-sql[mysql]"
```

Then verify database host, port, user, password, and database name.

## Unsafe SQL query

**Symptom**: `MaliciousQueryError: The SQL query is deemed unsafe and will not
be executed.`

**Cause**: Query includes mutation/metadata statements or blocked comments.

**Fix**: Use SELECT-only queries. Do not ask PandasAI-generated code to run
INSERT, UPDATE, DELETE, DROP, CREATE, ALTER, SHOW, DESCRIBE, or commented SQL.

## Missing local files

**Symptom**: `Schema file not found`, `SQL execution failed`, or file-read
errors from DuckDB.

**Cause**: `datasets/<org>/<dataset>/schema.yaml` or the local source file is
not where the file manager expects it.

**Fix**: Run from the intended project root, check the `datasets/` layout, and
inspect `schema.source.path`. For `pai.create(df=...)`, expect `data.parquet` to
be created in the dataset directory.

## Excel sheet issues

**Symptom**: `ValueError` for nonexistent/empty sheet, or code treats a dict as a
DataFrame.

**Fix**: Pass a valid `sheet_name`; when using `sheet_name=None`, iterate through
the returned dict and choose which sheet(s) to create or chat with.
