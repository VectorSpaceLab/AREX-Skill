# Cross-cutting troubleshooting

Read this for failures that cross GeoNode's package, Django, database, GeoServer,
worker, catalogue, or proxy boundaries. Record the first failing plane and keep
secrets out of diagnostics.

## Install and import

| Symptom | Likely cause | Recovery |
|---|---|---|
| `pg_config executable not found` while installing `psycopg2` | PostgreSQL client development tools are absent | Install a supported PostgreSQL client/development package or use the project's documented binary strategy; verify `pg_config --version` before retrying. |
| `gdal-config` missing or GDAL Python import fails | GDAL Python binding does not match the native GDAL library | Install a matching native GDAL and Python binding; compare `gdal-config --version` with `from osgeo import gdal; print(gdal.__version__)`. Do not mix arbitrary system and environment libraries. |
| `ImportError` from a Django app or optional package | Incomplete installation or a version conflict | Check the distribution metadata and `python -m pip check`; install only the documented GeoNode dependency set, then repeat a clean import in the intended environment. |
| `ImproperlyConfigured: settings are not configured` | A Django module was imported before `DJANGO_SETTINGS_MODULE`/`django.setup()` | Set the settings module for Django API/model inspection, or use package-only imports for version checks. |

## Settings and startup

| Symptom | Likely cause | Recovery |
|---|---|---|
| Host-header or CSRF errors | `ALLOWED_HOSTS`, `SITEURL`, proxy scheme, or forwarded headers disagree | Normalize the public scheme/host/port and trailing slash; configure trusted proxy headers deliberately; rerun the narrowest Django check. |
| Web app starts but redirects to the wrong host | `SITEURL`, `GEONODE` public URL, OAuth redirect URI, or reverse-proxy prefix is stale | Compare internal, public, and browser/UI URLs. Update the owning configuration and restart the affected process; do not broaden proxy allowlists. |
| Migration or ORM errors mention spatial fields | A normal SQLite backend is being used for a workflow requiring GIS behavior | Use PostGIS for the deployment; treat Spatialite as a development fallback only and do not infer production equivalence from a unit import. |
| Static/media files return 404 | Static collection, volume mount, URL prefix, or permissions are wrong | Validate `STATIC_ROOT`, `MEDIA_ROOT`, URL prefixes, mounted volumes, and the process user; run collection in a disposable/approved target and verify one asset. |

## Database and GeoServer

| Symptom | Likely cause | Recovery |
|---|---|---|
| `connection refused` or database hostname errors | DB service is down, not ready, or a container service name was used from the host | Test DNS/TCP from the same network namespace as GeoNode; validate credentials through the secret mechanism; wait for readiness instead of rerunning migrations blindly. |
| Resource upload remains `ready`/`running` or fails after HTTP success | GeoServer, media storage, worker/broker, or task queue is unavailable | Preserve the execution id; check worker/broker and GeoServer logs separately; inspect the target resource before retrying. |
| GeoNode login succeeds but WMS/WFS returns 401/403 | Django auth and GeoServer auth/role/filter chains are separate planes | Compare the GeoServer token/role-service/OAuth configuration, workspace/layer rule, and reverse-proxy URLs. Do not grant anonymous access as a diagnostic shortcut. |
| OGC capabilities or links use an internal hostname | `GEOSERVER_PUBLIC_LOCATION` or proxy path is wrong | Keep server-to-server and browser/public URLs distinct; test both a capabilities response and a browser redirect after the change. |

## Catalogue, indexing, and harvesting

| Symptom | Likely cause | Recovery |
|---|---|---|
| Metadata validator passes but CSW/search does not find the resource | Catalogue endpoint, index, Celery task, or cache is stale/unavailable | Compare schema, saved instance, generated metadata, index/AnyText, and CSW in that order; report the unavailable service gate rather than weakening the schema. |
| Harvest session is stuck or repeatedly fails | Remote endpoint/auth/network, database, broker, worker queue, or GeoServer gate | Split the gates, preserve session/job ids and last successful stage, then retry only after the failing plane is repaired. |
| Reindex/sync appears successful but results are unchanged | Wrong database/instance, stale cache, wrong filter, or task not consumed | Verify target settings, selected identifiers, worker execution, and post-change search counts; avoid broad unscoped reindexing. |

## API and safety

- `401` usually means missing/invalid authentication; `403` means the identity
  is known but lacks the required permission or policy. Confirm the resource's
  `perms` and the correct auth plane before changing payloads.
- `404` can be a wrong deployment prefix, typed resource route, or hidden private
  resource. Verify the public API base and authentication before declaring the
  resource absent.
- `422` on metadata or upload usually carries field-level or execution details;
  preserve `message`/`extraErrors`, fix only the offending fields, and retry
  with a bounded plan.
- A `201` upload response is not publication proof. Poll the returned execution
  identifier and verify database, media, GeoServer, and worker consequences.
- Before `DELETE`, replace/upsert, permission replacement, restore, or bulk
  synchronization, confirm the target, backup/rollback plan, scope, and expected
  side effects. Help output is parser proof only.
