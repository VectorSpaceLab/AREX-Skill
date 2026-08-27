# Service topology and startup lifecycle

## Docker Compose roles

| Service | Role | Readiness signal | Depends on |
|---|---|---|---|
| `db` | PostgreSQL/PostGIS primary and datastore host | `pg_isready` health check | persistent database volume |
| `redis` | Broker/result backend for asynchronous work | `redis-cli ping` health check | persistent Redis volume |
| `django` | GeoNode web process and initialization owner | HTTP health check on port 8000 | healthy `db`, healthy `redis` |
| `celery` | Worker process for background tasks | Celery broker `inspect ping` | healthy `db`, healthy `redis` |
| `geoserver` | OGC/publication backend | HTTP endpoint health check | healthy `django` |
| `nginx` | Public HTTP/HTTPS proxy and static/media edge | process health check | network/volumes and upstream readiness |
| `letsencrypt` | Certificate acquisition/renewal helper | container state and certificate files | healthy `nginx`, DNS/ACME access |

Compose service names are internal DNS names. `db`, `redis`, `django`, and
`geoserver` should not be substituted into public browser URLs unless the user
can resolve them. Conversely, `localhost` inside a container means that same
container, not the host or a sibling service.

The Compose file mounts persistent volumes for database data, Redis data,
GeoServer data, static/media-related content, certificates, and backup/restore
areas. Treat those volumes as state. Do not remove them to repair an ordinary
readiness failure.

## Startup lifecycle

The container entrypoint and task collection implement this broad order:

1. Refresh derived runtime environment values and wait for the Docker network
   proxy name where the deployment uses it.
2. Run database migrations. The configured primary database and, where used,
   the datastore receive their required migrations.
3. Prepare and load first-boot fixtures: admin/site/OAuth defaults and initial
   data. This is guarded by an initialization lock; `FORCE_REINIT` changes that
   behavior and must be treated as a stateful operation.
4. Create/write static, media, and asset directories and collect static files.
5. Load or update shipped thesauri.
6. Start uWSGI for `django`, or start the Celery worker command for `celery`.
7. Start GeoServer after the Django health condition is met; Nginx and
   certificate services then expose the chosen edge.

The exact fixture and environment task implementation is deployment-specific.
Use the order above to locate failures, not to rerun every phase blindly. A
failure before uWSGI indicates initialization/configuration; a 200 page with
pending uploads indicates a later worker/GeoServer/data path.

## Safe inspection sequence

```bash
docker compose config
docker compose ps --all
docker compose logs --tail=200 db
docker compose logs --tail=200 redis
docker compose logs --tail=300 django
docker compose logs --tail=200 celery
docker compose logs --tail=200 geoserver
docker compose logs --tail=200 nginx
```

Check in dependency order. Look for health status, migration completion,
static collection, uWSGI readiness, Celery ping, GeoServer HTTP readiness, and
Nginx upstream errors. Do not run `docker compose exec` against a service that
is not running; use logs and container state first.

## Bare topology

A bare deployment has the same logical roles but the process boundaries are
host-managed: Django/uWSGI, Nginx, PostgreSQL/PostGIS, GeoServer/Tomcat, and
Redis/Celery. The development server is not a production proxy. Keep static
and media storage durable and accessible to the processes that need them.

Run database migrations before serving requests, collect static files before
Nginx points at the static root, and start the worker only after its broker URL
and Django settings are available. If GeoServer is remote, configure its
internal and public URLs separately and test connectivity from the GeoNode
process host, not only from an administrator laptop.

## Failure localization

- `db` unhealthy: inspect credentials, host/port, role permissions, PostGIS
  extension, disk, and database logs. Do not switch to Spatialite silently.
- `redis` unhealthy: inspect broker URL, authentication/TLS, container DNS,
  and Redis logs. Web health does not cover this gate.
- `django` exits before uWSGI: inspect environment parsing, native imports,
  migrations, fixture prerequisites, and writable volume paths.
- `celery` unhealthy while web is healthy: inspect broker connectivity,
  worker command/settings, queue names, and task exceptions.
- `geoserver` unhealthy: inspect its data directory, Java heap, database/data
  store, advertised base URL, and the Django dependency; publication remains
  unavailable until this gate passes.
- `nginx` serves a bad gateway: compare upstream service names/ports with the
  Compose network and inspect generated HTTPS configuration and certificates.
