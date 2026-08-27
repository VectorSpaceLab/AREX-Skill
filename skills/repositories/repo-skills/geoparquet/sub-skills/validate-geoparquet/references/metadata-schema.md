# Local `geo` metadata schema

The GeoParquet 2.0 metadata object is validated locally by
[`../scripts/validate_geo_metadata.py`](../scripts/validate_geo_metadata.py).
The helper embeds the 2.0 field shape and never fetches a schema or authority
registry.

## Required shape

```json
{
  "version": "2.0.0",
  "primary_column": "geometry",
  "columns": {
    "geometry": {
      "encoding": "WKB",
      "geometry_types": []
    }
  }
}
```

`version` is exactly `2.0.0`; `primary_column` is a non-empty string; and
`columns` has at least one non-empty key. The primary column must be present in
`columns` as an additional semantic check. Every column object requires
`encoding: "WKB"` and an array `geometry_types`. File-level implementation
fields and column-level implementation fields may be retained for forward
compatibility; the `columns` object itself must not contain unrecognized
non-column entries.

The geometry-type expression is:

```text
^(GeometryCollection|(Multi)?(Point|LineString|Polygon))( Z| M| ZM)?$
```

The array may be empty, but entries must be unique. `Point Z` is valid and
`PointZ` is not. `bbox` accepts exactly 4, 6, or 8 finite JSON numbers. `edges`,
`orientation`, and `epoch` are checked against the rules in
[`vector-spec.md`](vector-spec.md).

## CRS validation boundary

The published schema describes a non-null `crs` through an external PROJJSON
schema. The local helper intentionally does not resolve that reference. It
checks the safe local contract: the value is either `null` or an object with a
string `type`; an authority string in GeoParquet column metadata is rejected.
A full PROJJSON schema check and equivalence with the native logical-type CRS
remain separately recorded observations, not implied by a local pass.

The native Parquet CRS forms are different: inline PROJJSON, an authority code,
`srid:<identifier>`, or `projjson:<key_name>` are allowed according to the
Parquet geospatial type rules. Put the resolved inline object (or `null` for
`srid:0`) in `geo.columns[*].crs` when the `geo` block is emitted.

## Example decisions

Valid minimal metadata:

```json
{"version":"2.0.0","primary_column":"geometry","columns":{"geometry":{"encoding":"WKB","geometry_types":[]}}}
```

This must fail locally:

```json
{
  "version":"2.0.0",
  "primary_column":"geometry",
  "columns":{"geometry":{
    "encoding":"WKB",
    "geometry_types":["PointZ","Point"],
    "bbox":[0,0,1,2,3]
  }}
}
```

`PointZ` has the wrong dimension spelling and the five-element bbox is never
legal. Add a repeated type such as a second `Point` to exercise the uniqueness
failure. `crs: "EPSG:4326"` is also invalid in this metadata object, even
though `EPSG:4326` may be a valid native Parquet logical-type CRS form.
