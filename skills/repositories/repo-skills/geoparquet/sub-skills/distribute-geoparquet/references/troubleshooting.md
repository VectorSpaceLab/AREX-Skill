# Distribution troubleshooting

This guide diagnoses planning and layout symptoms. It does not run a reader,
writer, query, cloud request, or validator. For every diagnosis, ask the user
to capture the tool/version and route concrete output metadata and data checks
to [`../../validate-geoparquet/SKILL.md`](../../validate-geoparquet/SKILL.md).

## First-response triage

Collect before changing the file:

1. writer, reader, extensions/backends, and exact versions;
2. target GeoParquet version and whether a `bbox` covering is expected;
3. geometry column, CRS, geometry types, approximate row/byte sizes;
4. row-group count and row/byte targets, file count and partition layout;
5. the exact spatial query, selectivity, columns requested, and cold/warm
   cache/network conditions;
6. whether the source was ordered globally, per partition, or not ordered;
7. validation reports and a before/after benchmark using the same query.

Do not infer a format or performance issue from a file extension, a successful
open, or a tool's default settings.

## Slow selective bbox query

### Symptom: unsorted data

**Likely cause:** geometries from distant areas share row groups, so native
GeoParquet 2.0 row-group bboxes or a GeoParquet 1.1 bbox covering are too broad
to prune much.

**Action:** inspect actual group-level geometry/bbox metadata through the
validation route. Rewrite using a global spatial order (for example DuckDB
`ST_Hilbert`, `gpio`'s documented Hilbert conversion, or GDAL's
`SORT_BY_BBOX=YES`). Do not sort independently with bounds that change per
chunk if the tool's spatial-order algorithm expects the entire dataset bounds.
Re-run the same selective query and compare groups/bytes read, elapsed time,
and output validity.

### Symptom: oversized row groups

**Likely cause:** even compact group bboxes select too much data, especially
for frontend range reads.

**Action:** start around 50,000–150,000 rows or 128–256 MiB per group. For
large/complex rows, reduce the row count. For a frontend-first artifact, use
smaller groups than an analytics-first artifact, and measure metadata overhead
and full-scan impact. Preserve compression and ordering while changing one
layout variable when possible.

### Symptom: both unsorted and oversized

Fix ordering and group sizing together only when the baseline is unusable, but
record both changes. For a large distribution, also test spatial files/tiles;
file-level pruning and parallelism may dominate row-group tuning. Avoid calling
a second output "equivalent" unless the CRS, geometry semantics, duplicates,
and partition assignment are checked.

## Old reader cannot open a 2.0 file

Confirm whether the reader understands native Parquet `GEOMETRY`/`GEOGRAPHY`,
not merely whether it can read ordinary Parquet or WKB. If old-reader support
is mandatory, publish GeoParquet 1.1 with a bbox covering and spatial ordering,
or publish separately tested 1.1 and 2.0 artifacts. Do not fix this by changing
only the filename or by labeling GDAL `USE_PARQUET_GEO_TYPES=ONLY` as
GeoParquet 2.0: the documented GDAL mode omits the `geo` metadata block.
Record the reader/version result as a compatibility constraint and validate
both artifacts independently.

## Native types present but metadata is missing or inconsistent

A native geometry column with geospatial statistics can still be useful to a
2.0-capable reader, but without the required `geo` metadata it is not a
self-described conformant GeoParquet 2.0 file. If `geo` metadata and the native
logical type disagree about CRS, geometry column, encoding, or semantics, stop
publication. Route the file to validation; repair with a writer that preserves
or correctly regenerates metadata rather than hand-editing a label without
checking the bytes and CRS.

## CRS disappeared after a rewrite

Probe the exact DuckDB release: the guide documents CRS preservation in DuckDB
1.5 and later, while earlier versions may drop CRS on write. Also inspect the
source/target writer's handling of PROJJSON and native Parquet CRS properties.
Do not silently assume EPSG:4326 is equivalent in every context; GeoParquet
coordinates use longitude/latitude axis order and OGC:CRS84 semantics when the
metadata says the default CRS. Repair with a CRS-aware tool, then validate that
the native property and any GeoParquet metadata describe the same CRS.

## File is too large or download is slow

Confirm compression, level, row groups, and partition count independently.
Switching Snappy to ZSTD often helps distribution, but level 17+ may cost
substantial publication time for small size gains. A single huge file also
prevents file-level parallelism and selective object reads; use spatial
partitioning for datasets above roughly 2 GB. Avoid making thousands of tiny
files: balance file size, row-group size, object-store request overhead, and
consumer workflows.

## Partitioned query reads too many files

Check whether partitioning is spatially meaningful and whether per-file
extents are tight. A partition column named `region` is not spatial unless its
values actually encode a documented spatial grouping. Review cell resolution,
admin-region size, overlap/duplication behavior, and STAC Item bboxes. For
non-points, check whether centroid/representative-point assignment can exclude
features that cross cells. Repartition with KD-tree, grid, geohash/S2/H3/A5, or
admin boundaries according to the workload, and validate every output file.

## STAC or frontend access does not work

STAC does not make a Parquet asset queryable. Check that the asset uses
`application/vnd.apache.parquet`, links resolve to the published object URL,
partition Items have correct bboxes, and the object store allows the frontend
reader's HTTP range requests and CORS policy. Check that the browser library
supports the chosen GeoParquet version and geometry logical type. If only a
native analytics reader was tested, do not claim browser compatibility.

## Tool recipe errors

- **GDAL/OGR:** probe GDAL and libarrow versions. `COMPRESSION_LEVEL` is
  documented for GDAL 3.12+; native logical types require GDAL 3.12+ built
  against libarrow 21+. `SORT_BY_BBOX=YES` may need temporary space.
- **DuckDB:** probe the DuckDB release and whether `spatial` is installed.
  Core 1.5 handles basic GeoParquet read/write, but `ST_*` ordering or
  reprojection needs the spatial extension. Verify the spelling and support
  for `GEOPARQUET_VERSION`, `COMPRESSION_LEVEL`, and byte row groups in the
  installed release.
- **gpio:** probe the `geoparquet-io` package and `gpio --help`. Defaults and
  subcommands are tool-version facts; confirm `convert`, partition schemes,
  STAC publishing, upload permissions, and `check all` before relying on them.
- **Sedona:** resolve Spark version, Sedona Python package, matching Sedona
  Spark JAR, Java, and cluster configuration. The setup/JAR step is documented
  as tricky. Confirm the `geoparquet` reader/writer and `KDBTREE` APIs against
  the installed release; the source guide does not claim complete support for
  all compression, row-group, or version controls.

When a command fails, retain the exact error and environment probe. Do not
replace a missing dependency with an unrecorded workaround or claim that an
external tool was verified by this skill.

## Difficult synthetic cases

1. **10 GB compatibility release:** an owner wants one public artifact, but
   the reader matrix includes an old GIS client that reads GeoParquet 1.1 and
   rejects native Parquet logical types. Require a version probe, select 1.1 +
   bbox unless the old-reader gate is cleared, use ZSTD 15, global ordering,
   roughly 100,000 rows or 128–256 MiB groups, spatial partitions, and STAC
   Collection/Items. Ask whether a separately maintained 2.0 artifact is worth
   the storage cost. Acceptance is a recorded compatibility matrix and
   validation evidence, not merely a successful write.
2. **Unsorted oversized source:** a selective bbox query on an unsorted single
   file scans nearly every row group. Require the baseline layout/query
   evidence, a global Hilbert/geohash or equivalent order, smaller groups, and
   a repeat query. If the result remains slow at multi-gigabyte scale, compare
   spatial partitioning. Acceptance requires observed improvement plus checks
   that the rewrite did not alter CRS, geometry types, row counts, or duplicate
   semantics.
