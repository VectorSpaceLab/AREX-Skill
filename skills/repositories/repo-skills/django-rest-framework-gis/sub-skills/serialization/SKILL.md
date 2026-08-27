---
name: serialization
description: "Serialize GeoDjango geometries and model instances as
  GeoJSON-compatible Geometry, Feature, or FeatureCollection data with validated
  input, IDs, properties, bboxes, precision, deduplication, transforms, and
  automatic field mapping."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Serialization

Use this skill when a DRF endpoint must read or write GeoJSON geometry values or
emit GeoJSON `Feature` / `FeatureCollection` objects. Start with
[references/api-reference.md](references/api-reference.md) for exact public
names, defaults, output shape, and validation messages. Use
[references/workflows.md](references/workflows.md) for complete serializer
recipes and [references/troubleshooting.md](references/troubleshooting.md) when
GeoDjango, geometry parsing, SRIDs, fields, or null/empty values fail.

## Route the request

- Use `GeometryField` for a model geometry field or a plain serializer geometry
  value. Configure `precision`, `remove_duplicates`, `auto_bbox`, and
  `transform` only when the representation needs them.
- Use `GeometrySerializerMethodField` when a serializer method computes the
  geometry. Return a `GEOSGeometry` or `None`.
- Use `GeoFeatureModelSerializer` for one GeoJSON `Feature`; pass `many=True`
  for a `FeatureCollection`. Set `Meta.geo_field` explicitly, including
  `None` for a geometry-less model, and choose `id_field`, properties, and bbox
  behavior deliberately.
- Use `get_properties()` and `unformat_geojson()` together when the GeoJSON
  `properties` object is not the model's ordinary serializer fields.
- Put query predicates in [spatial-filtering](../spatial-filtering/SKILL.md),
  pagination and OpenAPI behavior in
  [pagination-and-schema](../pagination-and-schema/SKILL.md), and database,
  native-test, and backend setup in
  [integration-testing](../integration-testing/SKILL.md).

## Operating sequence

1. Install `rest_framework_gis` after `rest_framework` in
   `INSTALLED_APPS` so its app config registers GeoDjango fields with DRF's
   `ModelSerializer` mapping. An explicitly declared `GeometryField` works
   without relying on automatic mapping.
2. For plain geometry input, accept a GeoJSON dictionary, WKT/EWKT/HEXEWKB
   string, or `GEOSGeometry`; send a JSON string when a multipart form cannot
   carry a nested dictionary.
3. For feature input, send `properties` plus optional `geometry`, `id`, and
   writable `bbox`. A partial update may omit `geometry`; DRF then retains the
   instance value.
4. Verify output as JSON-compatible data and test SRID transforms and spatial
   database behavior in the target environment. GEOS parsing alone does not
   prove ORM or PostGIS execution.

The deterministic, database-free smoke check is linked from
[references/workflows.md](references/workflows.md). From the runtime skill root,
run:

```bash
python sub-skills/serialization/scripts/geometry_smoke.py --help
python sub-skills/serialization/scripts/geometry_smoke.py
```
