# Service Integrations API Reference

## Purpose

This reference groups the smaller AWS service wrappers by the job they do rather than by source-file layout.

## DynamoDB

- `put_items`, `put_df`, `put_csv`, `put_json`
- `read_items`, `read_partiql_query`
- `delete_items`
- `get_table`
- `execute_statement`

Use the DynamoDB helpers when the user wants batch item movement or a PartiQL-style read path.

## Timestream

- `create_database`, `delete_database`
- `create_table`, `delete_table`
- `list_databases`, `list_tables`
- `write`, `query`
- `batch_load`, `batch_load_from_files`, `wait_batch_load_task`
- `unload`, `unload_to_files`

Timestream writes need a database, table, time column, measure column(s), and the right dimension columns.

## OpenSearch

- `connect`
- `create_collection`
- `create_index`, `delete_index`
- `index_df`, `index_documents`, `index_json`, `index_csv`
- `search`, `search_by_sql`

Important distinction:
- `connect` creates or wraps an OpenSearch client.
- `create_collection` is for serverless or managed collection creation.
- indexing helpers take a client and then push data in the chosen format.

## Neptune

- `connect`
- `execute_gremlin`, `execute_opencypher`, `execute_sparql`
- `to_property_graph`, `to_rdf_graph`
- `bulk_load`, `bulk_load_from_files`
- `flatten_nested_df`
- `GremlinParser`
- `BulkLoadParserConfiguration`

Neptune bulk-load workflows often need flattened data before the graph export step.
The Gremlin and SPARQL paths use the `gremlin` and `sparql` extras, and openCypher uses the `opencypher` extra.

## QuickSight

- Resource lookup helpers: `get_dashboard_id(s)`, `get_data_source_id(s)`, `get_dataset_id(s)`, `get_template_id(s)`
- List helpers: `list_dashboards`, `list_data_sources`, `list_datasets`, `list_templates`, `list_ingestions`, `list_groups`, `list_users`, and the other `list_*` helpers in the module
- Describe/delete helpers: `describe_dashboard`, `describe_data_source`, `describe_dataset`, `describe_ingestion`, `delete_dashboard`, `delete_data_source`, `delete_dataset`, `delete_template`
- Creation helpers: `create_athena_data_source`, `create_athena_dataset`, `create_ingestion`, `cancel_ingestion`

QuickSight workflows usually depend on an Athena data source or dataset and the right AWS account context.

## CloudWatch Logs

- `start_query`, `wait_query`, `run_query`, `read_logs`
- `describe_log_streams`, `filter_log_events`

These helpers are the natural choice for log-query workflows that need a DataFrame result.

## EMR

- `create_cluster`
- `build_step`, `build_spark_step`
- `submit_step`, `submit_steps`, `submit_spark_step`, `submit_ecr_credentials_refresh`
- `get_cluster_state`, `get_step_state`
- `terminate_cluster`

## EMR Serverless

- `create_application`
- `run_job`
- `wait_job`

## STS

- `get_account_id`
- `get_current_identity_arn`
- `get_current_identity_name`

## Secrets Manager

- `get_secret`
- `get_secret_json`

## Chime

- `post_message`

## Validation clues

- DynamoDB can often be validated with moto-backed tests.
- STS and Secrets Manager can often be validated with moto or a mocked boto3 session.
- OpenSearch, Neptune, QuickSight, CloudWatch, EMR, and EMR Serverless usually need real AWS services or a very carefully controlled mock environment.
- `post_message` performs input validation before any webhook call, so it is useful as a pure safety check.
