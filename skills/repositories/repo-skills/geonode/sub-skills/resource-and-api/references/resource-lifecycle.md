# Resource lifecycle and asynchronous work

GeoNode resource operations cross Django, the datastore, media/assets,
GeoServer, and a worker queue. Treat the API response as a state transition
request, not as proof that every side effect has completed.

## Preflight checklist

Before a mutation, record:

- site origin and the route resolved by the deployment;
- authenticated user, token scope/session, and whether the site is read-only or
  in maintenance mode;
- target `pk`, `uuid`, `resource_type`, `subtype`, owner, `perms`, and current
  `dirty_state`/publication flags;
- whether the operation is local or remote, vector or raster, and whether the
  target already has an asset/dynamic model;
- expected data type, CRS/SRID, schema, layer count, and upload size;
- whether PostgreSQL/PostGIS, media storage, GeoServer, Redis/Celery, and any
  remote endpoint are available.

Save the original metadata and permission response before replace, upsert,
permission PUT, or delete. Confirm the target identifier twice; a title or
alternate is not a safe substitute for the numeric `pk` in a destructive route.

## Lifecycle states

Execution requests use these terminal/working states:

| State | Meaning | Client action |
|---|---|---|
| `ready` | Request persisted; work has not started or is queued | Poll with a deadline; inspect worker/broker if unchanged |
| `running` | One or more handler/manager steps are active | Poll slowly and inspect `step`, `tasks`, and `log` |
| `finished` | Workflow marked complete | Verify resource flags, assets, metadata, and service side effects |
| `failed` | Workflow stopped or rolled back/partially failed | Read `log`/`output_params`, preserve the id, repair input/service, retry deliberately |

Upload executions may also expose `tasks` keyed by layer and step. A finished
request can still require a separate verification of `is_published`,
`is_approved`, `processed`, `detail_url`, or a generated download URL.

## Polling recipe

1. Capture `execution_id` from the upload response or from
   `execution_id`/`status_url` returned by a resource-service action.
2. Use the supplied `status_url` when present. Otherwise use the authenticated
   execution detail endpoint for the current user.
3. Poll immediately once, then use a bounded delay such as 2, 4, 8, 16, 30
   seconds with a total deadline appropriate for the file. Never busy-loop.
4. Stop on `finished` or `failed`; retain the final JSON and the last `step`.
5. On timeout, stop polling and diagnose the queue/service matrix. Retrying a
   request can duplicate a resource or submit a second destructive operation.

The status body may contain `input_params` with filenames, URLs, or other
sensitive data. Store it in a protected location and redact secrets before
sharing it.

## Common lifecycle workflows

### New file upload

1. Validate extension, MIME/magic-byte expectations, archive structure, XML
   safety, size, and parallelism locally where possible.
2. Send multipart `action=upload` and `base_file`; add `xml_file`/`sld_file`
   only for a handler that supports them.
3. Expect an accepted execution id, not an immediate resource detail.
4. Poll until terminal, then locate the created resource(s) in `output_params`
   or by a server-returned `detail_url`.
5. Verify owner, title, subtype, schema/attributes, `processed`, publication
   flags, links, and download availability.

Vector imports usually require OGR/GDAL, a PostGIS datastore, dynamic-model or
schema support, and GeoServer publication. Raster imports require GDAL and
GeoServer access to the stored file. A worker may create a database object but
fail at publish or thumbnail generation; diagnose the failed step rather than
re-uploading blindly.

### Replace dataset data

Use the importer with `action=replace`, `resource_pk`, and one compatible
`base_file`. Confirm the old resource's vector/raster class and CRS first. A
replace preserves the resource identity only when the handler and existing
resource support it; it can reconfigure the underlying datastore and
GeoServer. Do not replace a vector with a raster or vice versa. Preserve a
backup/asset according to the deployment policy before a live replace.

### Upsert vector features

Use `action=upsert`, `resource_pk`, and optionally `upsert_key` (default `fid`).
This is experimental and is not a general schema migration. The target must
be a supported vector dataset with dynamic model/schema state. The incoming
file must contain at least one feature, the same columns and compatible types,
an appropriate unique non-null key, and the same CRS. Upsert is not for 3D
Tiles. GeoServer feature restrictions can reject individual values; inspect
the generated error asset when the request fails.

### Create an empty dataset

Use the importer `action=create` with no `base_file`, a `title`, a geometry
name such as `Point`/`Polygon`, and an `attributes` JSON object. Each attribute
needs a supported type and nullability; optional range or enumeration
restrictions are applied when the deployment supports them. The handler uses a
dynamic model and creates the empty schema asynchronously. Verify the resulting
attribute list and do not expect a feature count greater than zero.

A representative JSON body is:

```json
{
  "action": "create",
  "title": "Inspection points",
  "geom": "Point",
  "attributes": {
    "code": {"type": "string", "nillable": false},
    "priority": {"type": "integer", "nillable": true}
  }
}
```

### Metadata and style

For an ISO metadata file, use the dedicated dataset metadata route or the
`resource_metadata_upload` importer action. Ensure the XML is safe and the
embedded resource UUID matches when supplied. For a style, use
`resource_style_upload` with the existing resource `resource_pk` and an SLD.
These handlers may only enqueue work; a style or XML response does not prove
GeoServer/catalogue regeneration succeeded.

The JSON metadata API is a separate schema-driven workflow. Read its schema,
read the instance, update only schema-supported fields, and check the caller's
metadata-change permission. Sparse custom fields are not a substitute for a
core schema field with the same name.

### Copy, permission, and delete

- Copy requires the source to be viewable and copyable. Dataset/document copy
  also requires add and download privileges. Let the server choose a new
  alternate when requested; verify assets and ownership on the new resource.
- Permission GET is synchronous; permission PUT/PATCH/DELETE creates a resource
  execution. A resource in `dirty_state` cannot accept a new permission update.
  Wait for the previous operation before retrying.
- Resource delete is asynchronous and may remove datastore tables, dynamic
  models, assets, service publication, and links. Confirm permissions and
  retention policy, record the execution id, and verify absence only after
  `finished`. Never use a delete route as a failed-upload cleanup shortcut
  without checking ownership and the execution record.

## Service gates and recovery

| Failed step/symptom | Gate to check | Safe next action |
|---|---|---|
| `ready` never changes | Redis/broker, worker queue, task expiry | Check worker logs and queue health; do not submit duplicates |
| `import_resource` fails | GDAL/OGR, file schema, PostGIS datastore | Re-run local format checks and inspect the task log |
| `publish_resource` fails | GeoServer URL/credentials/workspace/store | Repair the service and retry only with a known idempotent policy |
| thumbnail/metadata fails | media storage, XML/schema, GeoServer | Keep the resource id; repair the failing side effect separately |
| remote preparation fails | URL allowlist, DNS/TLS/auth/range support | Probe the remote endpoint without exposing credentials |
| request succeeds but flags stay false | later async step or moderation setting | Poll the actual execution and inspect `step`/`tasks` |

PostgreSQL/PostGIS, GeoServer, Redis/Celery, remote OGC services, object/media
storage, credentials, and browser services are downstream prerequisites. They
were not verified by a CPU package import; label each unavailable gate
explicitly in a handoff.
