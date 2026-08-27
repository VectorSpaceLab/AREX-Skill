# Distribution recommendations

This reference distills the repository's distribution guide for a producer
who needs a practical publication plan. It is not a conformance report. After
writing or receiving a file, route all concrete metadata and data checks to
[`../validate-geoparquet/SKILL.md`](../../validate-geoparquet/SKILL.md), and
record the tool versions used.

## 1. Choose a compatibility target

### Native GeoParquet 2.0

GeoParquet 2.0 stores geometry columns as native Parquet `GEOMETRY` or
`GEOGRAPHY` logical types. The values are WKB in a `BYTE_ARRAY`; the native
logical type carries CRS information and geospatial statistics, including a
bounding box at the column-chunk/row-group level. Readers can skip row groups
whose geometry bbox cannot intersect the query. A conformant file also has the
GeoParquet `geo` key with `version`, `primary_column`, and column metadata; the
metadata CRS, when present, is inline PROJJSON and must describe the same CRS as
the native logical type.

Native statistics remove the need for a separate per-row `bbox` covering and
usually make a smaller file. They remain row-group statistics: ordering and
sensible groups are still required for good pruning, and selected row groups
still have to be read. Native statistics do not provide page-level pruning in
the same way as an ordinary 1.1 covering column.

Use 2.0 when the known writer and reader set supports native geospatial types,
CRS handling, and the needed GeoParquet metadata. Probe versions first; a
writer that emits native types alone may create readable plain Parquet rather
than self-described GeoParquet 2.0.

### GeoParquet 1.1 with bbox covering

Use GeoParquet 1.1 when a wider range of deployed or older readers is a hard
requirement. The 1.1 bbox covering is a struct of four values per row and can
be larger—especially for points—but it is broadly understood and can benefit
from ordinary Parquet page-level column indexes as well as row-group
statistics. It is a valid compatibility choice, not an obsolete or invalid
format.

Do not mix up a 1.1 file with an arbitrary WKB Parquet file. Compatibility
fallbacks are only intended for producers that cannot write valid GeoParquet.
The lowest-common-denominator compatible shape is a root column called
`geometry` or `geography`, WKB in `BYTE_ARRAY`, WGS84 longitude/latitude
(OGC:CRS84 semantics), and `planar` edges for `geometry` or `spherical` edges
for `geography`; readers should still prefer official GeoParquet metadata when
it exists. Prefer a real 1.1 writer over relying on compatibility assumptions.

### Selection rule

Make the reader matrix explicit:

| Requirement | Recommended target |
|---|---|
| Current readers and native Parquet geospatial support | GeoParquet 2.0 |
| Old or heterogeneous readers, especially unknown versions | GeoParquet 1.1 + bbox covering |
| Both groups are mandatory | Publish a tested compatibility artifact and a separate 2.0 artifact, or select 1.1 as canonical until the old-reader gate is cleared |

A major-version change is not just a metadata label. Probe the actual output
and use the validation route before publishing.

## 2. Compression

Use ZSTD for distribution. Start at level 15 or higher, then benchmark if
publishing time matters. ZSTD decompression time is approximately constant
across levels, so spending more CPU at publication can reduce download cost.
Levels 17 and above have steeply diminishing returns and may take much longer;
level 22 is rarely worthwhile unless the extra publishing time is acceptable.
The repository notes that many Arrow-based writers default to level 1, and
many writers default to Snappy, so do not assume a library's default meets the
recommendation.

Compression saves network transfer but does not fix poor spatial layout. Keep
the chosen level, file sizes, elapsed write time, and reader behavior as
publication evidence.

## 3. Spatial ordering

Order rows so nearby geometries are near one another inside the file. Hilbert
ordering, geohash, S2, R-tree-derived order, or a source format's existing
spatial order can work; GeoParquet does not mandate one index. A GeoPackage or
FlatGeobuf source may already be spatially ordered, but confirm rather than
assuming.

Ordering makes row-group bboxes compact. Without it, a group may span most of
the dataset even when a query selects only a small area, forcing unnecessary
reads. For a rewrite, compute the ordering key over the bounds of the entire
dataset—not independently per chunk—when the selected tool requires global
bounds. Preserve the geometry and CRS semantics through the sort.

## 4. Row groups

Start with a maximum of 50,000–150,000 rows; 100,000 is a useful recipe
starting point. There is no universal optimum. The important physical unit is
bytes read for a selected group, so if the writer supports bytes, target about
128–256 MiB per row group. Use fewer rows for large or complex geometries and
more rows for small rows if metadata overhead is acceptable.

The trade-off is direct:

- oversized groups make selective bbox queries fetch too much irrelevant data;
- undersized groups increase footer metadata and can hurt full scans;
- frontend display typically favors smaller groups and lower latency;
- analytic scans typically favor larger groups and lower metadata overhead.

If the same artifact must serve both, choose based on the dominant workload or
publish separate frontend and analytics layouts.

## 5. Spatial partitioning

For datasets larger than roughly 2 GB, split the distribution into multiple
files using a spatially meaningful scheme. Partitioning allows file-level
selection and parallel reads. It can also keep each file's row-group bboxes
tight. The partitioning strategy must match geometry type and query behavior:

- KD-tree: balances feature counts and spatial separation; a strong default
  for large irregular datasets.
- Grid, quadkey, geohash, S2, H3, or A5: easy to address and useful for global
  datasets; choose resolution to avoid tiny files or overloaded cells.
- Administrative boundaries: intuitive and useful for user-facing downloads,
  but large regions may need further subdivision.
- R-tree-derived approaches: can preserve locality but may not balance file
  sizes as well.

For non-point geometries, partition by an explicit documented representative
point or another scheme that handles geometry extent; do not imply that a
centroid partition is a complete geometry-intersection index. Account for
cross-boundary features and whether the tool duplicates or assigns them.

Aim for reasonably sized files and row groups, not a fixed partition count.
Keep the partition column only if it is useful to consumers, and document its
meaning in the catalog.

## 6. STAC publication

For one public file, place a STAC Collection or Item alongside it as
appropriate; the guide specifically recommends a Collection-level description
and `application/vnd.apache.parquet` as the asset media type. For a partitioned
dataset, publish a Collection and an Item for each file, with each Item's bbox
covering that file's extent. Link assets with stable URLs and include enough
licensing, temporal, spatial, and provider information for the distribution's
users.

STAC is catalog metadata, not a replacement for the Parquet `geo` metadata,
CRS, geometry encoding, or validation. Generate it with a tool that supports
STAC or a library such as `pystac`/`rustac`, and validate the actual extents
against the files through the validation skill.

## 7. Frontend/object-store access

GeoParquet can be queried directly from object storage by frontend readers
using range requests, but the deployment must support the reader's required
HTTP range/CORS behavior and stable URLs. Native geometry statistics or a 1.1
bbox covering can skip irrelevant row groups; row groups remain the unit of
native geometry pruning.

For a map viewport or bbox query, reduce group size enough to avoid fetching a
large amount of irrelevant geometry. This increases footer/group metadata and
can slow whole-dataset analytics. Partitioned files can further reduce remote
work. Plan the browser reader and object-store behavior together; do not claim
frontend suitability solely because a file opens in an analytics engine.

## 8. Publication checklist

Before announcing a release, record:

- GeoParquet target (2.0 native types or 1.1 + bbox), reader/version matrix,
  and any compatibility artifact.
- CRS, coordinate-axis semantics, geometry encoding, primary geometry column,
  and edge interpretation.
- ZSTD level, write time, output size, and row-group row/byte target.
- Ordering key and whether ordering was global or per partition.
- Partitioning scheme, file count, approximate file sizes, overlap/duplication
  policy, and partition-column meaning.
- STAC Collection/Item links, asset media type, extents, license, and object
  URLs.
- Frontend range/CORS assumptions if direct browser access is promised.
- The concrete validation report and any unresolved reader/tool gaps.
