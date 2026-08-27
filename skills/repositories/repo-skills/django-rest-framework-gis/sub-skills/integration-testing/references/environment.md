# Installation and runtime environment

## Public installation

Install the published distribution into an isolated environment with the project’s supported Python interpreter:

```bash
python -m pip install --upgrade pip
python -m pip install djangorestframework-gis
```

The package’s declared runtime requirements are:

```text
Django>=4.2
djangorestframework>=3.12,<3.19
django-filter>=23.5,<26.0
```

For a prerelease or a source revision, use an explicit version or artifact selected by the maintainer rather than assuming that the public stable install is the same revision. Confirm the result with `python -m pip show djangorestframework-gis` and the bundled checker. Do not install a database server or native GIS library from a Python package as a substitute for the system/runtime libraries described below.

## Compatibility selection

For the current 1.3.x line, the supported range is Python 3.10–3.13, Django 4.2–6.1, and DRF 3.12–3.18. The package metadata additionally constrains django-filter to `>=23.5,<26.0`; the current inspection baseline used django-filter 25.2. Select a conservative pair first (for example, Django 4.2 with a supported DRF release), then test the application’s intended upper bound. Django, DRF, django-filter, GDAL, GEOS, and the database backend are separate compatibility axes.

The inspected package revision was 1.3.0a0. On Python 3.12, imports and a geometry smoke check passed with Django 6.1, DRF 3.18.0, django-filter 25.2, GDAL 3.13.3, and GEOS 3.14.1. This is an import/geometry result only: no PostGIS runtime result was established in production.

## Django registration

Register the application after REST framework so its `AppConfig.ready()` mapping can replace DRF’s model-field mappings for GeoDjango fields:

```python
INSTALLED_APPS = [
    # Django applications, including django.contrib.gis where needed
    "rest_framework",
    "rest_framework_gis",
    # project applications
]
```

Call `django.setup()` through the project’s normal management command or test runner. A package import should not be used as proof that settings, app registration, migrations, or model discovery work.

## Native GIS prerequisites

GeoDjango loads native libraries through Django’s GIS bindings:

- **GEOS** is required for geometry parsing and operations. The checker constructs a point and reports the GEOS version exposed by Django.
- **GDAL** is required by GeoDjango’s GDAL bindings and for many raster/reference-system operations. The checker reports the GDAL capability/version exposed by Django.
- **PROJ** is needed for coordinate-reference-system and transformation work. Django does not expose a portable PROJ version API in all supported versions, so the checker probes construction of a 4326-to-3857 coordinate transform and reports the result rather than inventing a version.

Install native libraries using the operating system or container distribution’s supported packages. Keep GEOS/GDAL/PROJ from a compatible distribution; mixing library families can produce import-time symbol errors or transformation failures. The checker does not connect to a database, run migrations, or download anything.

Run it from any working directory by substituting the directory containing this skill:

```bash
python "$SKILL_DIR/scripts/check_environment.py"
```

It always emits JSON. A missing required Python/native dependency produces an actionable error and a non-zero status; use `--help` for options. It is safe to run before setting `DJANGO_SETTINGS_MODULE`.

## Spatial database choices

### PostGIS: complete path

Use the GeoDjango PostGIS backend for ORM spatial predicates, distance filters, distance ordering, and the closest match to the package’s maintainer-tested path. Maintainer CI provisions `postgis/postgis:17-3.5-alpine`, installs `binutils`, `libproj-dev`, and `gdal-bin`, exposes the database service on localhost, and runs a Django/DRF compatibility matrix. Reproduce the same capabilities in the target project’s own environment, then run its migrations and focused tests.

A generic project check after settings are configured is:

```bash
python manage.py check
python manage.py migrate --noinput
python manage.py test path.to.gis_tests -v 2
```

A service being present is not enough: verify the configured database engine, connection, PostGIS extension, test-database creation, and the actual query paths. Current production has no PostGIS execution evidence, so these commands are a procedure, not a claim that they were run successfully here.

Docker or Compose can be convenient for a disposable PostGIS service, but no Docker orchestration is required by this skill. An existing managed PostGIS service or a local installation is equally valid when its connection and extension are verified.

### SpatiaLite: partial alternative

SpatiaLite can support basic GeoDjango geometry storage, retrieval, and serialization when the SQLite extension is installed and Django is configured with `django.contrib.gis.db.backends.spatialite`. The exact library path is platform-specific; configure `SPATIALITE_LIBRARY_PATH` only when the platform does not discover it automatically.

Treat it as a partial verification backend. The supported integration behavior skips or qualifies these capabilities on SpatiaLite:

- `dwithin` distance filtering;
- `GeometryDistance` distance ordering;
- `contains_properly` geometry filtering.

Tile predicates may also be skipped where SpatiaLite accuracy is insufficient. A passing GeoJSON serialization test on SpatiaLite does not prove that distance ordering or all spatial predicates work. In particular, retain a PostGIS case for “two points at known distances, ordered nearest first”; it must not be downgraded to a serialization-only pass.

## Maintainer-only context

Maintainers may run a version matrix around these bounds when changing compatibility-sensitive code. A project QA wrapper may combine formatting, docs, and static checks, but it is not a public `djangorestframework-gis` CLI and should not be presented as an installation or runtime command. For an application integration report, prefer the public pip install, the bundled no-database checker, project-native Django/pytest commands, and explicit database evidence.
