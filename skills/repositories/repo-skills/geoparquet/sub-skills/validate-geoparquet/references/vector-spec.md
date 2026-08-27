# GeoParquet 2.0 vector rules

Use the native GeoParquet 2.0 target when a file is claimed to be conformant.
The format has two coordinated contracts; passing one does not imply passing the
other.

## Native Parquet contract

Each geometry column MUST be a root-level `BYTE_ARRAY` annotated with the
Parquet `GEOMETRY` or `GEOGRAPHY` logical type. It MUST be required or optional
and MUST NOT be repeated, nested in a struct/list/map, or stored as a different
physical type. The bytes use WKB and the coordinate axis order is always x,y
(easting/longitude, then northing/latitude), overriding CRS axis declarations.

The native logical type carries the CRS source of truth. A reader MUST handle
inline PROJJSON and `<authority>:<code>` forms, and SHOULD try `srid:<id>` and
`projjson:<key_name>`. `srid:0` means an undefined or unknown CRS. Native
statistics should provide geospatial type codes and row-group extents.

## Footer metadata contract

The Parquet footer MUST contain a UTF-8 JSON key/value entry whose exact key is
`geo`. The object MUST include:

```json
{
  "version": "2.0.0",
  "primary_column": "geometry",
  "columns": {
    "geometry": {"encoding": "WKB", "geometry_types": []}
  }
}
```

`primary_column` must be non-empty and name a `columns` entry. `columns` must
contain metadata for every geometry column. Unknown implementation-specific
file and column fields are allowed where the schema allows them, but a reader
must explicitly validate values it relies upon.

## Geometry types and dimensions

Allowed base names are `Point`, `LineString`, `Polygon`, `MultiPoint`,
`MultiLineString`, `MultiPolygon`, and `GeometryCollection`. Dimension suffixes
are separated by one leading space:

- XY: `Point`
- XYZ: `Point Z`
- XYM: `Point M`
- XYZM: `Point ZM`

The list must be unique. An empty list means the types are unknown. If known,
it must be complete: a mixture of polygons and multipolygons requires both
`Polygon` and `MultiPolygon`, and a 3D point requires `Point Z`. These values
must agree with native geospatial statistics.

## Column metadata fields

- `encoding` is required and exactly `WKB`.
- `crs`, when present, is inline PROJJSON or `null`; an authority string such
  as `EPSG:4326` is invalid in GeoParquet column metadata. If absent, the
  default is OGC:CRS84: longitude, latitude on WGS84. `null` means undefined
  or unknown. If metadata is present, its CRS must describe the same CRS as the
  native logical-type property, without requiring byte-for-byte equality.
- `edges` may be `planar`, `spherical`, `vincenty`, `thomas`, `andoyer`, or
  `karney`; absent means `planar`.
- `orientation`, when present, is exactly `counterclockwise`. It asserts
  counterclockwise exterior rings and clockwise interior rings. If absent,
  winding order is not asserted. It is recommended with non-planar edges.
- `bbox` contains finite numbers in the geometry CRS. It is `[xmin, ymin,
  xmax, ymax]` for XY, `[xmin, ymin, zmin, xmax, ymax, zmax]` for XYZ, and
  `[xmin, ymin, zmin, mmin, xmax, ymax, zmax, mmax]` for XYZM. For geographic
  data, use RFC 7946 longitude/latitude ordering, including its antimeridian
  convention. Five elements and M-only bounds are not valid forms.
- `epoch` is an optional decimal year for a dynamic CRS and applies per column,
  not per geometry.

A metadata bbox must contain every row-group native extent. Missing native
statistics leave the strict conformance gate unverified.

## Version boundary

GeoParquet 1.1 compatibility commonly means WKB `BYTE_ARRAY` plus legacy `geo`
metadata and a bbox covering. It can be an appropriate older-reader target,
but it is not GeoParquet 2.0 without native geometry logical types. Native
logical types without the required `geo` block are also not self-described
GeoParquet 2.0. Keep the target version explicit.
