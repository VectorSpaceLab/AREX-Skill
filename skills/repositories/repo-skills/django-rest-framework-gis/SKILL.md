---
name: django-rest-framework-gis
description: "Guide Django REST Framework and GeoDjango projects through
  django-rest-framework-gis installation, GeoJSON serialization, spatial
  filtering, pagination, OpenAPI schema generation, and backend
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# django-rest-framework-gis

Use this repo skill when a Django REST Framework endpoint needs GeoDjango
geometry as GeoJSON, GeoJSON Features or FeatureCollections, spatial query
filters, GeoJSON pagination, or OpenAPI geometry schemas. It covers the public
`djangorestframework-gis` package, not a private application model or a
replacement for a spatial database.

## Install and smoke-check

Install the public distribution and its declared runtime dependencies:

```bash
python -m pip install djangorestframework-gis
python -c "import rest_framework_gis; print(rest_framework_gis.get_version())"
```

The package requires Django, Django REST Framework, `django-filter`, and
GeoDjango's native GEOS/GDAL/PROJ libraries for geometry operations. Add
`rest_framework_gis` to `INSTALLED_APPS` after `rest_framework` when you want
ordinary DRF `ModelSerializer` classes to map GeoDjango fields automatically.
Use [integration-testing](sub-skills/integration-testing/SKILL.md) for supported
version selection, native-library checks, and spatial-database boundaries.

For a no-database JSON diagnostic, run the bundled checker from the installed
skill tree:

```bash
python sub-skills/integration-testing/scripts/check_environment.py --help
python sub-skills/integration-testing/scripts/check_environment.py
```

## Route the task

- **GeoJSON geometry or Feature I/O:** read
  [serialization](sub-skills/serialization/SKILL.md). It owns `GeometryField`,
  `GeometrySerializerMethodField`, `GeoFeatureModelSerializer`, IDs,
  properties, bbox, SRID transforms, precision, deduplication, and null/empty
  behavior.
- **BBox, TMS tile, geometry, distance, or nearest/farthest queries:** read
  [spatial-filtering](sub-skills/spatial-filtering/SKILL.md). It owns DRF filter
  backends, query parameters, view attributes, units, SRIDs, and parse errors.
- **FeatureCollection pagination or OpenAPI:** read
  [pagination-and-schema](sub-skills/pagination-and-schema/SKILL.md). It owns
  `GeoJsonPagination`, `GeoFeatureAutoSchema`, geometry nesting, bbox schemas,
  and DRF version-specific schema behavior.
- **Installation, GeoDjango loaders, compatibility, test setup, or database
  verification:** read
  [integration-testing](sub-skills/integration-testing/SKILL.md). It separates
  package/GEOS/GDAL smoke from ORM and spatial-database evidence.

## Cross-cutting rules

1. Treat coordinates as GeoJSON `x,y` (longitude/easting, latitude/northing)
   and bbox values as west, south, east, north unless the application documents
   a different CRS.
2. `GeoFeatureModelSerializer` requires `Meta.geo_field`; use `None` explicitly
   for a geometry-less Feature. Choose one bbox mode: `auto_bbox` is read-only,
   while `bbox_geo_field` is writable and mutually exclusive with `auto_bbox`.
3. A GEOS/GDAL import or field serializer smoke does not prove that ORM
   predicates such as `dwithin`, `contained`, `bboverlaps`, or
   `GeometryDistance` work on the target database. Verify the actual spatial
   backend separately.
4. Read [references/troubleshooting.md](references/troubleshooting.md) for
   cross-cutting install, settings, native-library, dependency, and backend
   failures. Read [references/repo-provenance.md](references/repo-provenance.md)
   before deciding whether this skill matches a changed checkout.

## Scope boundary

This skill distills the package's public API and repository-tested behavior. It
does not include private environment paths, the original repository as a
runtime dependency, maintainer release automation, or the expensive 10,000-
object performance benchmark.
