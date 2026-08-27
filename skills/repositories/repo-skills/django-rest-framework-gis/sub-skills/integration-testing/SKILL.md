---
name: integration-testing
description: "Install and verify django-rest-framework-gis with GeoDjango,
  native geospatial libraries, and an appropriate spatial database."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Integration testing

Use this sub-skill when a project needs a safe installation check, GeoDjango/native-library diagnosis, a compatible Django/DRF matrix, or focused integration verification for `djangorestframework-gis`.

## Route here for

- Installing the public `djangorestframework-gis` distribution and its declared Python dependencies.
- Choosing a supported Python/Django/DRF/django-filter combination.
- Checking package imports separately from GEOS, GDAL, PROJ, and spatial-database readiness.
- Configuring `INSTALLED_APPS`, a PostGIS test database, or the deliberately partial SpatiaLite alternative.
- Running focused Django or pytest checks and interpreting database-dependent failures.
- Using [`scripts/check_environment.py`](scripts/check_environment.py) for a no-database, no-network JSON environment report.

## Do not handle here

- Serializer, field, filter, pagination, schema, tile-name, or GeoJSON API recipes: route to the corresponding API sub-skill.
- Designing application models, URLs, views, or endpoint contracts: route to the relevant API sub-skill.
- Claiming that a spatial database is healthy from Python imports alone.

## Operating workflow

1. Create or select an isolated environment and install the public package. Confirm the resolver selected versions within the declared ranges; do not silently mix an old DRF-gis release with a newer compatibility claim.
2. Select a supported matrix from [environment](references/environment.md). For the current 1.3.x line, Python 3.10–3.13, Django 4.2–6.1, DRF 3.12–3.18, and django-filter 23.5–25.x are the documented ranges; the package declares `django>=4.2`, `djangorestframework>=3.12,<3.19`, and `django-filter>=23.5,<26.0`.
3. Run the bundled environment checker before loading project settings. It checks imports and native GEOS/GDAL/PROJ capabilities without opening a database or network connection.
4. Add `rest_framework_gis` after `rest_framework` in `INSTALLED_APPS`, then run the project’s normal Django system check. Package imports can pass even when settings, app registration, or model loading is broken.
5. Choose PostGIS for the complete spatial test path. Use SpatiaLite only when its explicitly documented feature gaps are acceptable, and mark unsupported tests as skips rather than treating them as passes.
6. Run focused Django/pytest tests with the project’s configured settings and spatial database. Separate serialization/geometry smoke results from ORM predicate, distance, migration, and query-plan results.
7. If diagnosing a failure, use [troubleshooting](references/troubleshooting.md). Record the exact Python, Django, DRF, django-filter, GEOS, GDAL, PROJ, backend, and database evidence.

## Verification boundary

The maintainer CI path uses a PostGIS service and a broad compatibility matrix, which is evidence for the intended full test path. Current production inspection established Python 3.12 with Django 6.1, DRF 3.18.0, django-filter 25.2, GDAL 3.13.3, and GEOS 3.14.1 package/module imports and geometry smoke. It did **not** establish a live PostGIS execution result. Never report PostGIS integration as verified unless the target project actually connects to PostGIS and completes a focused database test.

Start with [environment](references/environment.md), then use [testing](references/testing.md) for reproducible checks and [troubleshooting](references/troubleshooting.md) for failures.
