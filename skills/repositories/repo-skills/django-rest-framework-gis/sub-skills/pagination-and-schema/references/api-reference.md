# Pagination and schema API reference

This reference describes the public behavior of the pagination and schema
helpers. It intentionally separates the serialized response from the OpenAPI
mapping of that response.

## Public entry points

| Component | Role | Important behavior |
| --- | --- | --- |
| `rest_framework_gis.pagination.GeoJsonPagination` | Page-number pagination for GeoJSON feature lists | Extends DRF `PageNumberPagination`; uses `page_size` as `page_size_query_param`; consumes `data["features"]`. |
| `rest_framework_gis.schema.GeoFeatureAutoSchema` | OpenAPI mapping for GIS fields and GeoFeature serializers | Extends DRF `AutoSchema`; maps geometry objects, Feature/FeatureCollection envelopes, and bbox. |
| `rest_framework_gis.serializers.GeoFeatureModelSerializer` | Feature representation and input flattening | The serializer owns the feature envelope; see the `serialization` skill for full `Meta` and input/output rules. |
| `rest_framework_gis.serializers.GeoFeatureModelListSerializer` | List representation for `GeoFeatureModelSerializer(many=True)` | Wraps the list as a FeatureCollection before pagination or schema mapping. |

## Response payloads

### One feature

A `GeoFeatureModelSerializer` instance produces a GeoJSON Feature-like object:

```json
{
  "id": 1,
  "type": "Feature",
  "geometry": {
    "type": "Point",
    "coordinates": [12.9721, 77.5933]
  },
  "properties": {
    "name": "example"
  }
}
```

`id` is present when `Meta.id_field` selects a field. `geometry` is `null`
when the serializer is configured with no geometry source. `bbox` is present
when `Meta.auto_bbox` or `Meta.bbox_geo_field` is configured. Serializer field
selection, GeoJSON input flattening, and custom `properties` behavior belong to
`serialization`.

### A feature list

`GeoFeatureModelSerializer(many=True)` uses
`GeoFeatureModelListSerializer`, whose representation is:

```json
{
  "type": "FeatureCollection",
  "features": [
    {"type": "Feature", "geometry": {}, "properties": {}}
  ]
}
```

A nested `many=True` field has this same envelope at the nested field name; it
is not flattened into the parent feature's `properties` object.

### A paginated feature list

`GeoJsonPagination.get_paginated_response(data)` returns a DRF `Response` with
this outer shape:

```json
{
  "type": "FeatureCollection",
  "count": 25,
  "next": "https://api.example.test/locations/?page=2",
  "previous": null,
  "features": [
    {"type": "Feature", "geometry": {}, "properties": {}}
  ]
}
```

The `features` value is copied from `data["features"]`; it is not copied from
`data["results"]` and it is not the entire FeatureCollection object. Pair this
paginator with a GeoFeature serializer whose page representation contains
`features`. A regular DRF `ModelSerializer(many=True)` or a custom list
serializer that returns only a bare list does not satisfy that input contract
without an adapter.

`page_size_query_param` is exactly `page_size`. A configured `page_size` is
needed for pagination to activate, and DRF's normal `max_page_size` and page
number rules still apply when configured. `next` and `previous` are generated
by DRF and can be `null`.

## OpenAPI schema mapping

`GeoFeatureAutoSchema` is a schema mapper, not a response renderer. It does
not alter runtime data. Configure it globally with the DRF setting:

```python
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS":
        "rest_framework_gis.schema.GeoFeatureAutoSchema",
}
```

Alternatively, pass the class explicitly to the DRF schema-view or schema
command integration. The integration-testing skill owns project-specific
settings and schema endpoint checks.

### Feature and FeatureCollection envelopes

For a `GeoFeatureModelSerializer`, the mapper builds an object with:

- `type`: a string enum containing `Feature`;
- `id`: moved out of the ordinary serializer properties when `id_field` is
  enabled;
- `geometry`: an object whose `properties` describe the selected geometry
  field;
- `bbox`: a four-number array when `auto_bbox` or `bbox_geo_field` is enabled;
- `properties`: the remaining serializer schema.

For `GeoFeatureModelListSerializer`, the mapper builds an object with a
`type` enum containing `FeatureCollection` and a `features` array whose
`items` schema is the mapped child serializer.

The FeatureCollection schema is also what a nested `GeoFeatureModelSerializer`
with `many=True` should expose under its parent field. A nested single feature
is mapped as a Feature object under its parent field instead.

The runtime serializer permits `Meta.geo_field = None` and emits
`"geometry": null`, but the current feature-schema mapping path expects a
model geometry name when it builds the geometry property. Treat schema support
for geometry-less Feature serializers as an explicit verification gap and use
an application schema override if that endpoint needs a published OpenAPI
contract.

### Geometry coordinate nesting

The mapper's built-in model-field mapping has these shapes. In the table,
`P` means a coordinate pair/triplet array and `L` means an array of `P` values.
The schema includes examples, `minItems`, and `maxItems` in several levels; use
those details as documentation hints, not as a substitute for GeoJSON
validation.

| GeoDjango field | GeoJSON `type` | Coordinate structure | Notes |
| --- | --- | --- | --- |
| `PointField` | `Point` | `P = [number, number]` or `[number, number, number]` | `minItems=2`, `maxItems=3`. |
| `LineStringField` | `LineString` | `L = [P, P, ...]` | At least two points. |
| `PolygonField` | `Polygon` | `[L, L, ...]` | The ring item is described with at least four points. |
| `MultiPointField` | `MultiPoint` | `[P, P, ...]` | The item schema is the Point coordinate schema. |
| `MultiLineStringField` | `MultiLineString` | `[L, L, ...]` | Each item is a LineString coordinate schema. |
| `MultiPolygonField` | `MultiPolygon` | `[[L, L, ...], ...]` | Each item is a Polygon coordinate schema. |
| `GeometryField` | unrestricted string in the mapper | `oneOf` the Point, LineString, or Polygon coordinate schemas | This generic mapping is intentionally narrower than every possible GeoJSON geometry. Verify any multi or collection geometry instead of assuming it is covered. |

The coordinate order remains GeoJSON `(x, y)`—normally `(longitude,
latitude)`—and an optional third value is permitted by the Point schema. The
schema does not perform coordinate or SRID transformation; those are runtime
field concerns owned by `serialization`.

The implementation also constructs a mapping for the GeoDjango
`GeometryCollectionField`, but custom geometry subclasses are not inferred by
name or by runtime output. An unmapped model geometry class generates a warning
and an empty schema for that geometry mapping.

### Bounding boxes

When a feature serializer uses `auto_bbox` or `bbox_geo_field`, the schema
adds:

```json
{
  "type": "array",
  "items": {"type": "number"},
  "minItems": 4,
  "maxItems": 4,
  "example": [12.9721, 77.5933, 12.9721, 77.5933]
}
```

The `bbox_geo_field` is removed from the normal `properties` schema because it
is represented by the feature-level `bbox`. Runtime output uses the geometry's
extent; writable bbox input is converted to a polygon by the serializer. Do
not confuse this feature bbox with an `in_bbox` query parameter; spatial filter
schema and execution belong to `spatial-filtering`.

## Unsupported and computed geometry

When `Meta.geo_field` points to a `GeometrySerializerMethodField`, the mapper
cannot inspect a model field or infer the returned geometry class. It emits a
warning with the message that generation for
`GeometrySerializerMethodField` is not supported and returns `{}` for the
geometry properties. Capture this warning in tests and preserve the empty
schema unless an explicit custom schema is supplied elsewhere.

A model geometry field whose concrete class is not in the built-in mapping is
handled similarly: the mapper warns that geometry generation is unsupported
and returns an empty mapping. This is different from runtime serialization,
which may still produce valid GeoJSON through the field; validate response and
schema separately.

## DRF version variation

Schema generation is supported for DRF `>=3.12`; package requirements cap DRF
below `3.19`. The CI matrix covers DRF 3.14 through 3.18 across supported
Django versions, including Django 6.1 with DRF 3.18.0 in the inspected
environment.

`GeoJsonPagination.get_paginated_response_schema()` starts with DRF's base
pagination schema, moves the `results` property to `features`, and prepends the
`FeatureCollection` type property. The base schema's shape and required-list
behavior vary by DRF. In the observed DRF 3.18 behavior, the property is
renamed but the inherited `required` list can still contain `results`; the
repository test explicitly accounts for this. Treat a stale required entry as
schema drift to report or normalize in an application-level schema layer, not
as evidence that the runtime payload uses `results`.
