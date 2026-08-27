# Fiona cross-cutting troubleshooting

Read the nearest sub-skill troubleshooting page for workflow-specific recovery:
[vector I/O](../sub-skills/vector-io/references/troubleshooting.md),
[`fio`](../sub-skills/cli/references/troubleshooting.md),
[CRS](../sub-skills/crs-transform/references/troubleshooting.md), or
[environment/cloud](../sub-skills/environment-cloud/references/troubleshooting.md).

| Surface | Symptom | First recovery |
|---|---|---|
| Install/import | `ImportError`, undefined symbols, or compiled module failure | Run the runtime checker, isolate Fiona with one compatible GDAL/PROJ stack, and use `pip check`. Do not mix wheel and unrelated system/conda libraries. |
| Optional dependency | `fio calc`/expression command missing or Shapely/boto3 import fails | Install only the documented `[calc]` or `[s3]` extra if that route is required; otherwise use the base route and record the capability as unverified. |
| Driver/data | Unsupported driver, mode, field, or encoding | Inspect `fiona.supported_drivers`, `src.schema`, and `src.crs`; select a compatible format or supply an explicit encoding/schema. |
| CRS/PROJ | Invalid CRS or missing coordinate database | Validate the CRS object and run a one-point transform; repair package-managed PROJ/GDAL data paths through the environment route. Do not guess EPSG codes. |
| CLI framing | JSON parse error or wrong feature count in a pipeline | Preserve LF versus RS sequence framing, inspect one record, and validate the first feature before `fio load` infers a schema. |
| Side effects | Remote download, credentials, requester-pays, or deletion would occur | Stop and request explicit authorization, bounded inputs, and credentials as applicable. Use local fixtures for deterministic work. |

## Verification boundary

A CPU/GDAL smoke check can prove core import, local vector I/O, schema, CRS, and
CLI behavior. It does not prove unapproved cloud access, every optional GDAL
format driver, or credentialed AWS requests. Keep those limitations visible in
reports rather than turning them into passes.
