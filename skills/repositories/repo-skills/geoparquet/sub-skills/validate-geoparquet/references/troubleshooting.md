# GeoParquet validation troubleshooting

Keep the writer, reader, exact versions, claimed format version, geometry
column names, and the validator output in the diagnosis. Never fix a failed
conformance check by changing only the filename or a metadata label.

## Missing or malformed `geo`

**Symptoms:** no `geo` footer key, invalid UTF-8/JSON, missing required keys, or
`primary_column` does not name a metadata entry.

1. Inspect the raw footer key/value metadata.
2. Confirm the exact lowercase key `geo` and JSON encoding.
3. Validate a copied metadata object with
   [`../scripts/validate_geo_metadata.py`](../scripts/validate_geo_metadata.py).
4. Regenerate metadata with a writer that understands the target version; do
   not hand-edit a label without checking the bytes, native logical type, CRS,
   and statistics.

## Metadata is present but native logical type is absent

**Symptom:** the geometry column is `BYTE_ARRAY` and contains WKB, but PyArrow
reports no native `Geometry`/`Geography` logical type.

Classify the file as non-conformant GeoParquet 2.0. This is the required
boundary case for a plain WKB fixture. It may be a GeoParquet 1.1 artifact or a
compatible WKB Parquet file, but metadata alone cannot promote it to 2.0.
Choose a writer that emits the native type, or explicitly publish and validate
it against the 1.1 reader target.

## Wrong physical layout, nesting, or repetition

A geometry must be a root-level `BYTE_ARRAY`, required or optional, and not
repeated. A nested path, list/map/struct, non-binary physical type, or repetition
level above zero is a schema failure. Inspect the logical schema rather than
only the Arrow table's column name; rewrite with a native geospatial type.

## Geometry type failures

- Replace `PointZ`, `PointM`, and `PointZM` with `Point Z`, `Point M`, and
  `Point ZM`.
- Remove duplicate list entries, but first determine whether the data actually
  contains a second type.
- Do not use only `MultiPolygon` when the column contains both polygons and
  multipolygons. The list must be complete.
- Treat `[]` as unknown, not as a claim that the data is homogeneous.
- Compare known metadata types with native geospatial statistic codes and
  record missing statistics as unverified.

## Bbox, dimension, and statistics failures

Use only 4 values for XY, 6 for XYZ, or 8 for XYZM. A five-element bbox and an
M-only bbox are invalid metadata forms. Values must be finite and in the same
CRS as the geometry. Compare every row-group extent with the file-level bbox;
do not compare only the first group. If statistics are unavailable in the
installed PyArrow API, report the strict gate as not verified.

## CRS failures

Keep these cases separate:

- metadata `crs` absent: default OGC:CRS84 (longitude, latitude on WGS84);
- metadata `crs: null`: CRS undefined or unknown;
- metadata non-null object: inline PROJJSON, not an authority string;
- native logical type CRS: may be inline PROJJSON, `EPSG:4326` or another
  authority code, `srid:<id>`, or `projjson:<key_name>`; `srid:0` is unknown.

When both forms are present, they must describe the same CRS but need not be
byte-identical. The local validator only checks the safe inline object shape;
it does not resolve an external authority or prove equivalence. Preserve that
limit in the report.

## Edges, orientation, and epoch

Reject misspelled or uppercase edge values. Absent `edges` means `planar`;
`orientation` is only `counterclockwise` and is an assertion about exterior
and interior polygon winding. `epoch` is numeric decimal-year metadata for a
dynamic CRS and is per column. If edges are non-planar and orientation is
omitted, report the portability/interpretation risk rather than silently
inventing a winding order.

## Remote schema, imports, and fixture creation

The default helpers never access the network. A local metadata pass is useful
without a PROJJSON registry, but it is not a complete PROJJSON validation. If a
full registry-backed check is required, run it as a separately approved,
versioned check and retain its result. If imports fail, probe the installed
CPU environment and exact versions; do not claim that the specification
repository is an installable package.

For a deterministic tiny case, use
[`../scripts/make_wkb_fixture.py`](../scripts/make_wkb_fixture.py). Use
`--plain` with the fixture writer to exercise the deliberate non-native boundary
and `--native` (the default) only when `geoarrow-pyarrow` is installed.

## 1.1 compatibility confusion

A bbox covering, legacy WKB column, or a `geometry`/`geography` column name does
not by itself establish 1.1 or 2.0. Record the actual metadata version and
native logical type. If old readers are mandatory, validate a real 1.1 artifact
against its 1.1 contract and keep it distinct from a 2.0 artifact.
