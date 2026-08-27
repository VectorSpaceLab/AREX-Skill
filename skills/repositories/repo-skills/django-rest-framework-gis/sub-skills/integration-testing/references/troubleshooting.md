# Troubleshooting

Diagnose failures by layer. Keep the command, versions, backend, and complete exception class in the integration report.

## Package and Python dependency failures

- **`ModuleNotFoundError: rest_framework_gis`**: the public distribution is not installed in the active environment, or the interpreter running the command is not the one where it was installed. Re-run `python -m pip install djangorestframework-gis`, then `python -m pip show djangorestframework-gis` and the checker with the same `python` command.
- **DRF or django-filter import failure**: install the declared runtime dependencies and let the resolver select versions within `djangorestframework>=3.12,<3.19` and `django-filter>=23.5,<26.0`. Do not fix an upper-bound failure by ignoring package metadata.
- **Import succeeds but a symbol is missing**: check the installed distribution version and consult the API sub-skill for the version-appropriate public surface. Do not infer that a feature in another major/minor revision exists here.

## Settings and app-registry failures

- **`ImproperlyConfigured` or “settings are not configured” after a package import**: this is a project setup failure if the package/module import itself passed. Set the project’s `DJANGO_SETTINGS_MODULE`, run the project’s normal management command, and ensure `django.setup()` is reached before importing models or constructing model serializers.
- **App registry or model mapping errors**: confirm `rest_framework` precedes `rest_framework_gis` in `INSTALLED_APPS`, include `django.contrib.gis` when the project uses GeoDjango models, and avoid importing models before Django setup. The package’s app config updates DRF serializer mappings during `ready()`.
- **`No installed app with label ...` or migration errors**: verify the project app is installed and use the project’s migration/test settings. This is not fixed by reinstalling the wheel.

## GEOS, GDAL, and PROJ failures

- **GEOS shared-library/load error**: install a compatible GEOS runtime and development package using the operating system’s supported mechanism; check loader paths and architecture. Re-run the checker. A successful `import rest_framework_gis` without a GEOS geometry probe is not enough.
- **GDAL load error or `HAS_GDAL` false**: install the GDAL runtime/bindings expected by the Django version and verify that the process can load them. The checker reports GDAL facts but does not repair system libraries.
- **CRS construction or transform failure**: treat it as a GDAL/PROJ/CRS-data issue. Confirm PROJ data is discoverable, the source and target SRS are valid, and the geometry has the intended SRID. A geometry parse smoke test does not prove a coordinate transform.
- **Symbol/version mismatch**: GEOS, GDAL, and PROJ libraries from different packaging channels may be ABI-incompatible. Prefer one coherent OS/container distribution and compare the checker’s reported versions before changing application code.

## Database and backend failures

- **Package imports and geometry smoke pass, but `OperationalError` occurs**: distinguish the database layer. Check engine, host, port, credentials, service readiness, test-database permissions, and migrations; then retry a minimal project database test.
- **PostGIS extension or spatial function error**: verify that the server is PostGIS-enabled and that the test database has the extension and supported version. The CI service definition is a reference to the full path, not evidence that an arbitrary server is equivalent. Current production contains no PostGIS execution evidence.
- **Plain SQLite/SQLite backend errors**: a non-spatial SQLite backend cannot validate GeoDjango ORM behavior. Use PostGIS or the explicitly configured SpatiaLite backend for database tests.
- **SpatiaLite serialization passes but distance ordering fails**: this is an expected backend distinction when `GeometryDistance` is unavailable. Keep serialization tests, skip or route distance ordering to PostGIS, and report the backend-specific limitation instead of changing expected order or silently passing the case.
- **SpatiaLite `dwithin` or `contains_properly` failure**: these capabilities are not part of the supported SpatiaLite path. Skip with a reason or run the case on PostGIS. Do not report a skipped predicate as verified.
- **Spatial results differ by backend**: compare SRIDs, units, geometry validity, precision, supported predicates, and query plans. Backend equivalence is not implied by identical serializer output.

## Test and performance failures

- **Django tests fail during collection**: first run the no-database import and checker layers, then inspect settings and pytest-django configuration. Collection success alone is not database verification.
- **Only a broad suite fails**: isolate the smallest test module and one backend. Preserve the first meaningful exception; do not mask it with retries or broad skips.
- **Performance regression is suspected**: rerun with fixed data, indexes, spatial backend, warm-up, and repetitions. The historical five-sample timings are not a current baseline, and geometry precision/deduplication can intentionally add processing cost.

## Maintainer command boundary

A project may provide a QA wrapper for formatting, documentation, or static checks. Treat it as maintainer automation, not as a public package CLI and not as proof of spatial-database integration. For an installed application, use `pip`, the environment checker, `manage.py`, pytest, and the project’s documented database setup.
