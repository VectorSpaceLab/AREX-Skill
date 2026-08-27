# Configuration

GeoNode settings are environment-driven. Keep one source of truth for the
process environment and validate the rendered values before starting services.
Never publish a complete `.env` file: it contains passwords, OAuth2 secrets,
Django keys, database URLs, and sometimes certificate material.

## Core settings

| Variable | Contract | Validation |
|---|---|---|
| `DJANGO_SETTINGS_MODULE` | Usually `geonode.settings` | `python -c 'import os; print(os.getenv("DJANGO_SETTINGS_MODULE"))'` without secrets |
| `SECRET_KEY` | Unique, high-entropy Django signing key | Non-empty and not a sample/default value; rotate with a planned session/token impact |
| `DEBUG` | `True` for local development only | Must be `False` before exposure; debug pages can disclose settings and environment data |
| `SITEURL` | Canonical public origin, normally ending `/` | Scheme, host, port, proxy, OAuth2 issuer, and GeoServer public URLs agree |
| `ALLOWED_HOSTS` | Parsed Python list or supported delimiter-separated host list | Include exact hostnames/ports as needed; avoid `*` publicly |
| `SITE_HOST_SCHEMA/NAME/PORT` | Default URL components | Keep consistent with `SITEURL`; do not let an internal container name become the public host |
| `MEDIA_ROOT`, `MEDIA_URL` | Persistent uploaded data and its URL | Writable by the web/worker processes; served through the intended proxy only |
| `STATIC_ROOT`, `STATIC_URL` | Collected static files and URL | Run `collectstatic`; mount/share the directory for proxy and web processes |

GeoNode adds a trailing slash to `SITEURL` and `GEOSERVER_LOCATION` when
needed. Still configure canonical values explicitly: redirects, OAuth2 issuer
URLs, catalogue URLs, and generated resource links depend on them.

## Database choices

`DATABASE_URL` selects the default Django database. The settings recognize a
Spatialite-style URL for local development and PostgreSQL/PostGIS URLs for
normal deployments. A typical container value has the form
`postgis://<role>:<password>@db:5432/<database>`; a bare host uses its actual
DNS name or address. If `DEFAULT_BACKEND_DATASTORE` is set, `GEODATABASE_URL`
is parsed into that named database and migrations/data operations must target
it explicitly.

Validate in this order:

```bash
python - <<'PY'
import os
from urllib.parse import urlparse
for name in ("DATABASE_URL", "GEODATABASE_URL"):
    value = os.environ.get(name)
    if value:
        parsed = urlparse(value)
        print(name, parsed.scheme, parsed.hostname, parsed.port)
    else:
        print(name, "unset")
PY
python manage.py check
python manage.py showmigrations --plan
```

The snippet intentionally omits usernames, passwords, query strings, and full
URLs. Do not use `showmigrations` as proof that a database is reachable if it
cannot connect. A PostGIS requirement cannot be replaced by a successful
Spatialite test.

For PostGIS, provision both databases/roles/extensions according to the
operator's policy and test the configured role's permissions. Do not grant
broad privileges just to make migrations pass. For Spatialite, verify the
extension can load and use a disposable database; keep it restricted to local
or test workflows.

## Service and identity URLs

| Variable | Meaning | Common failure |
|---|---|---|
| `GEOSERVER_LOCATION` | GeoNode-to-GeoServer URL, often internal in Compose | DNS works on host but not inside the Django container |
| `GEOSERVER_PUBLIC_LOCATION` | URL emitted for public OGC links | Links advertise an internal hostname or wrong scheme |
| `GEOSERVER_WEB_UI_LOCATION` | Browser/admin URL for GeoServer | Login redirects to a private port or stale hostname |
| `GEOSERVER_ADMIN_USER/PASSWORD` | GeoServer admin credentials | GeoNode can start but publication/security sync fails |
| `OAUTH2_CLIENT_ID/SECRET` | GeoServer's GeoNode OAuth2 client | Token/role calls fail after URL or secret rotation |
| `OAUTH2_API_KEY` | Secret protecting GeoNode role/info endpoints | Leaving it empty weakens the integration boundary |
| `NGINX_BASE_URL` | Public proxy URL in Docker templates | Proxy and `SITEURL` disagree |
| `CATALOGUE_URL` | Catalogue endpoint when configured | Metadata operations fail while the home page works |

Use the internal URL from Django/worker containers and the public URL from
browser/OGC clients. After changing OAuth2 values, update the matching GeoNode
OAuth application and GeoServer authentication filter, then recreate the
affected processes. A setting value alone does not update stored GeoServer
configuration.

## Async and process settings

`BROKER_URL` selects Redis for asynchronous signals/tasks when `ASYNC_SIGNALS`
is enabled. `CELERY_RESULT_BACKEND` commonly selects a second Redis database.
In tests, settings use memory/eager behavior; do not infer production worker
readiness from a test run. `CELERY_TASK_ALWAYS_EAGER=True` is useful for a
controlled local test but hides broker, serialization, queue, and worker
failures.

A deployment with uploads, harvesting, indexing, notifications, or publication
must test all of: Redis reachability, a worker consuming the relevant queue,
and the downstream service the task calls. A web request returning 200 only
proves the synchronous edge.

## Security and hardening

Before exposure, review at least:

- `DEBUG=False`, non-default `SECRET_KEY`, non-default admin/database/
  GeoServer passwords, and non-default OAuth2 client values.
- `ALLOWED_HOSTS` restricted to intended names; `PROXY_ALLOWED_HOSTS` restricted
  to approved outbound proxy targets; `SAFE_URL_CHECK_ENABLED=True` unless a
  specific test requires otherwise.
- `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_SSL_REDIRECT`, HSTS,
  `SECURE_CONTENT_TYPE_NOSNIFF`, `SECURE_REFERRER_POLICY`, and a deliberate
  `X_FRAME_OPTIONS` value aligned with TLS and proxy behavior.
- `CORS_ALLOW_ALL_ORIGINS=False` for public deployments unless the broad policy
  is explicitly required and compensated by an allowed-origin policy.
- `LOCKDOWN_GEONODE`, `API_LOCKDOWN`, admin/IP allowlists, signup/approval,
  email delivery, and default anonymous permissions.

Do not enable HTTPS flags before the proxy has a valid certificate and correct
forwarded-scheme behavior. Do not enable HSTS for a hostname that is not
consistently HTTPS; browsers cache HSTS policy.

## Validation checklist

```bash
docker compose config                         # Docker interpolation/YAML
docker compose ps                             # service state only
python manage.py check                        # Django checks
python manage.py check --deploy               # deployment warnings
python manage.py collectstatic --noinput      # static lifecycle
```

Run only commands appropriate to the selected topology. Redact command output
that includes settings or connection strings.
