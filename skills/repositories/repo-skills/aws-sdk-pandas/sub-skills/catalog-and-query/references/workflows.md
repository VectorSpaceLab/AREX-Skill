# Catalog and Query Workflows

## 1. Register a dataset in Glue Catalog

1. Create or choose the database with `wr.catalog.create_database(...)`.
2. If the dataset already exists in S3, point `create_parquet_table` / `create_csv_table` / `create_json_table` / `create_orc_table` at the dataset root.
3. Pass the column types, partition types, and any table comments or parameters.
4. Use `add_*_partitions` when the files already exist and you need explicit partition registration.
5. Inspect the result with `get_partitions`, `get_tables`, or `table`.
6. Route back to `s3-lakehouse` if the task is actually about writing the files rather than cataloging them.

## 2. Run an Athena query against a registered table

1. Make sure the database, table, output bucket, and workgroup exist.
2. Use `create_athena_bucket()` when the workflow wants the default output location.
3. Call `wr.athena.read_sql_query(sql=..., database=..., workgroup=...)`.
4. Choose `ctas_approach=True` for table-shaped results or `unload_approach=True` when the user prefers UNLOAD semantics.
5. Use `chunksize` when the result set is large or should be streamed.
6. Use `params` and `paramstyle` for parameterized SQL rather than string concatenation.
7. Inspect query metadata with `get_query_execution` or `get_query_results` when a query fails or is cancelled.

## 3. Materialize an Athena result as a new table

1. Use `create_ctas_table` when the caller wants a temporary or materialized table from SQL text.
2. Supply `database`, `ctas_database`, and `ctas_table` explicitly if the default names would be ambiguous.
3. Add `partitioning_info`, `bucketing_info`, or `storage_format` only when the downstream reader needs them.
4. If the user wants an answer only, prefer `read_sql_query` instead.

## 4. Manage Athena prepared statements and table descriptions

1. Create the statement with `create_prepared_statement`.
2. List it with `list_prepared_statements`.
3. Delete it with `delete_prepared_statement` when it is no longer needed.
4. Use `describe_table`, `show_create_table`, or `generate_create_query` for metadata inspection or debugging.

## 5. Work with data quality rulesets

1. Start from a rules DataFrame or a DQDL string.
2. Create a ruleset with `create_ruleset` or `create_recommendation_ruleset`.
3. Evaluate the ruleset with `evaluate_ruleset`.
4. Inspect the stored definition with `get_ruleset`.
5. Update the ruleset with `update_ruleset` when the rule set changes.

## 6. Query AWS Clean Rooms data

1. Ensure the membership, analysis template, output bucket, and output prefix are all known.
2. Call `wr.cleanrooms.read_sql_query(...)` with either a SQL string or an analysis template ARN, depending on the workflow.
3. Use `wait_query` when the user needs the final protected-query status.
4. Keep `keep_files` aligned with whether the temporary query output should be retained.

## Routing reminders

- If the problem is really S3 file layout, go back to `s3-lakehouse`.
- If the problem is a database driver, DSN, or connection string, go to `sql-connectors`.
- If the problem is configuration, extras, or Ray mode, go to `runtime-and-config`.
