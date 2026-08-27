---
name: s3-lakehouse
description: "Guides awswrangler S3 object, file-format, dataset, S3 Tables,
  Delta Lake, and S3 Vectors workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# S3 Lakehouse

Use this sub-skill when the user is working with `wr.s3.*` workflows.

Typical triggers:
- "write a parquet dataset to S3"
- "read partitioned S3 data"
- "copy or delete S3 objects"
- "write Delta Lake data"
- "create an S3 Table / Iceberg table"
- "use S3 Vectors"
- "read Excel or CSV files from S3"

Read `references/api-reference.md` for the function map and optional extras.
Read `references/workflows.md` for common end-to-end patterns.
Read `references/troubleshooting.md` for S3 path, format, dataset, vector, and optional-dependency failures.
Use `../../scripts/check_runtime.py` from the root skill when you need to confirm importability or extras before a workflow.

## Include here

- S3 object lifecycle helpers such as list, upload, download, copy, delete, describe, and wait.
- Tabular file workflows for Parquet, CSV, JSON, ORC, FWF, and Excel.
- Dataset reads and writes with partitioning, bucketing, schema evolution, and catalog registration flags.
- Delta Lake helpers on S3.
- S3 Tables / Iceberg helpers.
- S3 Vectors bucket, index, ingest, list, get, delete, and query helpers.

## Exclude or route elsewhere

- Glue Catalog metadata management and Athena SQL execution go to `catalog-and-query`.
- Runtime, extras, and Ray/Modin mode questions go to `runtime-and-config`.
- Redshift, Data API, and direct database connector workflows go to `sql-connectors`.
- DynamoDB, Timestream, OpenSearch, Neptune, QuickSight, CloudWatch, EMR, STS, Secrets Manager, and Chime go to `service-integrations`.

## Common user outcomes

A future agent should be able to:
- move files between S3 locations,
- serialize and read pandas data as S3-backed datasets,
- register dataset metadata when the user also wants Glue/Athena visibility,
- manage Iceberg-style S3 Tables,
- and stage or query vectors without reopening the repository.

## Shared references and scripts

- `references/api-reference.md`
- `references/workflows.md`
- `references/troubleshooting.md`
- `scripts/smoke_s3_moto.py`
- `scripts/smoke_s3_vectors_mocked.py`
