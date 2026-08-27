# Catalog and Query API Reference

## Purpose

This reference groups the public catalog, Athena, Data Quality, and Clean Rooms APIs by what a future agent needs to do with them.

## Glue Catalog helpers

### Create and delete

- `create_database`, `delete_database`
- `create_parquet_table`, `create_csv_table`, `create_json_table`, `create_orc_table`
- `delete_table_if_exists`, `delete_all_partitions`, `delete_partitions`
- `add_parquet_partitions`, `add_csv_partitions`, `add_json_partitions`, `add_orc_partitions`

### Inspect and search

- `does_table_exist`, `get_tables`, `get_databases`, `tables`, `databases`, `table`
- `get_partitions`, `get_parquet_partitions`, `get_csv_partitions`
- `get_table_location`, `get_table_description`, `get_table_parameters`, `get_table_types`
- `get_table_versions`, `get_table_number_of_versions`
- `get_columns_comments`, `get_columns_parameters`
- `search_tables`, `get_connection`

### DataFrame/schema helpers

- `sanitize_column_name`, `sanitize_table_name`
- `sanitize_dataframe_columns_names`, `rename_duplicated_columns`, `drop_duplicated_columns`
- `extract_athena_types`, `overwrite_table_parameters`, `upsert_table_parameters`

These helpers are the usual path when a user wants to transform a pandas frame into Glue-compatible table metadata.

## Athena helpers

### Query execution and results

- `read_sql_query`, `read_sql_table`
- `start_query_execution`, `stop_query_execution`, `wait_query`
- `get_query_execution`, `get_query_executions`, `get_query_results`, `list_query_executions`
- `get_query_columns_types`
- `create_athena_bucket`

### Table and SQL utilities

- `describe_table`, `show_create_table`, `generate_create_query`, `repair_table`
- `create_ctas_table`, `unload`
- `create_prepared_statement`, `list_prepared_statements`, `delete_prepared_statement`

### Spark-on-Athena and Iceberg helpers

- `create_spark_session`, `run_spark_calculation`
- `to_iceberg`, `delete_from_iceberg_table`

### Common query settings

Key parameters to remember across the query surface:
- `database`
- `workgroup`
- `s3_output`
- `ctas_approach`
- `unload_approach`
- `chunksize`
- `result_reuse_configuration`
- `params` and `paramstyle`
- `athena_query_wait_polling_delay`
- `dtype_backend`

## Data Quality helpers

- `create_recommendation_ruleset`
- `create_ruleset`
- `evaluate_ruleset`
- `get_ruleset`
- `update_ruleset`

These helpers create and manage Glue Data Quality rulesets from either a DataFrame of rules or a DQDL string.

## Clean Rooms helpers

- `read_sql_query`
- `wait_query`

Clean Rooms queries are execution- and membership-driven; the output bucket and prefix are part of the API contract.

## Validation clues

- Glue catalog helpers can usually be validated locally with moto-backed tests.
- Athena, Data Quality, and Clean Rooms are usually AWS-backed and require live credentials plus the expected IAM permissions and S3 locations.
- `read_sql_query(..., chunksize=True)` returns an iterator, not one DataFrame.
- `read_sql_query` supports CTAS and UNLOAD-style result handling; choose the mode that matches the user's output shape and permissions.
