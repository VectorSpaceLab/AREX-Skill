# SQL Connectors Troubleshooting

## Purpose

Use this reference when a relational connector or Redshift load/export workflow fails.

## Common failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Missing optional dependency ...` for `redshift_connector`, `pymysql`, `pg8000`, `pyodbc`, or `oracledb` | The matching connector extra is not installed | Install the right extra before retrying the workflow. |
| `pyodbc` import errors or missing ODBC driver | The SQL Server native driver or unixODBC package is missing | Install the OS driver layer before retrying the connector. |
| Connection errors mentioning a secret, catalog entry, or database name | The Glue connection or secret ARN is wrong | Recheck the source of the connection string and the AWS secret / catalog metadata. |
| `NoCredentialsError` or permissions errors during Redshift COPY / UNLOAD | The AWS session cannot access S3, Redshift, or the staging path | Fix the IAM role / session permissions and confirm the S3 path. |
| SSL, timeout, or TCP keepalive errors during direct DB connections | The endpoint is slow, blocked, or using an incompatible TLS setup | Tune `ssl_context`, `timeout`, or TCP keepalive settings and verify the network path. |
| Upsert or overwrite behavior does not match expectations | The destination connector does not support the requested mode the way the caller expected | Check the module-specific `to_sql` contract and use the supported mode for that engine. |
| `chunksize` calls return iterators instead of DataFrames | The caller requested streaming output | Consume the iterator explicitly. |
| Redshift unload or copy writes files in the wrong place | The staging path or cleanup settings were wrong | Point the workflow at a dedicated S3 prefix and verify `keep_files`, `cleanpath`, and `path_suffix` behavior. |
| Oracle numeric or object columns round-trip incorrectly | The Oracle-specific type handling was not applied | Use the Oracle-specific helpers and explicit dtype settings. |

## Recovery order

1. Confirm the connector extra and native driver are installed.
2. Confirm the secret, connection name, database, and endpoint identifiers.
3. Confirm the staging path or unload destination when Redshift is involved.
4. Retry with a tiny query or single-row frame before scaling up.

## Related guidance

- `../../../references/runtime-overview.md` for extras.
- `../../../references/troubleshooting.md` for the common install/import and credential checks.
- `../../s3-lakehouse/references/troubleshooting.md` for S3 staging or dataset issues.
