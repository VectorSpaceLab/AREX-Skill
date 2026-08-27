# Resource/API troubleshooting

Use the response status, body, execution `step`, and service gate together.
Redact bearer tokens, basic-auth headers, remote credentials, signed URLs, and
sensitive `input_params` before sharing diagnostics.

## Malformed or unsafe inputs

### `400 Invalid or unsafe ZIP archive`

The upload serializer inspects ZIP-based extensions before extraction. Rebuild
the archive with relative, normalized member names and no symlinks. Remove
`..`, absolute paths, suspiciously compressed filler, and excess entries. Run:

```sh
python scripts/validate-upload-archive.py suspect.zip
```

A clean archive from the helper still does not prove that it contains a valid
shapefile/GeoPackage/KMZ/XLSX. Confirm required companions and content with the
appropriate format tool, then retry once with a new execution id.

### `400` for GeoJSON, shapefile, GPKG, CSV, or TIFF

Check the extension, content signature, required companions, schema, CRS, and
size/parallelism limits. For GeoJSON, parse JSON and require `Feature` or
`FeatureCollection`. For shapefiles, keep the same basename for `.shp`, `.shx`,
`.dbf`, and `.prj`. For CSV, pair latitude/longitude columns or provide a
recognized geometry column. For GPKG, use a real GeoPackage with valid layers.
For TIFF, verify GDAL can open it and expose spatial reference.

### unsafe XML/SLD or metadata UUID mismatch

The XML safety gate rejects unsafe declarations/entities and malformed content.
Generate a safe metadata/SLD document, then ensure an embedded metadata UUID
matches the target dataset. Use the dedicated dataset metadata route only with
`metadata_file`; do not send an XML file in a JSON field and expect it to be
parsed.

## Authentication and permissions

### `401 Unauthorized`

The request lacks a valid session/basic credential or bearer token, the token
is expired, or the Authorization header was stripped by a proxy. Re-run a safe
`GET` against a public endpoint, then a private detail request with a token
loaded from an environment variable. Never put the token into the URL.

### `403 Forbidden`

The account is authenticated but lacks the required object-level permission.
Inspect the target's `perms`; view, download, edit, and manage are distinct.
Uploads need add-resource permission. Dataset replace/upsert needs edit/manage
and compatible target state. Permission changes need change-permissions/manage.
Downloads need view plus download. A site in read-only or maintenance mode can
also reject mutations. Ask an administrator to grant the minimum required
permission rather than switching to a superuser blindly.

### `404` or empty list for a private resource

Confirm the site origin, API version, trailing slash, numeric `pk`, and caller
visibility. An unauthenticated filtered list can legitimately hide a private
resource. Do not infer deletion from a hidden detail.

## Route and payload errors

### `405 Method Not Allowed`

The viewset intentionally restricts methods. Documents do not use typed POST
creation; use the document upload flow. Dataset files use the importer, not a
normal dataset POST. Confirm route resolution for `importer_upload`: the source
snapshot's named upload route and public docs can differ under a reverse proxy.

### `400` serializer/field errors

Preserve the field-level error body. Common causes are boolean values sent as
unrecognized strings, missing `resource_pk` for replace/upsert/style/metadata,
missing `title`/`geom`/`attributes` for empty create, invalid embedded map
layers, invalid `attributes` JSON, a missing WMS `identifier`, or both a local
document file and `doc_url`. Correct one field at a time and do not retry a
mutation while the prior execution is still active.

## Pending or failed asynchronous work

### Status remains `ready`

The execution row was created but the queue may be unavailable, the worker may
not consume the `geonode` queue, or the task may have expired. Poll with a
bounded deadline, then inspect broker/worker health and the execution's
`last_updated`/`log`. Do not submit duplicate uploads or deletes.

### Status remains `running`

Use the `step` and `tasks` fields. A long `import_resource` step points to
GDAL/OGR, datastore, schema, or input problems; a long publish step points to
GeoServer/workspace/store credentials; a metadata/thumbnail step points to
XML, media, or service access. Check worker logs and service readiness before
retrying.

### Status is `failed`

Keep the execution id, final `log`, `func_name`, `step`, and sanitized
`output_params`. If a partial import created resources, enumerate them before
retrying; the orchestrator can mark partial failures and may roll back only
some steps. Repair the input or service gate and follow the deployment's retry
policy. Do not delete a failed resource by guessed title.

## GDAL/PostGIS/GeoServer and remote gates

### Missing GDAL/OGR or spatial reference

A CPU Python import is not enough. Upload handlers call GDAL/OGR tools and may
need the native `ogr2ogr`/`gdal_translate` executables. Install the deployment's
supported geospatial libraries, verify the input opens, and ensure the worker
uses the same environment. A missing CRS can prevent publication or create an
ambiguous dataset.

### Datastore errors

PostgreSQL/PostGIS and the configured datastore must be reachable and migrated.
Do not substitute SQLite for spatial persistence and claim parity. Check
connection settings, role privileges, schema/dynamic-model state, and table
locks without printing passwords.

### GeoServer publication/thumbnail failures

Check GeoServer URL, workspace/store, credentials, catalog readiness, and
whether GeoServer can read the asset path. A created resource with
`is_published=false`, a failed `publish_resource` step, or missing OGC links
is not a successful publication. The external GeoServer service is not
verified by package imports.

### Remote WMS/COG/FlatGeobuf/3D Tiles failures

Check safe-URL/redirect policy, DNS, TLS, credentials, WMS capabilities and
identifier, HTTP Range support for COG/FlatGeobuf, and required 3D Tiles JSON
keys. Probe only with approved endpoints and bounded timeouts. Do not embed
remote secrets into the GeoNode payload unless the deployment explicitly
supports and protects its authentication configuration.

## Download and delete safety

### Download URL missing or returns forbidden

Check `resource_type`, `can_be_downloaded`, local asset availability, and
`download_resourcebase`. Remote datasets may intentionally have no local
payload; maps and geoapps normally return no dataset download URLs. Use the
server-provided route and do not turn an OGC service link into a file download.

### Delete needs recovery

Pause after a rejected or timed-out delete. Re-read the resource and execution
record as the caller; confirm that no worker is still deleting related assets or
GeoServer objects. Only an authorized manager should retry, with the exact
`pk`, retention decision, and a record of the previous response.

## Explicit unverified gates

The public GeoNode snapshot was inspected with CPU/geospatial Python support,
not a full deployment. External PostgreSQL/PostGIS, GeoServer, Redis/Celery,
Nginx/Docker, remote OGC endpoints, credentials, media/object storage, and
browser services remain prerequisites and unverified service gates unless a
separate environment proves them.
