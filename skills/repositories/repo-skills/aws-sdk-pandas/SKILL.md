---
name: aws-sdk-pandas
description: "Routes AWS SDK for pandas (awswrangler) workflows across S3
  lakehouse data, Athena/Glue catalogs, SQL connectors, runtime configuration,
  and AWS service integrations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# AWS SDK for pandas

Use this skill when a request names `awswrangler`, `aws-sdk-pandas`, `Pandas on AWS`, or a `wr.*` API from the repository.

This repo is a Python API package, not a CLI tool. The first questions are usually:
- how to install the right extras,
- how to import and verify the runtime,
- which AWS service family the user is working with,
- and which AWS credentials, region, or optional backend are required.

Read `references/runtime-overview.md` first for install, extras, and runtime facts.
Read `references/troubleshooting.md` when import errors, missing extras, region issues, or AWS service prerequisites are blocking you.
Read `references/repo-provenance.md` before deciding whether this skill is current for the checkout.
Run `scripts/check_runtime.py` after installation to confirm importability and optional dependency availability.

## Route map

| If the user asks about... | Read this sub-skill |
| --- | --- |
| Installing, importing, setting `WR_*` env vars, switching `wr.engine` / `wr.memory_format`, or debugging missing extras | `sub-skills/runtime-and-config/SKILL.md` |
| `wr.s3.*` object, file-format, dataset, S3 Tables, or S3 Vectors workflows | `sub-skills/s3-lakehouse/SKILL.md` |
| `wr.catalog.*`, `wr.athena.*`, `wr.data_quality.*`, or `wr.cleanrooms.*` workflows | `sub-skills/catalog-and-query/SKILL.md` |
| `wr.redshift.*`, `wr.data_api.*`, `wr.mysql.*`, `wr.postgresql.*`, `wr.sqlserver.*`, or `wr.oracle.*` workflows | `sub-skills/sql-connectors/SKILL.md` |
| `wr.dynamodb.*`, `wr.timestream.*`, `wr.opensearch.*`, `wr.neptune.*`, `wr.quicksight.*`, `wr.cloudwatch.*`, `wr.emr.*`, `wr.emr_serverless.*`, `wr.sts.*`, `wr.secretsmanager.*`, or `wr.chime.*` workflows | `sub-skills/service-integrations/SKILL.md` |

## Shared operating pattern

1. Confirm the runtime with `scripts/check_runtime.py` when the package was just installed or the environment changed.
2. Pick the service-family sub-skill that matches the `wr.*` API surface.
3. Use `wr.config` and `boto3.Session` for defaults, region, and credentials.
4. Install only the extras needed for the chosen workflow family.
5. Keep live AWS operations separate from local smoke checks; if a workflow needs credentials or managed AWS resources, say so early.

## Common signals

- `NoCredentialsError` or `NoRegionError` usually means the AWS session is not configured.
- `Missing optional dependency ...` usually means the relevant extra was not installed.
- Ray/Modin questions belong in `runtime-and-config` even when they affect `wr.s3` or `wr.athena` calls.
- Live AWS service prerequisites and IAM needs belong in the nearest service sub-skill, not here.

## Shared references and scripts

- `references/runtime-overview.md` for install commands, supported versions, and optional extras.
- `references/troubleshooting.md` for cross-cutting import, dependency, and credential failures.
- `scripts/check_runtime.py` for a safe import/config/extra check.
