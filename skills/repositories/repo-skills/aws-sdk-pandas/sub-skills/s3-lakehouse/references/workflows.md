# S3 Lakehouse Workflows

## 1. Write a partitioned parquet dataset and read it back

1. Build a pandas DataFrame with the final column names and dtypes.
2. Choose a bucket path such as `s3://my-bucket/datasets/my_table/`.
3. Call `wr.s3.to_parquet(..., dataset=True, partition_cols=[...], mode="overwrite")`.
4. Read the result with `wr.s3.read_parquet(..., dataset=True)`.
5. Add `partition_filter` or `columns` when you only need a slice.
6. If the next step is Athena, route to `catalog-and-query` and register the metadata there.

Practical notes:
- `index=False` is usually the safest default for lakehouse datasets.
- `schema_evolution=True` is the normal choice when later writes may add columns.
- `chunked=True` returns an iterator, not one DataFrame.

## 2. Move or mirror files in S3

1. Use `upload` or `download` for local file transfers.
2. Use `copy_objects` for S3-to-S3 copies.
3. Use `list_objects` or `describe_objects` to confirm the target contents.
4. Use `delete_objects` when the workflow needs cleanup.
5. Use `wait_objects_exist` or `wait_objects_not_exist` when a later step depends on object readiness.

## 3. Work with Delta Lake on S3

1. Install `awswrangler[deltalake]`.
2. Write the frame with `wr.s3.to_deltalake(path=..., mode=..., partition_cols=...)`.
3. Read with `wr.s3.read_deltalake(path=...)`.
4. Use `without_files=True` or `version=` only when you need those specific recovery or inspection features.

## 4. Create and query S3 Vectors

1. Create the vector bucket with `wr.s3.create_vector_bucket(...)`.
2. Create the index with `wr.s3.create_vector_index(...)`.
3. Insert vectors with `wr.s3.put_vectors(...)` or `wr.s3.put_vectors_from_df(...)`.
4. Retrieve exact keys with `wr.s3.get_vectors(...)`.
5. Enumerate the index with `wr.s3.list_vectors(...)`.
6. Search by embedding with `wr.s3.query_vectors(query_vector=..., top_k=...)`.
7. Search by text with `wr.s3.query_vectors(query_text=..., bedrock_model_id=...)` when Bedrock embedding is available.

Common edge cases:
- If the user passes both `index` and `index_arn`, or both bucket name and bucket ARN, explain the targeting rule before retrying.
- Prefer `return_metadata=True` only when the downstream step really needs it.
- Use `chunked=True` for large listings when memory use matters.

## 5. Manage S3 Tables / Iceberg

1. Create or choose a table bucket.
2. Create a namespace.
3. Create the table with `wr.s3.create_table(...)`.
4. Read or write Iceberg datasets with `wr.s3.to_iceberg(...)` and `wr.s3.from_iceberg(...)`.
5. Clean up namespaces and tables explicitly when the workflow is done.

## How to choose the right path

- If the task is about files, parquet/CSV/JSON/ORC, or object movement, stay in this sub-skill.
- If the task is about Glue tables or Athena queries, move to `catalog-and-query`.
- If the task is about a relational database or Redshift, move to `sql-connectors`.
