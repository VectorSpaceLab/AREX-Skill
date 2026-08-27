---
name: vector-io
description: "Guides Fiona Python workflows for reading, writing, appending,
  inspecting, and safely round-tripping vector datasets, features, schemas,
  layers, memory files, and local virtual files."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Fiona vector I/O

Use this route when the task is about Fiona's Python API for vector data: open a
file, stream features, inspect metadata, create or append a layer, validate a
schema, use `Feature`/`Geometry`/`Properties`, or work with bytes and local
archive paths. Fiona is a GDAL/OGR-backed feature I/O library; it is not a
geometry-analysis or CRS-transformation engine.

## Route

1. Read [API reference](references/api-reference.md) for signatures and object
   behavior.
2. Read [workflows](references/workflows.md) for read, write, append,
   conversion, and memory-file recipes.
3. Read [data model and schema](references/data-model-and-schema.md) when
   creating a layer or diagnosing field/geometry mismatches.
4. Read [troubleshooting](references/troubleshooting.md) before changing a
   driver, CRS, encoding, or schema after an error.
5. For CRS construction or coordinate transformation, continue to
   [crs-transform](../crs-transform/SKILL.md). For GDAL configuration, driver
   discovery, or cloud sessions, use
   [environment-cloud](../environment-cloud/SKILL.md). For shell pipelines, use
   [cli](../cli/SKILL.md).

## Core decision points

- Reading normally needs only a dataset path and optional `layer`; writing needs
  a driver, schema, and usually a CRS.
- Prefer `with fiona.open(...)` so external GDAL resources are closed even when
  feature processing raises.
- Use `src.profile` as a starting point for a compatible output, then change
  `driver`, `schema`, `layer`, or CRS deliberately and validate the result.
- Treat a `Collection` as a stream. Iterating consumes the current cursor;
  reopen it instead of assuming seeking to the beginning is supported.
- Use `MemoryFile` for bounded byte-backed or temporary datasets. Use a normal
  path when the result must persist beyond the process.
- Use `include_fields` or `ignore_fields`, but never both in one open call.

The generated references contain the operational detail; they are designed to
work when the original Fiona checkout is unavailable.
