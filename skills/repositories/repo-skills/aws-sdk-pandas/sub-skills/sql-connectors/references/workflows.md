# SQL Connectors Workflows

## 1. Choose the connector family

1. If the user has a Redshift cluster or workgroup and S3 staging, prefer the Redshift connector.
2. If the user has an RDS or Redshift Data API setup, use `data_api.rds` or `data_api.redshift`.
3. If the user has a direct database endpoint plus a Python driver, use the matching MySQL, PostgreSQL, SQL Server, or Oracle module.
4. If the task is really about S3 file staging or CTAS/UNLOAD output files, route to `s3-lakehouse` or `catalog-and-query` as appropriate.

## 2. Read from a database

1. Open the connection with the smallest set of credentials the workflow needs.
2. Use `read_sql_query` for custom SQL or `read_sql_table` for a full-table extract.
3. Add `chunksize` when the result set is large.
4. Pass `params` instead of interpolating user values into SQL strings.
5. Check `dtype_backend` if the caller needs `numpy_nullable` or `pyarrow` semantics.

## 3. Write a DataFrame back to the database

1. Start with a DataFrame whose columns already match the destination schema as closely as possible.
2. Use `to_sql` on the direct connector family.
3. Set `index=False` unless the database table really needs the index values.
4. Use `mode`, `overwrite_method`, `primary_keys`, `upsert_conflict_columns`, or `add_new_columns` only when the target engine supports them.
5. Route back to `s3-lakehouse` if the workflow should stage files first.

## 4. Use Redshift COPY / UNLOAD

1. Choose `copy` or `copy_from_files` when loading from S3 into Redshift.
2. Choose `unload` or `unload_to_files` when exporting Redshift results back to S3.
3. Keep the S3 staging prefix isolated and easy to clean up.
4. Pass the AWS role or temporary credentials required by the cluster.
5. Use the S3 lakehouse sub-skill when you need help shaping the files before the database step.

## 5. Use Redshift or RDS Data API

1. Call `connect` from the `data_api` family with the cluster / resource ARN, database, and secret ARN.
2. Call `read_sql_query` after the connection is open.
3. Use these paths when the workflow should avoid a direct socket connection.
4. Expect AWS permissions and service configuration, not a local driver, to be the main blocker.

## 6. Open a temporary Redshift connection

1. Use `connect_temp` when the workflow needs a temporary cluster/session connection.
2. Provide the cluster identifier, user, and database details.
3. Keep the duration and SSL / timeout parameters explicit when the caller is debugging connection instability.

## 7. Route by destination engine

- MySQL: `awswrangler[mysql]` and `pymysql`.
- PostgreSQL: `awswrangler[postgres]` and `pg8000`.
- SQL Server: `awswrangler[sqlserver]` and `pyodbc`.
- Oracle: `awswrangler[oracle]` and `oracledb`.

If the request is about database access but the engine is not one of those four, switch back to the caller for clarification instead of guessing.
