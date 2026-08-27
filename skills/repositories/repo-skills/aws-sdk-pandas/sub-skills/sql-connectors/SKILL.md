---
name: sql-connectors
description: "Guides awswrangler Redshift, Data API, and direct MySQL,
  PostgreSQL, SQL Server, and Oracle connector workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# SQL Connectors

Use this sub-skill when the user is working with relational database connections or SQL copy/unload flows.

Typical triggers:
- "connect to Redshift"
- "read SQL from MySQL or PostgreSQL"
- "write a pandas DataFrame to SQL Server"
- "use the RDS Data API"
- "use Redshift COPY or UNLOAD"
- "open an Oracle connection"

Read `references/api-reference.md` for the connector families and their key methods.
Read `references/workflows.md` for choosing the right connection path and moving data in or out.
Read `references/troubleshooting.md` for missing driver, secret, timeout, SSL, and permission failures.
Use `../../scripts/check_runtime.py` from the root skill to confirm the required connector extras before attempting a live database workflow.

## Include here

- Redshift direct connector workflows, including `connect_temp`, `copy`, and `unload`.
- Redshift and RDS Data API workflows.
- MySQL, PostgreSQL, SQL Server, and Oracle direct connectors.
- `read_sql_query`, `read_sql_table`, and `to_sql` for the supported database families.

## Exclude or route elsewhere

- S3 file staging, dataset reads and writes, and Delta Lake go to `s3-lakehouse`.
- Glue Catalog, Athena, Data Quality, and Clean Rooms go to `catalog-and-query`.
- Runtime, extras, and Ray/Modin mode questions go to `runtime-and-config`.
- DynamoDB, Timestream, OpenSearch, Neptune, QuickSight, CloudWatch, EMR, STS, Secrets Manager, and Chime go to `service-integrations`.

## Common user outcomes

A future agent should be able to:
- choose the correct connector family,
- open a connection with the right secret, catalog, or database arguments,
- run parameterized SQL,
- write pandas data back to a table,
- and decide when Redshift COPY/UNLOAD or Data API is the better fit.

## Shared references

- `references/api-reference.md`
- `references/workflows.md`
- `references/troubleshooting.md`
