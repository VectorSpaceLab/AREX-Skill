---
name: setup-and-configuration
description: "Install and configure GeoNode 5.1-style deployments, choose Docker
  or bare topology, validate settings and startup lifecycle, and diagnose
  service or hardening failures without claiming unavailable infrastructure is
  verified."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Setup and configuration

Use this skill when a user needs to install GeoNode, generate an environment
file, choose Docker versus bare deployment, align Django/GeoServer/database
settings, validate startup, or diagnose a deployment that is partly running.
This is a routing and validation skill: follow the linked references for the
long variable tables and recipes.

## Applicability and boundaries

- Target the GeoNode 5.1 configuration shape: Django settings, a primary
  database, an optional separate spatial datastore, GeoServer, Redis/Celery,
  and a web proxy.
- Choose **Docker** for the documented multi-container path or a **bare**
  installation for a controlled Linux host. Do not mix container service names
  with host-local addresses without deliberately mapping the topology.
- Treat PostgreSQL/PostGIS, GeoServer, Redis/Celery, Nginx, certificates,
  remote OGC endpoints, credentials, and browser checks as external gates.
  Package import or a static check does not prove these services are ready.
- Do not copy or execute privileged launchers, bulk fixture loaders, destructive
  volume resets, or host mutation as a generic fix. Use the lifecycle summary
  in [service topology](references/service-topology.md) and the recovery matrix
  in [troubleshooting](references/troubleshooting.md).

## Route the request

1. Identify deployment mode, intended public URL, database mode, and whether
   asynchronous jobs or GeoServer publication are required.
2. For Docker, read [installation](references/installation.md) and
   [service topology](references/service-topology.md). For bare, read the bare
   section and confirm native GDAL/GEOS/PROJ/SQLite or PostGIS prerequisites.
3. For settings or security changes, read [configuration](references/configuration.md)
   before editing `.env`. Never paste secrets into chat or logs.
4. For an environment template, run the bundled generator with explicit
   `--sample-file` and `--output`; inspect the resulting file locally and
   protect it as a secret-bearing artifact.

## Minimum configuration contract

Before startup, confirm the following values are intentional and mutually
consistent:

- `DJANGO_SETTINGS_MODULE=geonode.settings`, a unique `SECRET_KEY`, and
  `DEBUG=False` for any exposed deployment.
- `SITEURL` is the externally visible canonical URL with the right scheme,
  host, port, and trailing slash. `ALLOWED_HOSTS` includes the request host but
  is not an accidental wildcard in a public deployment.
- `DATABASE_URL` points to a spatially capable PostGIS database for normal
  deployments. If `DEFAULT_BACKEND_DATASTORE` is set, validate its
  `GEODATABASE_URL` separately. Spatialite is a development fallback, not a
  substitute for PostGIS behavior.
- `GEOSERVER_LOCATION` is reachable from GeoNode; public and UI locations are
  the URLs users and GeoServer advertise. Keep internal and public URLs
  distinct when Docker DNS is involved.
- `BROKER_URL` and `CELERY_RESULT_BACKEND` point to the same intended Redis
  topology when asynchronous processing is enabled. `ASYNC_SIGNALS` and
  Celery eager settings must match the deployment goal.
- HTTPS, cookie, CSRF, CORS, frame, HSTS, OAuth2, admin-password, and
  certificate settings are reviewed using the hardening checklist; defaults
  suitable for development are not production approval.

## Validate in increasing cost order

1. Run `python scripts/generate_envfile.py --help` and, if generating a file,
   use a disposable sample/output pair. Confirm no secret appears in stdout.
2. Parse the environment file and check URL schemes, trailing slashes,
   required non-empty values, and host/port consistency. Do not print values
   that contain `PASSWORD`, `SECRET`, `TOKEN`, `KEY`, or `URL` credentials.
3. In the selected environment, run `python manage.py check` and then
   `python manage.py check --deploy` when settings and dependencies are
   available. A database or GeoServer error is a service gate, not proof that
   the configuration is valid.
4. For a bare install, run `python manage.py migrate` for the default database
   and, when configured, `python manage.py migrate --database=datastore`.
   For Docker, let the documented startup lifecycle perform migrations and
   inspect container health and logs.
5. Confirm static collection and the home-page health check only after the web
   process is running. Confirm a Celery worker separately; a healthy web
   container does not prove that uploads or harvesting will complete.

## Expected observations and recovery

- A generated file has no `{placeholder}` tokens, is written only to the
  requested destination, and the generator reports counts/path—not values.
- A healthy Docker deployment has healthy `db` and `redis` before Django,
  Django before GeoServer, and a separate worker health signal. See the
  topology reference for dependency conditions and safe inspection commands.
- A bare deployment can import Django and pass static checks before its
  PostGIS, GeoServer, proxy, or Redis services are available. Record those
  gates explicitly and stop at the first unavailable required service.
- If a setting change is made, restart/recreate the affected process and
  re-run the narrowest check. If the web page works but jobs remain pending,
  route to the worker/broker branch in troubleshooting rather than rerunning
  migrations or deleting volumes.

## Handoff format

Report deployment mode, configuration checks, lifecycle stage reached, exact
service gates tested, and unresolved prerequisites. Include whether the result
is **package-valid**, **settings-valid**, **service-ready**, or **production
reviewed**; do not collapse these statuses. Link the relevant troubleshooting
entry and keep all credentials redacted.
