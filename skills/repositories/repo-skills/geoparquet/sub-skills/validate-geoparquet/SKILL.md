---
name: validate-geoparquet
description: "Validate and explain GeoParquet 2.0 vector files by checking local
  geo metadata, native Parquet Geometry/Geography types, WKB, CRS, dimensions,
  bounding boxes, footer statistics, and the GeoParquet 1.1 compatibility
  boundary."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Validate GeoParquet

Use this skill when a user asks whether a Parquet file is GeoParquet, wants to
check the `geo` metadata, needs to inspect a native geometry logical type or
geospatial statistics, or is troubleshooting WKB, CRS, `geometry_types`,
`bbox`, `edges`, `orientation`, or `epoch`. It covers vector GeoParquet 2.0.
It is not a general-purpose writer, converter, package installer, benchmark
runner, or raster validator. For publication layout and external writer
selection, route to [`../distribute-geoparquet/SKILL.md`](../distribute-geoparquet/SKILL.md).
For the alpha raster proposal, route to
[`../parquet-raster/SKILL.md`](../parquet-raster/SKILL.md).

The bundled helpers are deliberately checkout-independent and offline by
default. They require only the relevant installed Python dependencies (normally
PyArrow and `jsonschema`; native fixture creation additionally uses
`geoarrow-pyarrow`). The verified CPU smoke baseline is pyarrow 25.0.1,
geoarrow-pyarrow 0.2.0, geopandas 1.1.4, and jsonschema 4.26.0, with
`referencing` imports succeeding. Its local example reports `geo.version`
2.0.0, native `Geometry`, and geo statistics. Probe the actual runtime before
relying on these versions. The repository described by the source evidence is a
specification and example suite, not an installable Python package; do not
claim that installing this skill installs a GeoParquet writer.

## Conformance target

A GeoParquet 2.0 candidate has two coordinated contracts:

1. **Native Parquet geometry.** Every geometry column is a root-level,
   required or optional `BYTE_ARRAY` annotated as native `GEOMETRY` or
   `GEOGRAPHY`. It is not repeated, nested, a list, a map, or a struct. The
   values use WKB and x,y axis order regardless of CRS axis declarations.
2. **Footer metadata.** File key/value metadata has an exact `geo` key whose
   UTF-8 value is JSON. The object has `version: "2.0.0"`, a non-empty
   `primary_column`, and a non-empty `columns` object. Every geometry column is
   listed with `encoding: "WKB"` and a `geometry_types` array.

Metadata alone is not enough: a plain binary WKB column carrying plausible
`geo` JSON is **non-conformant** GeoParquet 2.0. Conversely, native Parquet
geometry without the `geo` metadata block is useful native geospatial Parquet
but is not a self-described GeoParquet 2.0 file.

Read the detailed rules in [`references/vector-spec.md`](references/vector-spec.md)
and the schema and offline-validation boundary in
[`references/metadata-schema.md`](references/metadata-schema.md).

## Operating procedure

### 1. Establish the claim

Record the intended version, each geometry column, whether this is a single file
or a partition, and whether GeoParquet 1.1 readers are required. Do not infer
format support from a filename, a successful generic Parquet open, or a writer
name. Preserve the exact tool and library versions used to create the file.

### 2. Inspect the footer before interpreting metadata

Run the bundled inspector from any working directory:

```bash
python /path/to/inspect_geoparquet.py data.parquet
```

For a strict gate, use `--require-conformant --require-statistics`. Review the
`geo` key, schema paths, physical types, definition/repetition levels, native
logical type JSON, row-group count, and every row-group's geospatial statistics.
The expected geometry leaf is root-level `BYTE_ARRAY`, max repetition level 0,
and native `Geometry` or `Geography`.

### 3. Validate the `geo` object locally

A metadata file may be the bare object or `{"geo": {...}}`:

```bash
python /path/to/validate_geo_metadata.py metadata.json
```

To validate a metadata file against a Parquet footer, use:

```bash
python /path/to/validate_geo_metadata.py metadata.json --parquet data.parquet
```

Passing `data.parquet` as the input extracts the footer `geo` value directly.
The default is local and does not fetch the PROJJSON schema. A non-zero exit
means the metadata or requested footer checks failed. Use
`--allow-missing-statistics` only when the report explicitly records that the
statistics gate was deferred; it does not turn absent statistics into verified
statistics. A supplied `--schema` is also localized offline if it contains a
remote `$ref`.

### 4. Reconcile metadata, logical types, and statistics

For every metadata geometry column, check that:

- the column exists as a root-level Parquet field and is WKB `BYTE_ARRAY`;
- it is required or optional, never repeated or nested;
- its native logical type is `Geometry` or `Geography`;
- the `primary_column` names both a metadata entry and a native geometry field;
- the geometry type list is complete, unique, and dimension-suffixed correctly;
- known types match native `geospatial_types` statistics, while `[]` means
  unknown rather than “Point”;
- the file-level bbox is in the same CRS and contains every row-group extent;
- native statistics are present for the strict 2.0 inspection gate; and
- native CRS semantics agree with `geo.columns[*].crs`, even when the two
  representations are not byte-for-byte identical.

The local helper reports metadata-level CRS shape and footer facts, but it does
not resolve an authority registry or prove semantic CRS equivalence. Record
those as unresolved unless a separately approved CRS-aware check is available.

### 5. Apply the exact field rules

- `encoding` is exactly `WKB`.
- Allowed base geometry types are `Point`, `LineString`, `Polygon`,
  `MultiPoint`, `MultiLineString`, `MultiPolygon`, and `GeometryCollection`.
  Dimension suffixes are exactly ` Z`, ` M`, or ` ZM`; `Point Z` is valid but
  `PointZ` is not. Types must be unique and complete.
- `crs` in GeoParquet metadata is inline PROJJSON or `null`, never an authority
  string. If absent, the default is OGC:CRS84 (longitude, latitude on WGS84);
  `null` means undefined or unknown. On the native logical type, CRS may be
  inline PROJJSON, `<authority>:<code>` such as `EPSG:4326`, `srid:<id>`
  (`srid:0` means undefined/unknown), or `projjson:<key_name>`.
- `edges` is one of `planar`, `spherical`, `vincenty`, `thomas`, `andoyer`, or
  `karney`; absent means `planar`. `orientation`, when present, is only
  `counterclockwise` and asserts counterclockwise exterior and clockwise
  interior polygon rings.
- `bbox` is 4 values for XY, 6 for XYZ, or 8 for XYZM, with minimums followed
  by maximums (and RFC 7946 geographic ordering). A 5-element bbox is invalid;
  M-only bounds cannot be expressed in this metadata field. `epoch` is an
  optional decimal year for a dynamic CRS and is per column.
- The native logical type's geospatial statistics should expose geometry type
  codes and x/y extents, with z/m extents when applicable. A supplied metadata
  bbox must contain all row-group extents.

For a compact field reference, see
[`references/vector-spec.md`](references/vector-spec.md). For schema-valid and
invalid examples, see [`references/metadata-schema.md`](references/metadata-schema.md).

### 6. Classify and recover

Classify the result as **conformant candidate** only when local metadata,
native schema, WKB/physical layout, and required statistics checks pass. Use
**non-conformant** for any required failure, especially metadata with no native
logical type, `PointZ`, duplicate geometry types, a five-element bbox, a string
metadata CRS, nested/repeated geometry, or mismatched statistics. Use **not
verified** when a full PROJJSON validation, CRS equivalence check, or required
statistics observation could not run. Do not relabel “not verified” as pass.

Follow [`references/inspection-workflow.md`](references/inspection-workflow.md)
for the complete decision sequence and
[`references/troubleshooting.md`](references/troubleshooting.md) for bounded
recovery actions. Keep raw reports and review artifacts outside this runtime
skill tree.

## Safe bundled helpers

All runtime files are linked here so they can be discovered without source
checkout assumptions:

- [`scripts/validate_geo_metadata.py`](scripts/validate_geo_metadata.py) —
  offline metadata validator; accepts bare/wrapped JSON or a Parquet footer and
  returns non-zero for invalid metadata or failed requested footer checks.
- [`scripts/inspect_geoparquet.py`](scripts/inspect_geoparquet.py) — emits a
  JSON footer report with `geo` metadata, schema/logical-type facts, native
  columns, and row-group statistics; non-conformant reports return non-zero.
- [`scripts/write_minimal_geo_metadata.py`](scripts/write_minimal_geo_metadata.py)
  — writes an explicit one-row native fixture when `geoarrow-pyarrow` is
  available, or a deliberate `--plain` non-native fixture for boundary tests.
- [`scripts/make_wkb_fixture.py`](scripts/make_wkb_fixture.py) — writes a
  deterministic WKB fixture for each supported base geometry and XY/XYZ/XYM/XYZM.

Each script supports `--help`, explicit paths, arbitrary current working
directories, and no network access. The fixture scripts refuse to overwrite an
existing output unless `--force` is supplied.

## GeoParquet 1.1 compatibility boundary

GeoParquet 1.1 commonly stores WKB `BYTE_ARRAY` values with legacy `geo`
metadata and a bbox covering. That is a deliberate compatibility target for
older or heterogeneous readers, not a 2.0 label: it lacks the required native
`GEOMETRY`/`GEOGRAPHY` logical type. The compatibility guidance assumes a
`geometry` or `geography` column, WGS84 longitude/latitude (OGC:CRS84), and
`planar` or `spherical` edges respectively. Prefer a real 1.1 writer when that
reader matrix is mandatory, and validate the 1.1 artifact as 1.1 rather than
calling it 2.0. A native-type-only file without `geo` metadata is likewise not
full 2.0 GeoParquet.

## Routing links

- Publication, compression, ordering, partitioning, STAC, and external writer
  selection: [`../distribute-geoparquet/SKILL.md`](../distribute-geoparquet/SKILL.md).
- Alpha raster proposal: [`../parquet-raster/SKILL.md`](../parquet-raster/SKILL.md).
- Normative vector rules: [`references/vector-spec.md`](references/vector-spec.md).
- Metadata schema and offline caveats: [`references/metadata-schema.md`](references/metadata-schema.md).
- Footer workflow: [`references/inspection-workflow.md`](references/inspection-workflow.md).
- Troubleshooting: [`references/troubleshooting.md`](references/troubleshooting.md).
