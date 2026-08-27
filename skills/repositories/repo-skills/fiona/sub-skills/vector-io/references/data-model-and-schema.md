# Fiona data model and schema

Fiona presents OGR features through GeoJSON-like mappings. A feature has an
identifier, one geometry, and a property mapping. A collection's schema has:

```python
{
    "geometry": "Point",                 # or Polygon, MultiPolygon, etc.
    "properties": {"name": "str:80", "count": "int"},
}
```

A list of `(field, type)` pairs preserves an intentional property order. Common
field names are `int32`, `int64`/`int`, `float`, `str`, `bytes`, `date`, `time`,
`datetime`, `List[str]`, and `json`, with optional width/precision suffixes for
driver-specific storage. Fiona normalizes width-bearing `int`, `str`, and
`float` declarations for type checks; a target driver may still impose narrower
limits.

## Validation sequence

1. Inspect `src.schema`, `src.crs`, and `src.driver` before choosing an output.
2. Choose a target driver whose write mode is listed by `fiona.supported_drivers`.
3. Define the output geometry type and properties explicitly.
4. Convert `None`, dates, bytes, and numeric values to values accepted by the
   target field type.
5. Write one tiny feature first and reopen the result to inspect `schema`,
   `crs`, `bounds`, and a representative feature.
6. Only then stream the full collection.

A schema mismatch commonly appears as `SchemaError`, `ValueError`, a driver
error, or a field silently becoming a string. Treat silent conversion as a
compatibility defect and verify the reopened schema.

## Geometry boundaries

Fiona stores coordinates and metadata but does not provide buffering,
intersection, centroid, validity repair, or general geometry algorithms. Use a
separate geometry library for those operations, convert the result back to a
GeoJSON-like mapping, and keep CRS conversion in the `crs-transform` route.

## Round-trip checks

A useful round trip checks more than file existence:

```python
with fiona.open("out.gpkg", layer="points") as check:
    assert check.driver == "GPKG"
    assert check.schema["geometry"] == "Point"
    assert check.crs is not None
    rows = list(check)
    assert all("properties" in row and "geometry" in row for row in rows)
```

Some drivers expose IDs, field widths, or CRS text differently after a write.
Compare semantic values and record any driver-specific normalization.
