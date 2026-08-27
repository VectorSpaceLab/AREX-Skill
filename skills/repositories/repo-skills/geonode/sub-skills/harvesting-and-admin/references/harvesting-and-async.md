# Harvesting and asynchronous execution

## What GeoNode persists

A `Harvester` is a database configuration for one remote service. Its useful
operational fields are:

| Field | Meaning and safe operator action |
|---|---|
| `name` | Unique name; it is also used when scheduling periodic work. Do not casually rename it while jobs are active. |
| `remote_url` | Base URL of the remote service. Validate scheme, path, DNS, proxy, TLS, and authentication from the worker's network namespace. |
| `harvester_type` | Import path for a worker class. The built-in workers are GeoNode unified, OGC WMS, and ArcGIS REST. |
| `harvester_type_specific_configuration` | JSON object validated against the selected worker's schema. Change it only when the resulting resource refresh is planned. |
| `scheduling_enabled` | Enables scheduler decisions; `False` is the safe pause for one-time or maintenance work. |
| `harvesting_session_update_frequency` | Minutes between automatic harvesting sessions. |
| `refresh_harvestable_resources_update_frequency` | Minutes between remote resource discovery/refresh sessions. |
| `check_availability_frequency` | Minutes between availability checks. |
| `default_owner` | Local owner assigned to created/updated resources. |
| `harvest_new_resources_by_default` | Marks newly discovered resources for harvesting. Prefer `False` until the remote scope is reviewed. |
| `delete_orphan_resources_automatically` | Allows missing remote resources, or resources from a removed harvester, to delete linked local resources. Keep `False` unless deletion is intended and backed up. |
| `status` / `remote_available` | Current local lock/state and last remote health result. A status other than `ready` means the harvester is busy or recovering. |

`HarvestableResource` rows are discovered during a refresh. They carry a
remote identifier, title/type, `should_be_harvested`, last refresh/harvest
timestamps, success flag, message, and optional `geonode_resource` link. A
refresh does not necessarily import a local resource: select or mark rows
first, then perform harvesting.

A session is either `discover-harvestable-resources` (refresh) or `harvesting`.
Useful terminal statuses are `finished-all-ok`, `finished-all-failed`,
`finished-some-failed`, and `aborted`; in-flight statuses are `pending`,
`on-going`, and `aborting`. Inspect `total_records_to_process`, `records_done`,
`details`, `started`, `updated`, and `ended`. The harvester should return to
`ready` after finalization.

## Built-in worker configuration

All worker-specific configuration is a JSON object. Unknown keys are rejected
by the worker schema. The standard shapes are:

### GeoNode unified worker

Use the modern worker for a current remote GeoNode and confirm the remote API
and permissions before scheduling a large replication. Common options include:

```json
{
  "harvest_datasets": true,
  "harvest_documents": true,
  "copy_datasets": false,
  "copy_documents": false,
  "resource_title_filter": "water",
  "start_date_filter": "2024-01-01T00:00:00Z",
  "end_date_filter": "2024-12-31T23:59:59Z",
  "keywords_filter": ["flood"],
  "categories_filter": ["environment"]
}
```

The current worker queries the remote `/api/v2/resources/` shape and paginates
by ten. It supports datasets and documents; maps are deliberately not
reconstructed because the remote API does not expose enough map composition
information. Date filters are parsed as datetimes and converted to UTC. A
remote API response, auth policy, and any copying/file-download behavior are
service-backed and must be tested from the worker network, not inferred from a
successful configuration save.

### OGC WMS worker

Set `harvester_type` to the WMS worker and use an optional configuration such
as:

```json
{"dataset_title_filter": "coast"}
```

The worker requests WMS `GetCapabilities`, accepts versions 1.1.1 and 1.3.0,
extracts leaf layers, and maps them to remote datasets. It may use the linked
GeoNode service authentication configuration for basic auth. Verify the
capabilities document, XML namespace, usable CRS/bounds, and access to
thumbnails/links. WMS availability and layer harvest are network and remote
service gates; never use a production endpoint as a parser test.

### ArcGIS REST worker

The remote URL can be a REST services catalog ending in `rest/services` or a
specific `MapServer`/`ImageServer`. Configuration may be:

```json
{
  "harvest_map_services": true,
  "harvest_image_services": true,
  "resource_name_filter": "roads",
  "service_names_filter": ["Transportation"]
}
```

Only supported `MapServer` and `ImageServer` extraction paths are built in.
Catalog/service discovery, JSON responses, nested layers, DNS/TLS, and remote
permissions are service-backed. Filter before enabling automatic selection.

### Custom workers

A custom worker subclasses the base harvester interface and must supply
construction from a Django record, availability, resource count/listing,
remote-to-local resource type mapping, and resource retrieval. Add its import
path to `HARVESTER_CLASSES`; GeoNode always retains the built-in classes and
extends that list. Add a JSON schema via `get_extra_config_schema()` when the
worker has options. Validate the class import, schema, and a mocked/local
worker contract before adding a remote URL.

## Operation sequence

### Safe discovery and one-time harvest

1. Create the harvester with scheduling disabled, a least-privilege owner, and
   `delete_orphan_resources_automatically=False`.
2. Validate the JSON configuration without launching a harvest. Check the
   remote URL and authentication from the worker runtime.
3. Run **check availability**. It is synchronous and changes status through
   `checking-availability`; inspect `remote_available` and its timestamp.
4. Run **update harvestable resources**. This creates a refresh session and
   asynchronous discovery. Wait for the session to finish and inspect its
   details and counts.
5. Review titles, types, identifiers, and remote URLs. Set
   `should_be_harvested=True` only for the approved subset.
6. Run **perform harvesting**, then inspect the harvesting session and each
   resource's last message/success flag. Verify local resources and ownership.
7. Keep scheduling disabled until the result and workload are understood.

For continuous harvesting, first complete the one-time flow, then set the two
update frequencies and scheduling explicitly. A scheduler task runs roughly
at `HARVESTER_SCHEDULER_FREQUENCY_MINUTES` (default 0.5 minutes), but broker
latency and worker load add delay. A harvester's next-dispatch calculations
return no scheduled time when scheduling is disabled.

### Admin and API controls

The admin exposes availability, refresh, perform, abort-refresh,
abort-harvesting, and reset-status actions. It checks availability before the
mutating asynchronous actions and reports when the harvester is not ready.
The sessions admin is read-only; harvestable resources expose selection flags
and safe review fields.

The API exposes `/api/v2/harvesters/` and nested harvestable resources, plus
read-only harvesting sessions. Non-admin users can list harvesters, but changes
and actions require admin privileges. PATCHing a harvester status starts work:
`updating-harvestable-resources`, `harvesting-resources`, or
`checking-availability`. The server owns the return to `ready`; clients cannot
set `ready` explicitly. Do not change worker type/configuration and status in
one request. A worker configuration update deletes current harvestable rows
and schedules a new refresh, so treat it as a destructive refresh boundary.

## Celery topology and eager mode

The application autodiscovers tasks and defines named queues. Harvesting tasks
use `harvesting`; the session monitor and general coordination use `geonode`;
HTTP management jobs use `management_commands_http`; notifications use
`email`; permissions use `security`; upload workflows use specialized upload
queues. The production launcher starts beat, a general worker excluding
`harvesting`, and a dedicated `harvesting` worker. It is a topology reference,
not a safe helper to copy into a runtime skill.

The scheduler is a periodic task. Refresh discovery builds a Celery chord of
paged batches and a finalizer. Harvesting builds a chord of per-resource tasks
and a finalizer; larger workloads are split into resource-id chunk groups. The
configured `CHUNK_SIZE` and `MAX_PARALLEL_QUEUE_CHUNKS` bound how many resource
IDs are submitted in each batch. Dynamic expiry/time limits are calculated
from estimated per-resource duration plus buffers. The monitor can force a
failed finalization after its workflow deadline.

`ASYNC_SIGNALS=True` selects the configured broker/result backend (normally
Redis URLs); `False` selects local in-process signaling and the settings default
makes Celery eager. Test settings also use an in-memory broker/result backend
and eager propagation. Eager mode is useful for deterministic unit behavior,
but it does not prove a real broker, worker process, beat schedule, queue
binding, result backend, or network task can work. Conversely, `QUEUED` with no
progress is a worker/broker/queue gate until proved otherwise.

For a real service check, independently verify:

- the web process uses the same broker/result settings as workers;
- Redis/RabbitMQ is reachable from the worker and accepts the configured URL;
- beat is running once and has a writable schedule/state location;
- a general worker consumes `geonode` and other required queues;
- a harvesting worker consumes `harvesting` and is not excluded from it;
- the management-command worker consumes `management_commands_http`;
- result persistence/events are enabled when status inspection depends on them;
- PostgreSQL/PostGIS is healthy and task workers can open/close connections.

## Stalled harvest triage

Start with the persisted state, not a retry:

1. Record harvester id/name, status, remote URL (redacted if sensitive), last
   availability, session id/type/status, counts, details, and each failed
   resource message.
2. If `remote_available=False`, test DNS/TLS/auth/HTTP status and WMS/ArcGIS or
   GeoNode API shape from the worker network. Do not reset the status first.
3. If the session is `pending` or a management job is `QUEUED`, check broker
   connectivity, queue routing, worker registration, and worker logs.
4. If `on-going` has no progress, check database locks/connections, remote
   latency, task expiry, worker memory/time limits, and monitor settings.
5. If remote listing succeeds but individual rows fail, narrow the resource
   set and inspect `last_harvesting_message`; preserve successful rows and do
   not delete all harvestable rows.
6. If the session is terminal but the harvester is not `ready`, inspect the
   finalizer/error handler and confirm the correct session id before an admin
   reset. Reset is a recovery operation that clears the local busy lock; it
   does not finish or undo remote work.
7. After the cause is fixed, run one small approved resource, verify terminal
   state and local links, then resume scheduling gradually.

An abort marks pending work aborted or an ongoing session aborting; it does not
revoke every Celery task. Finalizers synchronize task completion. Allow the
workflow to settle and inspect results before starting a second session.
