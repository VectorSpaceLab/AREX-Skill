---
name: resource-and-api
description: "Route and operate GeoNode resource REST workflows, safe uploads,
  asynchronous execution requests, downloads, metadata changes, and
  resource-level permissions for datasets, documents, maps, and geoapps."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Resource and API

Use this sub-skill when the task touches a GeoNode resource through HTTP: list
or inspect resources, upload or update data, create maps or geoapps, attach
metadata/assets, follow an execution request, download content, or change
resource-facing permissions.

## First route

1. Establish the deployed site origin explicitly. Do not infer it from a
   payload, a service URL, or a browser address. Use the API helper only with
   an explicit `--base-url`.
2. Establish the identity and permissions needed for the operation. Anonymous
   reads may work for advertised public resources; uploads and mutations need
   an authenticated account and resource-level permissions.
3. Read [api-reference.md](references/api-reference.md) for the exact route,
   method, serializer shape, response wrapper, and request example.
4. For an upload, update, copy, delete, permission, or remote-resource action,
   read [resource-lifecycle.md](references/resource-lifecycle.md) before
   sending the request, then read [upload-formats.md](references/upload-formats.md)
   for file and data assumptions.
5. Use [troubleshooting.md](references/troubleshooting.md) when a response is
   not the expected status or an execution remains pending.

## API boundaries

- Prefer the versioned REST resources below `/api/v2/` for resource operations.
  The legacy Tastypie resources below `/api/api/` have different serializers,
  filters, and authorization; do not mix their payloads with v2 payloads.
- The v2 resource collection is `/api/v2/resources/`; typed collections are
  `/api/v2/datasets/`, `/api/v2/documents/`, `/api/v2/maps/`, and
  `/api/v2/geoapps/`. The deployed upload route must be confirmed with the
  named `importer_upload` route or the instance's published API documentation;
  some deployments expose it as `/api/v2/uploads/upload`, while the snapshot's
  root URL declaration is not version-prefixed.
- Treat response `execution_id` or `exec_id` as opaque UUIDs. Never guess an
  execution URL or assume that HTTP 201 means the resource is published.
- A package import or serializer check proves neither database persistence,
  GeoServer publication, object storage, Redis/Celery execution, nor remote OGC
  access.

## Operating procedure

### Read and preflight

- Start with `GET /api/v2/resources/` or the typed collection. Record the
  returned `pk`, `uuid`, `resource_type`, `subtype`, `perms`, `is_published`,
  `is_approved`, and `download_urls` before mutating anything.
- Use `search`, repeated `search_fields`, `filter{...}`, `extent`,
  `metadata_only`, `favorite`, `page`, and `page_size` deliberately. Preserve
  the `links`, `total`, `page`, and `page_size` pagination envelope.
- For a private resource, authenticate before interpreting an empty list as
  absence. A filtered permission result is not proof that the resource does
  not exist.

### Mutate

- Use typed `PATCH` for ordinary metadata changes where supported. Use the
  dedicated dataset metadata `PUT` for an ISO metadata file and the metadata
  API for schema-shaped JSON. Check the required permission before attempting
  either.
- Use typed map/geoapp `POST` only with a serializer-valid payload; map layer
  relations are embedded and are transactionally saved. Document creation is
  intentionally a file/URL upload workflow, not a typed `POST`.
- For dataset data, use the importer with an explicit `action`: `upload`,
  `replace`, `upsert`, `create`, `resource_style_upload`, or
  `resource_metadata_upload`. Capture the returned execution identifier.
- Poll the returned status endpoint with bounded delay and a deadline. Terminal
  `finished` is success; `failed` is failure; `ready` and `running` require
  worker/service diagnosis, not repeated unbounded requests.

### Safety-sensitive operations

- Obtain and inspect `perms` or `GET .../permissions` before changing access.
  `PUT` replaces the proposed compact permission set; `PATCH` merges it. Do
  not send a partial `PUT` unless replacement is intended.
- Treat `DELETE /api/v2/resources/{pk}/delete`, upload `replace`, `upsert`, and
  asset removal as destructive. Confirm the `pk`, backup/retention policy, and
  target dataset type first. Prefer a dry read and a saved execution id.
- Download only through a URL returned by the resource and only after checking
  `download_resourcebase`. Dataset downloads require a locally available,
  downloadable resource; maps and geoapps normally have no data download URL.
- Do not place Basic credentials, bearer tokens, remote-service passwords, or
  full secret-bearing payloads in shell history, logs, or issue reports.

## Checks and handoff

A successful call must be checked at three levels: HTTP status and content
shape, resource/execution state, and service-side consequences when applicable.
For uploads, validate the archive before sending it with
`scripts/validate-upload-archive.py`; it inspects without extracting. For a
read-only request, use `scripts/api_request.py --help` and an explicit base URL.

If the database, PostGIS, GDAL/OGR, GeoServer, Redis/Celery, media storage,
remote endpoint, credentials, or browser stack is unavailable, report that
specific gate as unverified and hand back the execution id, response body,
and next diagnostic—not a claim of publication or completion.

## References and scripts

- [api-reference.md](references/api-reference.md): v2 routes, filters, auth,
  payloads, response envelopes, downloads, and permissions.
- [resource-lifecycle.md](references/resource-lifecycle.md): preflight,
  asynchronous state transitions, metadata/resource actions, and safe delete.
- [upload-formats.md](references/upload-formats.md): handlers, actions,
  supported formats, required companion files, and data constraints.
- [troubleshooting.md](references/troubleshooting.md): owned failure modes and
  bounded recovery paths.
- `scripts/api_request.py`: explicit-origin, JSON/GET, bearer-from-environment
  request probe with non-secret output.
- `scripts/validate-upload-archive.py`: non-extracting ZIP safety validator
  with a tiny self-test fixture.
