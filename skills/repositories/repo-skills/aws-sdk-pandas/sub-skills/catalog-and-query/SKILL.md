---
name: catalog-and-query
description: "Guides awswrangler Glue Catalog, Athena, Data Quality, and AWS
  Clean Rooms workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Catalog and Query

Use this sub-skill when the user is working with `wr.catalog.*`, `wr.athena.*`, `wr.data_quality.*`, or `wr.cleanrooms.*` workflows.

Typical triggers:
- "create a Glue table"
- "register a parquet dataset for Athena"
- "run an Athena query"
- "use CTAS or UNLOAD"
- "manage Athena prepared statements"
- "create or evaluate a data quality ruleset"
- "read from AWS Clean Rooms"

Read `references/api-reference.md` for the function map and public signatures.
Read `references/workflows.md` for the common end-to-end query and metadata flows.
Read `references/troubleshooting.md` for Athena, Glue, Data Quality, and Clean Rooms failure modes.
Use `../../scripts/check_runtime.py` from the root skill when you need to check importability, extras, or engine mode before a workflow.

## Include here

- Glue Catalog database, table, partition, and schema helpers.
- Athena query execution, result handling, CTAS, UNLOAD, prepared statements, table inspection, and Spark-on-Athena helpers.
- Glue Data Quality ruleset creation, update, retrieval, recommendation, and evaluation.
- AWS Clean Rooms SQL query execution and query waiting.

## Exclude or route elsewhere

- S3 object movement, read/write, S3 Tables, Delta Lake, and S3 Vectors go to `s3-lakehouse`.
- Redshift, Data API, and direct relational connectors go to `sql-connectors`.
- Runtime, extras, and distributed execution questions go to `runtime-and-config`.
- DynamoDB, Timestream, OpenSearch, Neptune, QuickSight, CloudWatch, EMR, STS, Secrets Manager, and Chime go to `service-integrations`.

## Common user outcomes

A future agent should be able to:
- register S3-backed datasets in Glue,
- inspect and evolve catalog metadata,
- build and run Athena queries with the right output location and workgroup,
- manage data quality rulesets,
- and handle Clean Rooms query execution with the right membership and output settings.

## Shared references and scripts

- `references/api-reference.md`
- `references/workflows.md`
- `references/troubleshooting.md`
- `scripts/smoke_catalog_moto.py`
