---
name: pagination-and-schema
description: "Shape GeoJSON pagination responses and OpenAPI schemas with
  GeoJsonPagination and GeoFeatureAutoSchema, including geometry, bbox, nested,
  and list serializers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Pagination and schema

Load this skill when a DRF GIS endpoint needs a paginated GeoJSON response, an
OpenAPI description of a GeoJSON feature, or schema troubleshooting for nested
or computed geometries. Keep the wire payload and the generated OpenAPI schema
as two separate contracts; a correct response does not prove that the schema is
correct.

## Operating path

1. Identify the serializer at the endpoint boundary and whether DRF is
   serializing one object, `many=True`, or a nested/list field.
2. For a paginated feature list, subclass or configure
   `rest_framework_gis.pagination.GeoJsonPagination`. It is a
   `PageNumberPagination` subclass, accepts `page_size` as its page-size query
   parameter, and expects the serialized page data to contain `features`.
   Confirm the response has `type`, `count`, `next`, `previous`, and
   `features`; do not substitute DRF's ordinary `results` payload.
3. For OpenAPI, configure
   `rest_framework_gis.schema.GeoFeatureAutoSchema` as DRF's schema class, or
   pass it explicitly to the schema generator. Verify the generated document
   independently of a live response. The pagination schema renames the
   inherited `results` property to `features` and adds the
   `FeatureCollection` type property; inspect version-specific `required`
   metadata as well.
4. Use the geometry and nesting rules in `references/api-reference.md` rather
   than copying large coordinate schemas into an endpoint skill. Treat a
   `GeometrySerializerMethodField` used as the geometry source, or an
   unsupported custom geometry field, as an explicit schema limitation: the
   mapper warns and returns an empty geometry schema.
5. Route serializer `Meta` options, GeoJSON input flattening, output property
   ownership, and coordinate transformation details to `serialization`.
   Route runtime spatial filters and their query semantics to
   `spatial-filtering`. Route Django/DRF settings, schema endpoint wiring, and
   database-backed integration checks to `integration-testing`.

## Verification contract

Check both artifacts:

- Serialize representative objects and assert the actual Feature or
  FeatureCollection envelope, including bbox when configured.
- Generate OpenAPI with the same serializer/view and assert the geometry type,
  coordinate nesting, Feature/FeatureCollection wrappers, bbox, nested/list
  placement, and pagination property names.
- Run the method-field and unsupported-custom-field cases while capturing the
  expected warning; an empty schema is safer than inventing a geometry shape.
- Record the DRF version because schema base output varies across supported
  DRF versions (the package supports `>=3.12,<3.19`).

The documented inspection scope has verified package imports and geometry smoke
with GeoDjango's GEOS/GDAL libraries. Database-backed spatial predicates require
a spatial database; PostGIS is the CI-tested full path, but PostGIS execution
is not claimed by this skill.

See:

- [API reference](references/api-reference.md) for payload keys, schema shapes,
  geometry nesting, bbox, and version notes.
- [Workflows](references/workflows.md) for endpoint setup and paired response /
  schema checks.
- [Troubleshooting](references/troubleshooting.md) for schema drift, warnings,
  nested serializers, and backend limits.
