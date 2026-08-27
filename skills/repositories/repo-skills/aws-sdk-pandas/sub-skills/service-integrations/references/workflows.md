# Service Integrations Workflows

## 1. DynamoDB item round-trip

1. Create the DynamoDB table out of band or in a moto-backed smoke environment.
2. Use `put_items` for plain Python dictionaries or `put_df` / `put_csv` / `put_json` when the source is tabular or file-based.
3. Read the rows back with `read_items`.
4. Use `delete_items` to clean up the inserted data.
5. Use `read_partiql_query` or `execute_statement` when the caller wants PartiQL instead of a key-based read.

## 2. Timestream ingest and query

1. Create the database and table.
2. Choose `write` for direct DataFrame ingest.
3. Choose `batch_load` or `batch_load_from_files` when the workflow stages files first.
4. Use `query` for SQL-style reads.
5. Use `unload` or `unload_to_files` when the data should come back out to S3.
6. Keep the time column, measure column, and dimensions aligned before calling the writer.

## 3. OpenSearch index and search

1. Create or connect to the OpenSearch client.
2. Create the target index when it does not already exist.
3. Index data with `index_df`, `index_documents`, `index_json`, or `index_csv` depending on the input shape.
4. Read it back with `search` or `search_by_sql`.
5. Use `index_documents` when the caller needs fine-grained control over IDs, chunk size, or retry settings.

## 4. Neptune graph operations

1. Create a Neptune client with `connect`.
2. Flatten nested tabular data before a graph export if the source is not already graph-shaped.
3. Use `to_property_graph` or `to_rdf_graph` for graph loading.
4. Use `bulk_load` or `bulk_load_from_files` when the workflow wants to stage data and ask Neptune to load it asynchronously.
5. Use `execute_gremlin`, `execute_opencypher`, or `execute_sparql` when the caller wants to query the graph directly.

## 5. QuickSight resource setup

1. Identify the AWS account, namespace, and source Athena dataset or data source.
2. Create the Athena data source or dataset.
3. List or describe the created resources to confirm the IDs.
4. Trigger an ingestion when the dataset is ready.
5. Clean up dashboards, data sources, datasets, or templates when the workflow is temporary.

## 6. CloudWatch log analysis

1. Start with `start_query` or `run_query` for a quick log search.
2. Use `wait_query` when the caller needs to poll for completion.
3. Use `read_logs` when a DataFrame result is more convenient than raw rows.
4. Use `describe_log_streams` and `filter_log_events` for lower-level stream inspection.

## 7. EMR and EMR Serverless orchestration

1. Create the EMR cluster or EMR Serverless application.
2. Build a step or job payload with the helper that matches the execution model.
3. Submit the step or job and wait for the state transition.
4. Terminate the cluster or stop the application when the workflow is done.
5. Treat subnet, role, logging, and security-group setup as first-class prerequisites.

## 8. STS, Secrets Manager, and Chime

1. Use STS helpers to confirm the current account or identity before a live workflow.
2. Use Secrets Manager helpers to fetch structured JSON secrets.
3. Use Chime only when the user explicitly has a webhook URL and wants a message posted.
4. Keep Chime input validation separate from the live notification path so the failure is obvious.

## Routing reminders

- If the workflow is about graph storage or search but not AWS, this is the wrong skill.
- If the workflow is about Athena tables or query output, route to `catalog-and-query`.
- If the workflow is about S3 files staging a downstream load, route to `s3-lakehouse`.
