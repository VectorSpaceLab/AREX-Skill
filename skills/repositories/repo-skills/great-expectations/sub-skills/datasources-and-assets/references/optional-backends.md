# Optional Backends and Dependencies

GX Core can define datasources for many backends, but a base install may not include every driver, storage SDK, Spark package, or warehouse client. Treat local pandas and SQLite as the safest baseline; add backend-specific dependencies only when the task requires them.

## Backend Families

| Backend family | Factory examples | Typical dependency surface |
| --- | --- | --- |
| In-memory pandas | `add_pandas` | `pandas` must be importable. |
| Local/network files via pandas | `add_pandas_filesystem` | `pandas`; format-specific packages such as Excel or Parquet engines. |
| SQLite | `add_sqlite` | SQLAlchemy-compatible SQLite support; usually available with Python plus SQLAlchemy. |
| Generic SQL | `add_sql` | `sqlalchemy` plus the dialect driver named in the connection string. |
| SQL warehouses | `add_postgres`, `add_redshift`, `add_snowflake`, `add_bigquery`, `add_databricks_sql`, `add_sql_server`, and similar factories | SQLAlchemy dialects, native clients, auth libraries, and network access. |
| Spark dataframe/files | `add_spark`, `add_spark_filesystem`, `add_spark_s3`, `add_spark_gcs`, `add_spark_abs`, `add_spark_dbfs` | `pyspark`, Java/Spark runtime, and storage connectors. |
| Cloud object storage with pandas | `add_pandas_s3`, `add_pandas_gcs`, `add_pandas_abs`, `add_pandas_dbfs` | Provider SDKs, filesystem adapters, and credentials. |
| Fabric/Power BI | `add_fabric`, `add_fabric_powerbi` | Microsoft Fabric/Power BI client dependencies and credentials. |

If a factory exists on `context.data_sources` but fails at import or connection time, the method is part of GX Core but the environment or credentials may be incomplete.

## SQLAlchemy and SQL Drivers

Generic SQL and many warehouse factories use SQLAlchemy underneath.

Checklist:

- Install `sqlalchemy` and a dialect driver for the connection string, such as a Postgres, Snowflake, BigQuery, SQL Server, or Databricks SQL driver.
- Use a read-only account or least-privilege credentials for validation.
- Prefer config-variable or environment substitution for secrets instead of hardcoding passwords.
- Verify the connection string format outside GX only with safe read-only probes.
- Use `create_temp_table=False` unless the backend and account allow temporary table creation and the validation metrics require it.

Connection strings are backend-specific. A valid SQLite string looks like `sqlite:///path/to/file.db`; networked SQL strings usually follow SQLAlchemy `dialect+driver://user:password@host:port/database` patterns.

## Spark Backends

Spark datasources require a working Spark runtime, not just GX Core.

Use Spark factories only when:

- `pyspark` imports successfully.
- The Spark session can read the target files/tables.
- Required Hadoop/cloud storage connectors are configured.
- The task expects Spark DataFrames or distributed execution.

For small local files, prefer pandas filesystem assets; they have fewer runtime assumptions and easier troubleshooting.

## Cloud Storage

Cloud filesystem factories discover files through provider-specific paths or prefixes and then read them through pandas or Spark.

Common requirements:

- S3: AWS credentials and object permissions; often `boto3`, `s3fs`, or Spark S3 connector dependencies.
- GCS: Google credentials and bucket permissions; often `gcsfs`, Google auth libraries, or Spark GCS connector dependencies.
- Azure Blob Storage: account/container credentials and storage SDKs; often `adlfs` or Spark Azure connectors.
- DBFS: Databricks runtime or API-compatible filesystem access.

Do not embed tokens, keys, service account JSON, or connection secrets in skill content, source code, or committed config. Use GX config variables, environment variables, secret managers, or backend-native credential discovery.

## Warehouses and Credentials

Warehouse datasources often need both Python packages and external service access. A failure can come from any layer:

1. Python import or SQLAlchemy dialect missing.
2. Connection string malformed or wrong driver prefix.
3. Network, DNS, firewall, proxy, or private endpoint unavailable.
4. Authentication credentials missing, expired, or not substituted.
5. User lacks read permissions on database, schema, table, or query result.
6. Temporary table creation or metadata introspection blocked by permissions.

Prefer `add_table_asset` for stable tables/views and `add_query_asset` only for read-only `SELECT` statements that need projection, joins, or filters.

## Format-Specific File Dependencies

Pandas filesystem assets pass many options through to pandas readers. Some formats need optional packages:

- Excel assets may require engines such as `openpyxl`, `xlrd`, or `pyxlsb` depending on file type.
- Parquet assets may require `pyarrow` or `fastparquet`.
- ORC, HDF, Feather, XML, SAS, SPSS, Stata, and HTML assets may require pandas optional dependencies.
- CSV assets are the safest smoke-test choice and can still need explicit `encoding`, `sep`, `quotechar`, `parse_dates`, or `dtype` options.

When a reader fails, first reproduce with the equivalent pandas read function and the same options, then move the fixed options into `add_*_asset(...)`.
