---
name: geoparquet
description: "Use the GeoParquet specification and bundled inspection helpers to
  author, validate, distribute, or safely review geospatial Parquet data,
  including GeoParquet 2.0 vector metadata, external writer choices, and the
  alpha Parquet Raster proposal."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# GeoParquet

Use this skill when a task involves GeoParquet, Parquet `GEOMETRY`/`GEOGRAPHY`
logical types, WKB geometry columns, the Parquet `geo` metadata key, CRS/PROJJSON,
spatial row-group statistics, GeoParquet distribution, STAC publication, or the
alpha Parquet Raster proposal.

This repository is a specification and example suite, not an installable Python
writer package. Do not tell a user to install `geoparquet` as if it were a
library. For local inspection helpers, install the dependencies appropriate to
the task, then run a neutral import check:

```bash
python -m pip install "pyarrow>=22" "jsonschema>=4" "geoarrow-pyarrow>=0.2"
python -c "import pyarrow, jsonschema; print(pyarrow.__version__)"
```

The helper scripts are self-contained and offline by default. They do not fetch
PROJJSON schemas, resolve authority registries, install external writers, or
contact out-of-database raster URIs. Keep the exact writer/reader versions and
raw inspection output with any conformance or publication decision.

## Route by task

- **Validate or inspect a vector file:** read
  [`sub-skills/validate-geoparquet/SKILL.md`](sub-skills/validate-geoparquet/SKILL.md).
  Use it for `geo` JSON, native logical types, WKB layout, CRS, geometry types,
  bbox, and row-group geospatial statistics. It distinguishes a full 2.0 file
  from metadata-only or native-type-only Parquet.
- **Plan a distribution or choose a writer:** read
  [`sub-skills/distribute-geoparquet/SKILL.md`](sub-skills/distribute-geoparquet/SKILL.md).
  Use it for GDAL/OGR, DuckDB, `gpio`/geoparquet-io, Sedona, compression,
  ordering, row groups, spatial partitioning, STAC, and old-reader tradeoffs.
- **Review raster-in-Parquet designs:** read
  [`sub-skills/parquet-raster/SKILL.md`](sub-skills/parquet-raster/SKILL.md).
  Treat it as an alpha proposal only; do not transfer vector conformance rules
  to raster columns.

## Shared operating rules

1. Establish the claimed GeoParquet version, file or dataset scope, writer and
   reader versions, expected CRS, and compatibility requirements before giving
   a pass/fail result.
2. Inspect the Parquet footer, not only the filename or a successful generic
   Parquet read. GeoParquet 2.0 requires native root-level, non-repeated
   `BYTE_ARRAY` geometry columns annotated `GEOMETRY` or `GEOGRAPHY`, plus a
   JSON `geo` metadata block.
3. Validate metadata locally, then reconcile metadata with physical schema,
   WKB representation, native CRS, geometry-type statistics, and row-group
   extents. Mark unresolved PROJJSON or CRS-equivalence checks as **not
   verified**, never as passed.
4. Choose GeoParquet 2.0 for native geometry types and geospatial statistics
   when the reader matrix supports them. Choose 1.1 with bbox covering when
   older readers require it, and label the artifact with its actual version.
5. Before publication, plan compression, spatial ordering, row groups,
   partitioning, and STAC separately from logical conformance. A valid bbox or
   native statistic does not make unsorted data fast.
6. Never fetch an out-db raster URI during review. Preserve alpha-proposal
   ambiguities and external dependencies in the result.

Read [`references/troubleshooting.md`](references/troubleshooting.md) for
cross-cutting recovery guidance, and read
[`references/repo-provenance.md`](references/repo-provenance.md) before deciding
whether this graph is stale relative to a repository checkout.

## Scope limits

This graph does not implement a general GeoParquet writer, run production-scale
conversion or benchmarks, install external tools, resolve every CRS authority,
or certify the alpha raster proposal. It does include safe bundled vector
metadata/footer helpers; their ownership and usage are described by the
validation sub-skill.
