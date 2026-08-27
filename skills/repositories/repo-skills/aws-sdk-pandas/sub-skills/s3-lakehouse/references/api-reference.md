# S3 Lakehouse API Reference

## Purpose

This reference groups the public `wr.s3` surface by workflow family so future agents can answer common questions without reopening the repository.

## Object and path helpers

- `list_buckets`, `list_objects`, `list_directories`, `does_object_exist`
- `upload`, `download`, `copy_objects`, `merge_datasets`, `delete_objects`
- `describe_objects`, `size_objects`, `get_bucket_region`
- `wait_objects_exist`, `wait_objects_not_exist`

These helpers are the first stop for moving data around S3 or checking whether a location is ready for a later read/write step.

## Tabular file workflows

### Parquet

- Write: `to_parquet(df, path, dataset=..., partition_cols=..., mode=..., catalog_id=..., database=..., table=...)`
- Read: `read_parquet(path, dataset=..., partition_filter=..., columns=..., chunked=..., dtype_backend=...)`
- Metadata: `read_parquet_metadata`, `read_parquet_table`, `store_parquet_metadata`

Common use cases:
- append or overwrite partitioned datasets,
- read only selected partitions or columns,
- register S3 Parquet datasets for later Athena/Glue use.

### CSV and JSON

- Write: `to_csv`, `to_json`
- Read: `read_csv`, `read_json`

These APIs follow the same dataset, partitioning, and `use_threads` patterns as Parquet.

### ORC and Excel

- Write: `to_orc`, `to_excel`
- Read: `read_orc`, `read_orc_metadata`, `read_orc_table`, `read_excel`

Excel helpers rely on `openpyxl`.

### Text and fixed-width

- `read_fwf`
- `select_query` for S3 Select style reads

## Delta Lake

- `to_deltalake(df, path, ...)`
- `to_deltalake_streaming(...)`
- `read_deltalake(path, ...)`

The Delta Lake helpers require the `deltalake` extra.

## S3 Tables / Iceberg

- Table bucket and namespace management: `create_table_bucket`, `delete_table_bucket`, `create_namespace`, `delete_namespace`
- Table management: `create_table`, `delete_table`
- Iceberg conversions: `to_iceberg`, `from_iceberg`

The Iceberg path requires the `pyiceberg` extra.

## S3 Vectors

- Bucket and index management: `create_vector_bucket`, `delete_vector_bucket`, `list_vector_buckets`, `get_vector_bucket`, `create_vector_index`, `delete_vector_index`, `list_vector_indexes`, `get_vector_index`
- Data access: `put_vectors`, `put_vectors_from_df`, `get_vectors`, `delete_vectors`, `list_vectors`, `query_vectors`

Important rules:
- `query_vectors` accepts exactly one of `query_vector` or `query_text`.
- `query_text` requires `bedrock_model_id`.
- Vector payloads must be one-dimensional and finite.
- Targeting by name uses `index` plus exactly one of `vector_bucket` or `vector_bucket_arn`; targeting by ARN uses `index_arn` alone.

## Validation clues

- `to_parquet` / `read_parquet` and `to_csv` / `read_csv` are the easiest round-trip checks when moto-backed S3 is available.
- S3 Vectors are best validated with a mocked client because moto does not currently support the service.
- The public functions return pandas DataFrames or iterators of DataFrames; chunked reads should be documented as iterators, not lists.
