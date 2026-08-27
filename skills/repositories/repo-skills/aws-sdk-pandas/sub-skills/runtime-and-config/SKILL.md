---
name: runtime-and-config
description: "Guides awswrangler installation, import checks, configuration,
  optional extras, and Ray/Modin runtime switches."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Runtime and Config

Use this sub-skill for install, import, version, `wr.config`, and distributed-mode questions.

Typical trigger phrases:
- "install awswrangler"
- "why is `Missing optional dependency` raised?"
- "how do I set `WR_*` defaults?"
- "how do I switch between python/pandas and ray/modin?"
- "why does the import work but my feature still fails?"

Read `references/configuration.md` for the public config and distributed-mode facts.
Read `references/troubleshooting.md` when the failure is about importability, optional extras, Ray/Modin, or environment-variable overrides.
Use the shared `../../scripts/check_runtime.py` helper to confirm importability and visible extras before digging into a bug report.

## What belongs here

- Base install and editable install guidance.
- `awswrangler` import verification and version checks.
- `wr.config`, `wr.config.reset`, and `wr.config.to_pandas()`.
- `wr.engine` and `wr.memory_format`.
- `WR_*` environment variables, especially defaults for database, workgroup, region, cache, and service endpoints.
- Optional dependency discovery and the meaning of the repository's lazy optional imports.

## What does not belong here

- S3 file operations, datasets, S3 Tables, or S3 Vectors.
- Athena, Glue Catalog, Data Quality, or Clean Rooms query flows.
- Redshift / RDS / MySQL / PostgreSQL / SQL Server / Oracle connector details.
- DynamoDB, Timestream, OpenSearch, Neptune, QuickSight, CloudWatch, EMR, STS, Secrets Manager, or Chime workflows.

## Common route decisions

- If the user is still deciding what to install, route them here first.
- If the user only needs one service family, finish the runtime check here and then move to the relevant service sub-skill.
- If the user is in distributed mode and seeing unsupported arguments, stay here until the engine/memory mode is clear.

## Shared references and scripts

- `../../references/runtime-overview.md` for install commands and optional extras.
- `../../references/troubleshooting.md` for cross-cutting import / credential / region issues.
- `../../scripts/check_runtime.py` for a safe import and extras check.
