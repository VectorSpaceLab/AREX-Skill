# Installation

This reference gives bounded Docker and bare installation paths. Replace
angle-bracket values with local choices; do not copy sample passwords into a
public deployment.

## Select a path

| Path | Use when | Required gates |
|---|---|---|
| Docker Compose | You want the documented GeoNode, PostGIS, GeoServer, Redis, Celery, and Nginx topology on one Docker host | Docker Engine/Compose, image access, disk/RAM, ports, persistent volumes |
| Bare GeoNode/project | You administer a Linux host and need systemd/uWSGI/Nginx or a development server | Python environment, GDAL/GEOS/PROJ, libpq, PostGIS, Java/GeoServer, reverse proxy, Redis/Celery as needed |
| Package-only inspection | You only need settings/import/API code checks | Python dependencies and native geospatial libraries; no live services claimed |

The quick-start documentation describes roughly 8 GB RAM as a bare minimum for
a single-server deployment and more for production. Treat capacity as a
planning input, not an acceptance result. A public deployment also needs
backups, monitoring, patching, firewall policy, certificate management, and an
operator; this skill does not certify those controls.

## Docker workflow

1. Install Docker Engine and the Compose plugin using the host distribution's
   supported instructions. Confirm `docker version` and `docker compose version`
   before touching GeoNode.
2. Use a project directory containing the Compose file and a sample environment
   template. Generate an environment file without logging secrets:

   ```bash
   python scripts/generate_envfile.py \
     --sample-file <project-dir>/.env.sample \
     --output <project-dir>/.env \
     --hostname localhost \
     --env-type dev \
     --no-input
   ```

   Use `--https --email <operator-email>` only when DNS, ports, certificate
   issuance, and mail/certificate prerequisites are arranged. Review the
   generated values and change any development defaults before exposure.
3. Build and start the stack:

   ```bash
   docker compose config
   docker compose build
   docker compose up -d
   ```

   `docker compose config` catches interpolation and YAML errors before image
   work. The first build may require network access and substantial disk.
4. Inspect state and logs without printing the environment file:

   ```bash
   docker compose ps
   docker compose logs --tail=200 db redis django celery geoserver nginx
   curl --fail --silent --show-error --max-time 10 http://<public-host>/
   ```

   Use the configured scheme and port, not a guessed URL. A successful home
   page is only a web gate; test the worker and GeoServer independently.
5. When `.env` changes, recreate affected containers so the new process
   environment is loaded. Prefer `docker compose up -d <services>` over
   destructive `down -v`. Never use `down -v` as ordinary troubleshooting: it
   deletes persistent database, GeoServer, media, and queue data.

For a project rather than vanilla GeoNode, use the project's own Compose file
and sample template. The environment generator is template-driven; do not
assume a project accepts every variable in the vanilla sample.

## Bare workflow

1. Create and activate an isolated Python environment. Install the package
   requirements for the selected GeoNode release/project and verify native
   libraries before debugging Django. The source documentation lists Python
   development headers, `libgdal`/GDAL utilities, GEOS, PROJ, SQLite/SpatiaLite
   development packages, `libpq`, and Java among bare prerequisites.
2. Verify versions from the actual host:

   ```bash
   python --version
   gdalinfo --version
   geos-config --version
   projinfo --version
   java -version
   ```

   Version compatibility is release- and distribution-specific. For this
   snapshot the Python package declares Python >=3.10, Django 5.2.17, GDAL
   3.12.2, and psycopg2 2.9.12; do not force a mismatched binary wheel.
3. Set `DJANGO_SETTINGS_MODULE=geonode.settings` and source an environment
   file through a controlled shell. Keep database URLs and secrets out of
   command history where possible. Use PostGIS for the main and datastore
   databases when configured.
4. Verify database connectivity and extensions before migrations. Then run:

   ```bash
   python manage.py check
   python manage.py migrate --noinput
   python manage.py migrate --database=datastore --noinput  # only if configured
   python manage.py collectstatic --noinput
   ```

   The `datastore` command is conditional: only run it when
   `DEFAULT_BACKEND_DATASTORE` names a configured database. Migrations are
   state-changing; take an approved backup and use a maintenance window in a
   real deployment.
5. Start a development server only for development:

   ```bash
   python manage.py runserver 127.0.0.1:8000
   ```

   For a managed deployment, use a supported WSGI process and reverse proxy,
   configure static/media paths, and supervise separate Celery worker/beat
   processes. The exact service manager and uWSGI configuration are host
   choices and must be tested on that host.

## Native prerequisites and import failures

- `ImportError` for `osgeo`, `django.contrib.gis`, `shapely`, or `pyproj`
  usually means the Python package and system ABI are misaligned. Compare
  `gdalinfo --version`, the Python package metadata, and library search paths;
  reinstall in the same environment rather than mixing system and virtualenv
  packages.
- `psycopg2` import or connection errors require a compatible `libpq` runtime
  and PostgreSQL access. A successful import does not prove a PostGIS server.
- SpatiaLite can support a small local development fallback only when the
  SQLite extension and GeoDjango backend work together. It does not validate
  PostgreSQL roles, PostGIS extensions, concurrent writes, or production
  performance.
