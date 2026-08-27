---
name: service-integrations
description: "Guides awswrangler DynamoDB, Timestream, OpenSearch, Neptune,
  QuickSight, CloudWatch, EMR, EMR Serverless, STS, Secrets Manager, and Chime
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Service Integrations

Use this sub-skill when the user is working with `wr.dynamodb.*`, `wr.timestream.*`, `wr.opensearch.*`, `wr.neptune.*`, `wr.quicksight.*`, `wr.cloudwatch.*`, `wr.emr.*`, `wr.emr_serverless.*`, `wr.sts.*`, `wr.secretsmanager.*`, or `wr.chime.*` workflows.

Typical triggers:
- "write items to DynamoDB"
- "query Timestream"
- "index documents into OpenSearch"
- "load data into Neptune"
- "create a QuickSight dataset"
- "search CloudWatch logs"
- "create an EMR cluster or EMR Serverless app"
- "get the current AWS account ID"
- "read a secret from Secrets Manager"
- "send a Chime message"

Read `references/api-reference.md` for the service-by-service function map.
Read `references/workflows.md` for the common service patterns and the right mental model for each wrapper.
Read `references/troubleshooting.md` for missing extras, permissions, service setup, and backend-specific failures.
Use `../../scripts/check_runtime.py` from the root skill when you need to verify optional extras before a workflow.

## Include here

- DynamoDB item and PartiQL helpers.
- Timestream database, table, write, query, batch load, and unload helpers.
- OpenSearch connection, indexing, and search helpers.
- Neptune graph connect, execute, flatten, and bulk load helpers.
- QuickSight resource listing, creation, description, and ingestion helpers.
- CloudWatch Logs query, wait, read, filter, and stream description helpers.
- EMR and EMR Serverless cluster/job/application helpers.
- STS identity helpers.
- Secrets Manager secret helpers.
- Chime webhook message posting.

## Exclude or route elsewhere

- S3 file movement, S3 Tables, Delta Lake, and S3 Vectors go to `s3-lakehouse`.
- Glue Catalog, Athena, Data Quality, and Clean Rooms go to `catalog-and-query`.
- Relational database drivers, Redshift, and Data API workflows go to `sql-connectors`.
- Runtime, extras, and Ray/Modin mode questions go to `runtime-and-config`.

## Common user outcomes

A future agent should be able to:
- decide whether a service needs moto, live AWS, or only a pure helper check,
- use the right boto3 session and optional extra,
- and avoid forcing a live AWS assumption when the local helper path is enough.

## Shared references and scripts

- `references/api-reference.md`
- `references/workflows.md`
- `references/troubleshooting.md`
- `scripts/smoke_dynamodb_moto.py`
- `scripts/smoke_service_basics.py`
