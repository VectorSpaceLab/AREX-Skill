# SQL Connectors API Reference

## Purpose

This reference groups the Redshift, Data API, and direct database connectors so future agents can answer connection and write-back questions without reopening the repository.

## Redshift connector

- `connect`
- `connect_temp`
- `read_sql_query`
- `read_sql_table`
- `to_sql`
- `copy`
- `copy_from_files`
- `unload`
- `unload_to_files`

Key parameters to remember:
- `connection` or `secret_id` for regular Redshift connections.
- `cluster_identifier` and `user` for temporary connections.
- `iam_role` or explicit AWS credentials for COPY / UNLOAD flows.
- `overwrite_method`, `diststyle`, `sortstyle`, `sortkey`, `primary_keys`, `precombine_key`, and `add_new_columns` for load behavior.
- `chunked` on reads and `keep_files` on staging-heavy writes.

## Redshift and RDS Data API

### Redshift Data API

- `data_api.redshift.connect`
- `data_api.redshift.read_sql_query`

### RDS Data API

- `data_api.rds.connect`
- `data_api.rds.read_sql_query`
- `data_api.rds.to_sql`

These wrappers keep the database access on AWS-managed APIs instead of a direct socket connection.

## Direct database connectors

### MySQL

- `connect`
- `read_sql_query`
- `read_sql_table`
- `to_sql`
- `identifier`

### PostgreSQL

- `connect`
- `read_sql_query`
- `read_sql_table`
- `to_sql`
- `identifier`

### SQL Server

- `connect`
- `read_sql_query`
- `read_sql_table`
- `to_sql`
- `identifier`

### Oracle

- `connect`
- `read_sql_query`
- `read_sql_table`
- `to_sql`
- `identifier`
- `detect_oracle_decimal_datatype`
- `handle_oracle_objects`

## Capability notes

- `read_sql_query` and `read_sql_table` usually return DataFrames or iterators when `chunksize` is set.
- `to_sql` is the common write-back path for the direct connectors.
- PostgreSQL and SQL Server support upsert-oriented modes; Oracle and Redshift have their own load and overwrite controls.
- Redshift COPY/UNLOAD work best when the staging path is already covered by `s3-lakehouse`.
- The Data API paths need the appropriate AWS-managed database service, secret, and permissions rather than a local socket.
