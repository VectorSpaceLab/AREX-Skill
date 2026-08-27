# Focused verification

## Layer the checks

Run checks in this order so a database failure is not confused with an import or native-library failure:

1. **Distribution and dependency facts** — `python -m pip show ...` plus `scripts/check_environment.py`.
2. **Package/module imports** — import `rest_framework_gis`, its public integration modules, and representative GeoDjango classes without project settings.
3. **Geometry smoke** — parse a small WKT or GeoJSON point, inspect its type/SRID, and if transformations are part of the application, perform an explicit CRS transform.
4. **Django project setup** — configure `DJANGO_SETTINGS_MODULE`, call the project’s normal management command, and run `python manage.py check`.
5. **Database-backed integration** — migrate a disposable test database and exercise the intended serializer/view/filter path.

The first three layers do not establish database connectivity, spatial extension support, migrations, or query semantics.

## Safe no-database checks

After installing the public package, these checks are intentionally independent of application settings and database access:

```bash
python -c 'import rest_framework_gis; from rest_framework_gis.fields import GeometryField; from rest_framework_gis.serializers import GeoFeatureModelSerializer; print(rest_framework_gis.get_version(), GeometryField.__name__, GeoFeatureModelSerializer.__name__)'

python -c 'from django.contrib.gis.geos import GEOSGeometry; g = GEOSGeometry("POINT (12.5 41.9)"); assert g.geom_type == "Point"; print(g.srid, g.geom_type, g.geojson)'

python -c 'from django.contrib.gis import gdal; print({"version": gdal.GDAL_VERSION})'
```

Use the bundled checker instead of copying these probes into automation when a machine-readable report is useful. The import probe intentionally does not call `django.setup()`, so it also helps distinguish a package problem from a project-settings problem.

## Django test runner

Configure a test settings module that includes `django.contrib.gis`, `rest_framework`, `rest_framework_gis` in that order, and the application under test. Use a disposable spatial database and the project’s ordinary test command:

```bash
export DJANGO_SETTINGS_MODULE=your_project.settings
python manage.py check
python manage.py test your_project.tests.gis -v 2
```

For an integration slice, assert both API output and the database-backed behavior it depends on. Include invalid geometry/query parameters, SRID or transformation cases used by the project, null geometry behavior, and at least one boundary predicate. Use a query-count assertion only when the project has a stable intended query budget; do not rewrite a query count merely to make a test green.

For a PostGIS run, also verify the test database can be created and that the required extension is present through the project’s normal database setup. Do not substitute a plain SQLite backend for a spatial test.

## pytest-django

If the project uses pytest, install `pytest` and `pytest-django`, declare the settings module in the project’s supported configuration, and run a focused selection:

```bash
python -m pytest -q your_project/tests/test_gis.py
```

Use the project’s own settings and database fixture conventions. A pytest collection success only proves import/collection; require a test that reaches the configured spatial database before reporting ORM integration as passed.

## Backend-specific assertions

Prefer PostGIS for the complete contract. At minimum, a database-backed integration slice should cover:

- model creation and retrieval with a geometry field;
- GeoJSON serialization and deserialization through the project’s serializer;
- one invalid geometry response;
- the application’s spatial filter or bounding-box behavior;
- distance filtering and nearest-first distance ordering when those features are used;
- CRS/SRID transformation when the API promises it.

On SpatiaLite, keep serialization and supported geometry checks separate from unsupported distance/predicate checks. Mark `dwithin`, `GeometryDistance`, and `contains_properly` cases as skipped with a backend-specific reason when the backend lacks them; do not turn them into unconditional passes.

Synthetic case to retain: configure SpatiaLite, create two points at different distances from a query point, confirm serialization succeeds, then require the distance-ordering assertion to be skipped or routed to PostGIS. A test that only serializes the two points is insufficient.

Synthetic settings case to retain: import `rest_framework_gis` and `GeometryField` successfully, then attempt a project model/test without `DJANGO_SETTINGS_MODULE` or `django.setup()`. The first phase should pass; the second should fail with a settings/app-registry diagnosis rather than being mislabeled as a package import failure.

## Performance caveat

The historical performance document reports old averages from five measurements and does not provide a current Python 3.10–3.13, Django 4.2–6.1, GEOS/GDAL, or PostGIS baseline. Use any performance test only as a controlled comparison: keep dataset, backend, indexes, query plan, warm-up, and environment fixed, report variance, and do not treat an old timing as a support guarantee. Coordinate precision and duplicate-removal options can trade response size for extra geometry processing time.
