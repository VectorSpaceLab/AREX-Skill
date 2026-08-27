---
name: distribute-geoparquet
description: "Plan and produce a distribution-ready GeoParquet publication using
  evidence-backed compression, spatial ordering, row-group, partitioning,
  compatibility, STAC, and frontend-access choices; route file-level metadata
  and data checks to validate-geoparquet."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Distribute GeoParquet

Use this sub-skill when a user is planning a public or internal GeoParquet
release, choosing a writer, designing a partitioned distribution, or diagnosing
spatial-access performance. It is a planning and recipe skill: it does **not**
install, bundle, invoke, or claim to verify GDAL/OGR, DuckDB, `geoparquet-io`
(`gpio`), Sedona, Spark, cloud storage, or frontend readers.

For concrete file metadata, schema, native-type, `geo`-metadata, CRS, bbox,
compression, and data-validity checks, route to
[`../validate-geoparquet/SKILL.md`](../validate-geoparquet/SKILL.md). Ask the
user to probe the installed tool and version before selecting a command. Keep
the tool/version output and any validation report as evidence; do not infer
support from a command name alone.

## Routing workflow

1. Establish the publication target: one file or a dataset, approximate size
   and row count, object-store layout, query shapes, frontend versus analytic
   access, expected readers, and whether old GeoParquet readers must work.
2. Choose the format target. Prefer native GeoParquet 2.0 when the complete
   reader set supports Parquet `GEOMETRY`/`GEOGRAPHY` and geospatial statistics.
   Choose GeoParquet 1.1 with the bbox covering when compatibility with a wider
   or older reader population is more important. Do not describe GDAL's native
   type-only output as conformant GeoParquet 2.0; see
   [`references/tool-recipes.md`](references/tool-recipes.md).
3. Plan physical layout: spatial ordering, row groups, and—normally for data
   above roughly 2 GB—spatial partitioning. Tune the plan to feature size and
   access patterns, not just row counts.
4. Plan publication metadata: STAC Collection/Items, media type
   `application/vnd.apache.parquet`, stable object URLs, and reader/browser
   access constraints.
5. Hand the plan and candidate writer recipe to the user. Require them to
   install/probe the external tools and then use
   [`../validate-geoparquet/SKILL.md`](../validate-geoparquet/SKILL.md) on the
   resulting files. If a required tool or reader capability is unknown, mark
   it unresolved rather than claiming success.

For detailed recommendations, read
[`references/distribution-recommendations.md`](references/distribution-recommendations.md).
For copyable commands and code, read
[`references/tool-recipes.md`](references/tool-recipes.md). For failure modes,
read [`references/troubleshooting.md`](references/troubleshooting.md).

## Decision guardrails

- Use ZSTD, normally level 15 or higher. Levels 17–22 can take substantially
  longer for less than roughly one percent additional size reduction; choose
  based on publishing time and benchmark evidence.
- Spatial ordering is a prerequisite for useful row-group bbox pruning. A
  valid bbox or native geometry statistic does not make unsorted data fast.
- Start with 50,000–150,000 rows per row group. If byte sizing is available,
  target about 128–256 MiB per group, reducing row counts for wide or complex
  features. Frontend bbox access often needs smaller groups than full scans.
- Partition spatially, rather than only by arbitrary attributes, when the
  dataset is larger than about 2 GB or selective spatial reads dominate. KD
  trees, grids, geohash/S2/H3/A5 cells, and administrative boundaries are
  alternatives with different balance and overlap trade-offs.
- A single file can serve analytics and a frontend, but row-group size is a
  compromise: small groups reduce irrelevant network transfer for bbox reads;
  too many groups increase metadata and full-scan overhead. Consider separate
  distributions when the workloads conflict.
- STAC describes the published asset; it is not a substitute for GeoParquet
  metadata or validation. Use the Parquet media type and describe partition
  extents with Items.
- `.parquet` and `application/vnd.apache.parquet` are the interoperable file
  extension and media type. Avoid presenting `.geoparquet` as the default.

## Synthetic planning cases

- **10 GB public data with old-reader compatibility:** probe the actual reader
  matrix first. If old readers do not reliably understand native Parquet
  geospatial types, select a GeoParquet 1.1 distribution with bbox covering,
  ZSTD level 15, spatial ordering, 100,000-row (or byte-sized) row groups, and
  spatial partitions. Publish a STAC Collection with per-partition Items. Only
  choose 2.0 as the public canonical distribution when the old-reader gate is
  explicitly cleared; a second 2.0 distribution may be preferable to silently
  sacrificing compatibility.
- **Slow bbox query from unsorted data and oversized row groups:** do not first
  add arbitrary indexes or claim the bbox metadata is broken. Confirm ordering
  and inspect row-group sizing with the validation skill, then rewrite with
  spatial ordering and smaller groups (for example 100,000 rows as a starting
  point, or a byte target around 128–256 MiB). Repartition if the dataset is
  large. Re-run the same selective query and metadata/data checks; retain both
  before/after observations.

## References

- [Distribution recommendations](references/distribution-recommendations.md)
- [Tool recipes and version caveats](references/tool-recipes.md)
- [Troubleshooting and synthetic cases](references/troubleshooting.md)
- [Metadata and data validation router](../validate-geoparquet/SKILL.md)
