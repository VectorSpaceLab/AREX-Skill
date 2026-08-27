# Pagination and schema troubleshooting

## The response has `features`, but the schema has `results`

These are separate execution paths. `GeoJsonPagination.get_paginated_response`
controls the response, while `get_paginated_response_schema` controls the
OpenAPI fragment. Diagnose in this order:

1. Confirm the view actually uses `GeoJsonPagination`, not DRF's default
   `PageNumberPagination` or an unrelated subclass.
2. Confirm the schema generator is using `GeoFeatureAutoSchema` and that the
   pagination class is visible on the generated view.
3. Inspect schema `properties` and `required` separately. The implementation
   moves the inherited `results` property to `features`, but DRF version
   variation can leave `results` in `required` (observed with DRF 3.18).
4. If `results` remains a property, a custom pagination schema override or an
   ordinary DRF paginator is being used; fix that integration or normalize the
   OpenAPI document explicitly.

Never change a working response from `features` to `results` to hide a schema
configuration problem.

## Pagination raises a missing-key error or returns the wrong list

`GeoJsonPagination` indexes `data["features"]`. Common causes are:

- the child is `ModelSerializer(many=True)` instead of
  `GeoFeatureModelSerializer(many=True)`;
- a custom list serializer returned a bare list or used `results`;
- a custom serializer changed the FeatureCollection key;
- the endpoint was expected to paginate a single Feature rather than a list.

Inspect the serializer's unpaginated representation first. Adapt the serializer
boundary or use a paginator appropriate for that representation; do not add a
fallback that silently nests malformed data.

If `page_size` in the URL has no effect, verify that the paginator has a
configured `page_size` or a project default that enables pagination. The query
parameter is exactly `page_size`, not `limit` (an endpoint may intentionally
choose a different paginator, but that is no longer the GeoJsonPagination
contract).

## The schema is ordinary DRF instead of GeoJSON

A response can still be valid GeoJSON while OpenAPI remains an ordinary DRF
object if the schema class was not installed. Use either the global
`DEFAULT_SCHEMA_CLASS` setting or an explicit `GeoFeatureAutoSchema` on the
schema-generation path. Then regenerate the document rather than inspecting a
cached artifact.

For mixed APIs, prefer explicit schema selection for GIS endpoints. Check that
the schema view, not only the application REST setting, is using the intended
class.

## Geometry schema is empty or warns

An empty geometry mapping is intentional when inference is unsafe:

- `Meta.geo_field` is a `GeometrySerializerMethodField`; the mapper warns that
  method-field geometry generation is unsupported.
- the model field is a custom geometry class absent from the built-in mapping;
  the mapper warns and returns an empty mapping.
- the serializer's geometry name does not resolve to a model geometry field;
  verify the serializer/model contract before blaming OpenAPI.

Keep runtime and schema checks separate. A method can return a valid Point or a
null geometry at runtime even though the static schema is empty. If a stable
contract is required, add an application-level explicit schema override and
keep the warning/limitation documented.

A generic `GeometryField` is not a promise of every GeoJSON geometry in the
schema. The built-in mapping advertises a type string and a limited set of
coordinate alternatives. Verify Multi* or collection output with a concrete
field and schema override where necessary.

## Coordinate nesting looks off

Count the arrays from the coordinate number outward:

- Point: numbers;
- LineString: points;
- Polygon: rings of points;
- MultiPoint: points;
- MultiLineString: lines of points;
- MultiPolygon: polygons of rings of points.

Check that the runtime field's geometry type matches the model field class
being mapped. Also check GeoJSON order `(x, y)`—normally `(longitude,
latitude)`—and whether an optional third ordinate is present. Schema examples
and minimum lengths are descriptive; they do not transform SRIDs or validate
closed polygon rings.

If a coordinate transform is required, route field/runtime behavior to
`serialization`; the schema helper only describes the resulting structure.

## Nested or list schema is misplaced

`GeoFeatureModelSerializer(many=True)` creates a
`GeoFeatureModelListSerializer`, so the schema must contain:

```text
parent property
└── type: FeatureCollection
    └── features: array
        └── items: Feature schema
```

A single nested child has the Feature schema directly under its field. If a
parent schema instead exposes child fields as top-level geometry or turns a
nested FeatureCollection into `results`, inspect whether the child was created
with `many=True` and whether the active mapper is `GeoFeatureAutoSchema`.

Do not treat a normal DRF list field as a GeoFeature list; only the GIS list
serializer gets the FeatureCollection wrapper automatically.

## bbox is missing or duplicated

For runtime output, check exactly one of `Meta.auto_bbox` and
`Meta.bbox_geo_field`. The serializer rejects both together. `auto_bbox` uses
the feature geometry's extent; a separate bbox geometry uses that field's
extent. A null source can yield a null bbox at runtime.

For OpenAPI output, a configured bbox is a feature-level four-number array, and
a configured `bbox_geo_field` is removed from ordinary properties. If both a
feature bbox and a bbox geometry property appear, compare the serializer's
`Meta` configuration with the schema mapper's input serializer rather than
patching only the document.

A bbox on a geometry field's raw GeoJSON object and a feature-level bbox are
not interchangeable. Route raw field formatting to `serialization` and bbox
query parameters to `spatial-filtering`.

## Version or environment behavior differs

Check the package dependency window before attributing a change to the GIS
helpers: Django `>=4.2`, DRF `>=3.12,<3.19`, and django-filter `>=23.5,<26.0`.
The supported test matrix spans Django 4.2 through 6.1 and DRF 3.14 through
3.18; base DRF OpenAPI details can vary between those releases. Record the
actual versions in a verification report and compare required-list, nullable
URL, and nested-schema differences.

GeoDjango geometry imports and in-memory geometry smoke require GEOS and GDAL.
Database-backed spatial predicates require a spatial database. PostGIS is the
CI-tested full path, but this skill does not claim that PostGIS execution was
verified. Route database setup, migrations, endpoint integration, and native
spatial tests to `integration-testing`.

## Filter schema appears in the wrong place

`GeoFeatureAutoSchema` can participate in schema mapping for spatial filter
parameters, but filter runtime semantics—bbox containment/overlap, tile
conversion, distance units, and ordering—belong to `spatial-filtering`. If a
filter parameter is absent, verify the view's filter backend and field settings
first. Do not duplicate filter parsing rules in this pagination/schema skill.
