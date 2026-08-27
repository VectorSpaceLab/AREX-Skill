# Cross-cutting troubleshooting

Read this reference when a package or endpoint failure does not clearly belong
to one API route. Then follow the nearest sub-skill reference for the detailed
serializer, filter, pagination/schema, or environment contract.

## Import and settings failures

- `ModuleNotFoundError: rest_framework_gis`: install the public distribution in
the Python environment that runs Django, then verify with `python -c
"import rest_framework_gis"`.
- `ImproperlyConfigured: Requested setting REST_FRAMEWORK ... settings are not
configured`: import DRF-backed modules such as filters or schema only after
`DJANGO_SETTINGS_MODULE` is set or a project settings object is configured.
- Geometry modules fail while importing with a shared-library error: install
compatible GEOS and GDAL/PROJ libraries and ensure the process can load them.
The bundled `sub-skills/integration-testing/scripts/check_environment.py` checks
these native libraries without opening a database.
- Automatic geometry mapping is absent: put `rest_framework_gis` after
`rest_framework` in `INSTALLED_APPS`, complete `django.setup()`, and use an
explicit `GeometryField` when per-field options or independent app loading are
needed.

## Dependency and version drift

The source line represented by this skill documents Python 3.10–3.13, Django
4.2–6.1, DRF 3.12–3.18, and django-filter 23.5–25.x. The package metadata
requires Django >=4.2, DRF >=3.12,<3.19, and django-filter >=23.5,<26.0.
Resolve the project's actual versions before diagnosing behavior. If a schema
shape, import, or exception differs, record the package and native GIS library
versions rather than copying a message from a different matrix.

## GeoJSON and CRS failures

Use [serialization](../sub-skills/serialization/SKILL.md) for invalid input,
`geo_field`, bbox, ID, precision, duplicate, empty, null, method-field, and SRID
issues. A dict passed to `GeometryField.to_representation()` is already treated
as prepared output; use a GEOS geometry when field options must run.

Coordinates are not transformed merely because an API is GeoJSON. Configure an
explicit `transform` and assign a source SRID when a CRS conversion is needed.
Test transformed coordinates with tolerances and ensure PROJ data is available.

## Spatial-database failures

A successful GEOS/GDAL serializer check is not a database check. `InBBoxFilter`,
`TMSTileFilter`, `GeometryFilter`, distance filtering, distance ordering, model
saves, and spatial migrations need a supported spatial database and compatible
geometry columns. Prefer PostGIS for the complete path. SpatiaLite can be a
useful local partial alternative, but do not treat skipped `dwithin`,
`GeometryDistance`, or `contains_properly` tests as passes.

When a query returns no rows or a backend reports an unsupported operation,
check geometry SRIDs, coordinate order, database units, spatial indexes, the
lookup support of the backend, and the endpoint's field attributes. The
spatial-filtering and integration-testing references contain the exact query
parameters and backend decision points.

## Freshness

If the source commit, package metadata, public entry points, or dirty evidence
paths differ from [repo-provenance.md](repo-provenance.md), run the repository
skill refresh workflow before relying on detailed claims.
