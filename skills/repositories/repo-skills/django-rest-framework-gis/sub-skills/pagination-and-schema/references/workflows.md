# Pagination and schema workflows

These workflows keep response assertions and schema assertions separate. Use
an in-process DRF request/schema generator in the host project; project setup
and database-backed checks belong to `integration-testing`.

## 1. Establish the serializer-to-paginator contract

1. Choose a `GeoFeatureModelSerializer` for the endpoint and make sure its
   `many=True` representation is a FeatureCollection with a `features` key.
2. Subclass `GeoJsonPagination` only when endpoint-specific page sizing is
   needed. Keep `page_size_query_param = "page_size"`; configure `page_size`
   and, if needed, `max_page_size` using normal DRF pagination settings.
3. Set the view's `pagination_class` to that paginator.
4. Exercise an unfiltered first page and a later page. Assert the runtime keys
   exactly: `type`, `count`, `next`, `previous`, `features`.
5. Exercise an empty queryset and assert that the response still has a
   FeatureCollection envelope and an empty `features` list. Do not infer the
   schema from this response.
6. If `get_paginated_response` raises a missing-`features` error, inspect the
   serializer's page representation before changing the paginator. A plain
   DRF list serializer does not provide the required key.

The paginator is a response adapter around the child serializer. It does not
turn arbitrary ordinary results into GeoJSON features.

## 2. Configure and generate the GeoFeature schema

Use the global setting when all API schemas are GIS-oriented:

```python
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS":
        "rest_framework_gis.schema.GeoFeatureAutoSchema",
}
```

For a mixed API, leave the global default alone and pass
`GeoFeatureAutoSchema` explicitly to the schema-view or schema command path.
Then:

1. Generate the schema for a single-feature endpoint and inspect the Feature
   envelope, selected `id`, geometry object, and properties.
2. Generate it for a `many=True` endpoint and inspect the FeatureCollection
   wrapper and `features.items` child schema.
3. Generate it for a paginated endpoint and verify that the pagination schema's
   properties include `features`, not `results`, plus the FeatureCollection
   type enum.
4. Inspect the `required` list separately. DRF versions can retain an inherited
   `results` entry after the property is renamed; do not silently claim that
   the response has a `results` key.
5. Compare the generated schema with the actual response from the same view.

The schema mapper can describe the known GeoDjango geometry field classes, but
it cannot infer arbitrary method-field or custom geometry output. Keep those
limitations visible in the generated contract.

## 3. Cover geometry and bbox variants

For each selected model geometry field, generate a schema and assert the
GeoJSON type and nesting level from the API reference:

- Point: coordinate numbers;
- LineString: an array of points;
- Polygon: an array of linear rings;
- MultiPoint: an array of points;
- MultiLineString: an array of line strings;
- MultiPolygon: an array of polygons;
- generic Geometry: the mapper's documented `oneOf` coordinate alternatives.

At runtime, serialize a representative geometry of the same class and compare
its envelope with the schema. Include a 2D and, where supported by the model,
a 3D point to check the `minItems=2`, `maxItems=3` boundary.

For bbox coverage, use one serializer with `auto_bbox=True` and one with a
separate `bbox_geo_field`:

- response: assert a four-number feature-level `bbox`;
- schema: assert the four-number bbox array and absence of the bbox geometry
  field from ordinary feature properties;
- input path for a writable bbox field: route detailed flattening and polygon
  conversion assertions to `serialization`.

Do not use a bbox query parameter test as a substitute for feature bbox
coverage; route query filter behavior to `spatial-filtering`.

## 4. Verify nested and list serializers

Build two parent serializers around a known GeoFeature serializer:

```python
class ParentSerializer(serializers.Serializer):
    point = PointFeatureSerializer()
    points = PointFeatureSerializer(many=True)
```

For runtime output, assert that `point` is a nested Feature and `points` is a
nested FeatureCollection with its own `features` list. For the schema, map the
parent and assert the same wrappers appear under the corresponding parent
properties. The child geometry schema must remain beneath `geometry.properties`
and must not be mistaken for a top-level parent geometry.

If the parent contains ordinary DRF list or method fields alongside GIS
children, inspect each field independently. A nested list envelope does not
make unrelated fields geographic.

## 5. Handle method fields and custom geometry safely

For a `GeometrySerializerMethodField` used as `Meta.geo_field`:

1. Generate the serializer schema while capturing warnings.
2. Assert one unsupported-generation warning.
3. Assert the mapped geometry properties are empty rather than an invented
   Point/LineString/Polygon shape.
4. Separately serialize an object and assert the method's actual GeoJSON output
   (or `null`) using the `serialization` contract.

Repeat with a custom `GeometryField` subclass that is not one of the built-in
model field classes. The expected schema result is the same warning/empty
mapping unless the application provides its own explicit OpenAPI override.

For a nested/list parent containing one method-field child, check both that the
FeatureCollection wrapper remains present and that the warning/empty child
geometry schema is nested in the correct location.

## 6. Version-aware acceptance pass

Record the installed DRF version and compare against `>=3.12,<3.19`. Run the
same paired checks at the versions supported by the application rather than
assuming the newest base `AutoSchema` shape. In particular, check:

- pagination `required` entries after `results` → `features` renaming;
- nullable/URI details for `next` and `previous`;
- nested serializer mapping and list child shape;
- warning behavior for unsupported geometry.

If a project needs a normalized OpenAPI document across DRF versions, apply the
normalization in its schema integration layer and document it; do not change
runtime response keys to satisfy a schema artifact.

## Difficult synthetic usability cases

1. **Features response, stale results schema:** Configure a view with
   `GeoJsonPagination` and a GeoFeature list serializer. Assert the response
   has `features` and no `results`, then deliberately obtain the pagination
   schema through a generator path that uses ordinary DRF pagination or a
   custom override. The test must detect `results` in schema properties or in
   `required`, identify the generator/configuration mismatch, and not “fix” the
   response payload.
2. **Nested list plus computed geometry:** Create a parent serializer with a
   GeoFeature child using `many=True` and a child whose `Meta.geo_field` is a
   `GeometrySerializerMethodField`. Assert the runtime nested FeatureCollection
   and method-generated geometry, then assert the schema keeps the nested
   `features.items` wrapper, emits the expected warning, and leaves that child
   geometry schema empty.
