# GeoNode resource API reference

This is an operating reference for the GeoNode 5.1 API shape. Replace
`https://geonode.example` with the explicitly selected site origin and use the
route spelling returned by that deployment. Never put a real password or token
in an example.

## Authentication and response discipline

- Public advertised resources may be readable without authentication.
  Private-resource reads, uploads, edits, downloads, deletes, and permission
  actions require an authenticated user.
- The documented choices are a session/basic-auth request or
  `Authorization: Bearer <access-token>`. The bundled request helper accepts a
  bearer token only from an environment variable and never echoes it.
- Check both HTTP status and JSON shape. Common statuses are `200` for reads or
  accepted actions, `201` for an accepted importer/document creation, `204` for
  a successful no-content deletion, `400` for validation, `401` for missing or
  invalid authentication, `403` for insufficient object permissions, `404` for
  an unknown resource/execution, and `405` for a route/method mismatch.
- A successful asynchronous submission is only an acknowledgement. Preserve
  `execution_id`/`exec_id`, `status_url`, `status`, and the response body.

## Versioned resource routes

All of the following are under `/api/v2/` and normally end in `/`. Use the
collection route for list/create and `/{pk}` for a detail operation.

| Resource | Collection | Detail/actions | Safe starting methods |
|---|---|---|---|
| All resources | `resources/` | `resources/{pk}/` | `GET` |
| Datasets | `datasets/` | `datasets/{pk}/` | `GET`, `PATCH` |
| Documents | `documents/` | `documents/{pk}/` | `GET`, `PATCH` |
| Maps | `maps/` | `maps/{pk}/` | `GET`, `POST`, `PATCH`, `PUT` |
| GeoApps | `geoapps/` | `geoapps/{pk}/` | `GET`, `POST`, `PATCH`, `PUT` |
| Execution requests | `executionrequest/` | `executionrequest/{exec_id}/` | `GET` |
| Upload limits | `upload-size-limits/` | `upload-size-limits/{pk}/` | `GET` |
| Upload parallelism | `upload-parallelism-limits/` | `upload-parallelism-limits/{pk}/` | `GET` |

Typed creation is intentionally asymmetric: map and geoapp viewsets expose
`POST`; the document viewset does not expose creation, and dataset creation is
normally performed by the importer or the empty-dataset action. Do not infer
that every collection accepts `POST`.

The base resource serializer can expose `pk`, `uuid`, `resource_type`, `owner`,
roles, title/abstract, keywords, regions, category, `group`, state flags,
`detail_url`, `embed_url`, `thumbnail_url`, `perms`, `download_url`,
`download_urls`, `links`, `favorite`, and deferred fields such as `executions`.
Use `include[]=executions`, `include[]=linked_resources`, or another supported
include only when the client needs the deferred field.

## Listing, filtering, and detail

A list response contains a `resources`, `datasets`, `documents`, `maps`, or
`geoapps` collection plus pagination information. In the v2 pagination shape,
look for `links.next`, `links.previous`, `total`, `page`, and `page_size`.
A detail response is usually keyed by its singular serializer name, such as
`resource`, `dataset`, `document`, or `map`; dynamic response configuration can
alter embedding, so inspect the actual body.

Examples (read-only):

```sh
python scripts/api_request.py \
  --base-url https://geonode.example \
  --path /api/v2/resources/ \
  --method GET

python scripts/api_request.py \
  --base-url https://geonode.example \
  --path '/api/v2/resources/?filter%7Bresource_type%7D=dataset&page_size=20' \
  --method GET \
  --bearer-env GEONODE_TOKEN
```

Useful query patterns include:

```text
/api/v2/resources/?search=roads&search_fields=title&search_fields=abstract
/api/v2/resources/?filter{resource_type}=dataset
/api/v2/resources/?filter{resource_type.in}=dataset&filter{resource_type.in}=map
/api/v2/resources/?filter{subtype}=vector
/api/v2/resources/?filter{is_published}=true
/api/v2/resources/?filter{is_approved}=true
/api/v2/resources/?filter{owner.username}=alice
/api/v2/resources/?filter{keywords.name.icontains}=water
/api/v2/resources/?extent=-180,-90,180,90&page=2&page_size=10
/api/v2/resources/?favorite=true
```

URL-encode braces when using a shell or an HTTP library that treats them as
format syntax. `extent` is four comma-separated coordinates. `metadata_only`
and configured API presets are deployment settings; verify them rather than
assuming a preset exists.

## Upload entry point and route caveat

The importer accepts multipart form data and returns `201` with an
`execution_id` when a handler accepts the request. The public documentation
uses:

```text
POST /api/v2/uploads/upload
```

The snapshot also declares a named root route `importer_upload` whose literal
URL is not version-prefixed in the URL declaration. Some deployments or
reverse proxies expose the documented v2 path, while a direct installation may
resolve the named route differently. Resolve the named route in the deployed
site, use the published API documentation, or try a harmless authenticated
`OPTIONS`/`GET` method check before posting. A `404` or `405` here is a route
selection problem, not a file-format diagnosis.

A standard multipart request (with a deployment-resolved `$UPLOAD_URL`) is:

```sh
curl --fail-with-body -X POST "$UPLOAD_URL" \
  -H "Authorization: Bearer $GEONODE_TOKEN" \
  -F action=upload \
  -F base_file=@roads.geojson
```

`base_file` is the primary upload. Optional fields include `xml_file`,
`sld_file`, `store_spatial_files` (default true), and
`skip_existing_layers` (default false). See the format reference for action
specific fields and for why a successful `201` still requires polling.

## Dataset-specific actions

### Metadata and relationships

- `PUT /api/v2/datasets/{dataset_id}/metadata` accepts multipart
  `metadata_file=@metadata.xml`; the metadata UUID, when present, must match
  the target dataset. It returns a success message only after parsing and
  applying the metadata.
- `GET /api/v2/datasets/{dataset_id}/maplayers` lists the map-layer relations.
- `GET /api/v2/datasets/{dataset_id}/maps` lists maps using the dataset.
- `GET`/`PUT /api/v2/datasets/{dataset_id}/timeseries` reads or changes time
  configuration. It is permission checked and may require GeoServer metadata.
- `PUT /api/v2/datasets/{dataset_id}/recalc-bbox` requests a GeoServer-backed
  bbox recalculation; an optional JSON `{"bbox": [...]}` can force a bbox.

### Resource-service operations

The base resource detail actions are asynchronous unless stated otherwise:

```text
POST   /api/v2/resources/create/dataset
PUT    /api/v2/resources/{pk}/update
PUT    /api/v2/resources/{pk}/copy
DELETE /api/v2/resources/{pk}/delete
GET|PUT|PATCH|DELETE /api/v2/resources/{pk}/permissions
```

Representative update payload (JSON or the form fields accepted by the
installed parser):

```json
{
  "vals": "{\"title\":\"Updated title\"}",
  "metadata_uploaded": false,
  "regions": "[]",
  "keywords": "[\"water\"]",
  "custom": "{}",
  "notify": true
}
```

Create uses the resource type in the path and a defaults object, for example:

```json
{
  "uuid": "optional-client-uuid",
  "resource_type": "dataset",
  "defaults": "{\"owner\":\"alice\",\"title\":\"New dataset\"}"
}
```

The returned object has the shape:

```json
{
  "status": "ready",
  "execution_id": "opaque-uuid",
  "status_url": "https://geonode.example/api/v2/resource-service/execution-status/opaque-uuid"
}
```

The legacy-compatible execution route is
`GET /api/v2/resource-service/execution-status/{execution_id}`. The versioned
execution collection is useful for the requesting user's own records:
`GET /api/v2/executionrequest/{execution_id}` and
`GET /api/v2/executionrequest/?filter{status}=finished`. The status endpoint
returns `user`, `status`, `func_name`, timestamps, `input_params`,
`output_params`, `step`, and `log` when visible to the caller.

## Maps, geoapps, documents, and downloads

- A map `POST /api/v2/maps/` payload can include resource fields and an
  embedded `maplayers` list. Each map layer may carry `dataset`, `name`,
  `order`, `visibility`, `opacity`, `current_style`, and `extra_params`.
  Save the response `pk`, then use `GET /api/v2/maps/{pk}/maplayers` or
  `/datasets` to verify relations.
- A geoapp `POST /api/v2/geoapps/` must provide the app-specific `name`; the
  server sets the owner to the authenticated user. Do not pass a different
  owner expecting it to override that behavior.
- Upload a local document with multipart `POST /documents/upload/` or the
  deployment's documented equivalent, using `title` and `doc_file`. A remote
  document uses `doc_url` and, when the URL has no recognizable suffix,
  `extension`. A document cannot provide both a local file and URL.
- Use `GET /documents/{pk}/download` for a document and
  `GET /datasets/{resource.alternate}/dataset_download` for a dataset's
  default download. Prefer a serializer-provided `download_url` or
  `download_urls` and check permissions first. Do not treat map/geoapp
  `download_urls: []` as an error.

## Permissions and favorites

Resource permissions are compact levels: `view`, `download`, `edit`, and
`manage` (with `owner` for the owner). The effective low-level permissions are
returned in `perms`. A manager can inspect:

```text
GET /api/v2/resources/{pk}/permissions
```

A compact request has user/group entries and a permission level. The installed
API also accepts `organizations` in the documented compact form:

```json
{
  "users": [{"id": 1001, "permissions": "edit"}],
  "groups": [{"id": 2, "permissions": "view"}],
  "organizations": []
}
```

`PUT` computes a replacement from the proposed compact specification; `PATCH`
merges a compact change. `DELETE` removes managed permissions while retaining
owner/admin invariants. These requests return an execution object, so poll it.
A non-manager receives `403`; site read-only or maintenance mode also blocks
mutations. Whether the caller may manage anonymous or registered-member groups
is separately restricted.

Favorites are user-scoped:

```text
GET    /api/v2/resources/favorites/
POST   /api/v2/resources/{pk}/favorite/
DELETE /api/v2/resources/{pk}/favorite/
```

The POST/DELETE responses are small messages and do not change resource
permissions.

## Related resources and assets

```text
GET    /api/v2/resources/{pk}/linked_resources/
POST   /api/v2/resources/{pk}/assets/
DELETE /api/v2/resources/{pk}/assets/{asset_pk}/
```

Asset upload uses multipart `file` plus optional `title` and `description`.
Asset deletion requires change permission and is distinct from resource
 deletion. Validate file type and XML safety before sending an asset.
