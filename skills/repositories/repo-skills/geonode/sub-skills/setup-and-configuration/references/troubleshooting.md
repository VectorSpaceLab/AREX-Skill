# Troubleshooting

Use the first failing layer. Record commands and redacted observations; do not
paste `.env`, passwords, tokens, private keys, or full database URLs into an
issue or handoff.

## Installation and import failures

**Symptom:** `ImportError: osgeo`, GDAL version errors, GEOS/PROJ load errors,
or `psycopg2` cannot load.

1. Activate the intended Python environment and run `python --version`.
2. Compare `gdalinfo --version`, `geos-config --version`, and `projinfo
   --version` with the Python package metadata.
3. Verify `python -c 'from osgeo import gdal; print(gdal.VersionInfo())'` and
   similar imports without printing environment paths.
4. Reinstall the Python package and native libraries as one compatible set;
   do not mix a system GDAL with an unrelated binary wheel.
5. Retry `python manage.py check`. If it now reaches a database error, the
   native-import gate passed and the database gate is the next blocker.

**Symptom:** Django cannot parse settings or `manage.py check` fails on a
missing variable. Validate booleans expected by `ast.literal_eval` (`True` or
`False`), Python-list syntax for list settings such as `ALLOWED_HOSTS`, URL
schemes, and quoting. Compare the rendered file to the template without
revealing secret values.

## Database and spatial backend

**Symptom:** connection refused, authentication failed, `postgis` extension
missing, or migration fails on geometry.

- Confirm host/port from the process's network namespace. `db` is a Compose
  name; a bare process normally needs a host address or socket.
- Confirm the role can connect to both the main database and configured
  `GEODATABASE_URL`, and that PostGIS is enabled where GeoDjango needs it.
- Run `python manage.py migrate` only after connectivity is proven; use
  `--database=datastore` for the separate datastore when configured.
- Do not “fix” a PostGIS deployment by switching to Spatialite. Spatialite is
  a limited local fallback and does not verify PostGIS SQL, permissions,
  concurrency, or GeoServer datastore behavior.
- Check disk space, locks, migration history, and database logs before retrying.
  Never delete migration files or persistent volumes as a first response.

## Web settings and routing

**Symptom:** `DisallowedHost`, redirect loop, wrong absolute links, or 404s at
GeoServer/callback URLs.

- Make `SITEURL`, proxy public URL, `ALLOWED_HOSTS`, and GeoServer public/UI
  locations agree on scheme, hostname, port, and trailing slash.
- In Compose, use internal names only for service-to-service URLs and public
  names for browser/OGC URLs.
- If the host or scheme changed, update stored OAuth2/GeoServer settings and
  run the supported base-URL update procedure for the deployment. Restart
  affected processes and retest a home page, login redirect, and OGC link.
- Do not add `ALLOWED_HOSTS=*` or disable safe URL checks merely to suppress an
  error on a public instance.

## Startup, migrations, fixtures, and static files

**Symptom:** Django container exits before uWSGI, repeats initialization, or
has no CSS/media.

1. Read Django logs from the beginning of the current container attempt.
2. Identify whether failure occurs in derived environment setup, migrations,
   fixture loading, static collection, thesaurus loading, or process start.
3. Check writable persistent mounts and free disk; confirm the database is
   healthy before rerunning migrations.
4. Use `FORCE_REINIT` only with a documented backup and disposable/recovery
   plan. It can reload initialization fixtures and is not a harmless restart.
5. Run `collectstatic --noinput` after correcting paths and ensure Nginx and
   Django/volume mounts reference the same static root.

**Symptom:** migrations pass but startup hangs or first boot is slow. Wait for
health checks while inspecting logs, and distinguish a long fixture/thesaurus
phase from a deadlock or missing service. Do not start a second initialization
against the same persistent database without understanding the lock state.

## Worker-down deployment (web up, jobs pending)

Expected symptom: the home page/API responds, but upload publication,
harvesting, indexing, notifications, or cleanup remains pending.

1. Confirm `docker compose ps celery` or the bare worker supervisor state.
2. Confirm the worker uses the same `DJANGO_SETTINGS_MODULE`, `BROKER_URL`,
   result backend, and network/DNS as the web process.
3. Check Redis health and `celery inspect ping`; inspect worker logs for import,
   authentication, serialization, queue, or task exceptions.
4. Confirm the task's downstream gate: GeoServer for publication, remote OGC
   endpoint for harvesting, or PostGIS for persistence.
5. After repair, submit one small safe operation and observe enqueue,
   consumption, completion, and resulting resource state. Do not claim all
   historical tasks recovered from one successful job.

## GeoServer and OAuth2

**Symptom:** GeoServer is up but publication, previews, role synchronization,
or token callbacks fail.

- Test the internal `GEOSERVER_LOCATION` from the Django/worker network and
  the public location from the browser/client network.
- Verify admin credentials, GeoServer proxy/base URL, OAuth2 client id/secret,
  API key, issuer URL, and clock/TLS correctness. Rotate all related values as
  a coordinated change.
- Confirm the GeoServer security filter and role service were updated to match
  the GeoNode OAuth application. Environment changes do not necessarily
  rewrite stored GeoServer configuration.
- Preserve the service gate when GeoServer or credentials are unavailable;
  package checks cannot validate publication.

## HTTPS and hardening

**Symptom:** HTTP works but HTTPS redirects, cookies, callbacks, or certificates
fail.

- Confirm DNS points to the edge, ports 80/443 are reachable, and the
  certificate covers the exact hostname.
- Check `HTTP_HOST`, `HTTPS_HOST`, `HTTP_PORT`, `HTTPS_PORT`, `SITEURL`, and
  `LETSENCRYPT_MODE`. For custom certificates, verify the Nginx certificate
  volume and edit the real available configuration, not a generated symlink.
- Confirm the reverse proxy forwards the scheme/host expected by Django before
  enabling `SECURE_SSL_REDIRECT` or HSTS.
- Review `DEBUG`, secret/default credentials, CORS, frame policy, cookie flags,
  `ALLOWED_HOSTS`, `PROXY_ALLOWED_HOSTS`, API lockdown, and admin allowlists.
  A green HTTPS page is not a production security review.

## Unverified service gates

The following require infrastructure not present in a package-only or CPU
inspection: external PostgreSQL/PostGIS, GeoServer/Tomcat, Redis/Celery,
Nginx/Docker runtime, remote OGC services, cloud storage, credentials,
certificate issuance, and browser behavior. Mark each as **unverified** until a
safe, authorized check produces the expected signal.
