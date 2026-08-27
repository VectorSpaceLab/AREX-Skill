# Cross-cutting troubleshooting

Read this reference when a GeoParquet task fails before the focused route is
clear, or when a result mixes package setup, format claims, and external tools.

## No `geoparquet` package or import

The source is a specification repository. There is no general-purpose Python
package import to test. Install only the helpers needed for inspection, such as
PyArrow and `jsonschema`, and use the bundled scripts from
`sub-skills/validate-geoparquet/scripts/`. Do not “fix” this by inventing an
editable install or by treating contributor-only scripts as a distribution.

## Generic Parquet read succeeds but GeoParquet validation fails

A `.parquet` extension and a successful `pyarrow.parquet.read_table()` prove
only that the file is readable as Parquet. Inspect the footer and check the
root-level physical type, repetition levels, native `Geometry`/`Geography`
logical type, `geo` metadata, WKB, and row-group statistics. Metadata-only WKB
is not full GeoParquet 2.0.

## CRS appears inconsistent

GeoParquet column metadata accepts inline PROJJSON or `null`; an authority string
such as `EPSG:4326` is not valid in that field. Native Parquet logical-type CRS
has a wider representation set, including authority strings. Resolve the CRS
forms and axis-order semantics separately, then mark semantic equivalence as
not verified if no CRS-aware check was run. Missing `crs` means OGC:CRS84 in the
GeoParquet metadata rules; explicit `null` means undefined or unknown.

## Slow spatial query after “adding a bbox”

A bbox in metadata does not guarantee useful pruning. Confirm spatial ordering,
row-group size, native or 1.1 covering statistics, and partition layout. Route
to `sub-skills/distribute-geoparquet/` for a rewrite plan, then route the
result back to `sub-skills/validate-geoparquet/` for evidence-backed checks.

## External command or extension is missing

GDAL/OGR, DuckDB spatial functions, `gpio`, Sedona/Spark, R geoarrow, and cloud
storage are external surfaces. Probe the exact installed version and required
extension before using a recipe. An unavailable optional tool is not evidence
that the data format is invalid; do not claim a recipe was executed when it was
only read from the specification.

## Raster review tries to validate as vector

The alpha Parquet Raster proposal has a struct raster column, a paired geometry
column, and different metadata semantics. Route to
`sub-skills/parquet-raster/`; do not apply the vector `geo` schema to raster
metadata. Never dereference an out-db URI during review.
