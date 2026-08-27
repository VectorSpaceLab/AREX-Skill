# GeoServer and OGC reference

This reference is for a GeoNode deployment that uses the GeoServer backend. It
is an operating contract, not a claim that GeoServer or any external service is
available. Substitute the deployment's managed secrets and URLs; do not put
secret values in commands or logs.

## Settings and URL matrix

| Setting | Consumer | Contract and diagnostic question |
|---|---|---|
| `GEOSERVER_LOCATION` | GeoNode server-side catalog, REST, GeoFence, and OGC calls | Can the GeoNode process resolve and reach this internal base URL? Does it have one trailing slash? |
| `GEOSERVER_PUBLIC_LOCATION` | capabilities, generated links, map clients, and proxy rewriting | Does a client outside the GeoNode process reach this exact scheme/host/path? Does it match the reverse-proxy prefix? |
| `GEOSERVER_WEB_UI_LOCATION` | links to the GeoServer administration UI | Does a browser reach the UI at this URL, even if OGC traffic uses a different public endpoint? |
| `OGC_SERVER.default.BACKEND` | backend selection | Is it `geonode.geoserver` for GeoServer-backed publication? |
| `OGC_SERVER.default.LOCATION` | effective internal OGC location | Does it agree with `GEOSERVER_LOCATION` after environment overrides? |
| `OGC_SERVER.default.PUBLIC_LOCATION` | effective public OGC location | Does it agree with `GEOSERVER_PUBLIC_LOCATION` and capability URLs? |
| `OGC_SERVER.default.WEB_UI_LOCATION` | effective UI location | Does it agree with the browser-facing GeoServer UI route? |
| `LOGIN_ENDPOINT` / `LOGOUT_ENDPOINT` | GeoNode-to-GeoServer OAuth2 bridge | Do the names exactly match the GeoServer OAuth2 filter and logout chain? |
| `USER` / `PASSWORD` | GeoNode's GeoServer catalog administration calls | Are these internal GeoServer admin credentials supplied only through a secret manager? |
| `GEONODE_SECURITY_ENABLED` | GeoServer security bridge | Is the setting intentionally enabled for the deployment? |
| `GEOFENCE_SECURITY_ENABLED` / `GEOFENCE_URL` | fine-grained layer and geographic authorization | Is the compatible GeoFence extension installed and is its endpoint reachable? |
| `BACKEND_WRITE_ENABLED` | writes from GeoNode to GeoServer | Is catalog/rule mutation intentionally enabled? Keep it off for read-only diagnostics. |
| `TIMEOUT`, `MAX_RETRIES`, `BACKOFF_FACTOR` | OGC and catalog client behavior | Are retries masking an outage, or is the endpoint simply slow/unavailable? |
| `WPS_ENABLED` / `WMST_ENABLED` | optional GeoServer services | Are the corresponding GeoServer extensions and policy rules installed before enabling? |

The defaults in a development environment are not production-safe. Change all
factory/default administrator credentials and rotate any copied OAuth2 or API
keys before exposure. Keep URLs free of embedded credentials.

## Route map

GeoNode adds a GeoServer bridge below `/gs/`. The important route families are:

| GeoNode route family | Downstream use |
|---|---|
| `/gs/ows` | shared OWS endpoint; use `service=WMS`, `WFS`, or `WCS` with a capabilities request |
| `/gs/wms`, `/gs/wfs`, `/gs/wcs`, `/gs/wps` | service-specific OGC routes |
| `/gs/<workspace>/<layer>/ows` and service variants | workspace/layer-specific OGC links |
| `/gs/gwc` | GeoWebCache requests and cache invalidation paths |
| `/gs/rest/layers`, `/gs/rest/styles`, `/gs/rest/workspaces` | mediated catalog/style/workspace operations |
| `/gs/acls` | GeoNode-generated read/write ACL view for GeoServer integration |
| `/gs/online` | service availability probe when the route is enabled |
| `/proxy/` | generic remote-link proxy; safe-host checks still apply |
| `/services/` | GeoNode remote-service registration and harvesting UI |
| `/catalogue/csw` | GeoNode catalogue/CSW endpoint when the local catalogue backend is selected |

The bridge rewrites GeoServer URLs in XML/JSON responses to the GeoNode `/gs/`
space where appropriate. If capabilities contain an internal hostname, inspect
`PUBLIC_LOCATION`, reverse-proxy routing, and response rewriting before changing
layer metadata.

## OGC service assumptions

- **WMS** supplies map images and capabilities. A view permission normally
  results in GeoFence WMS access; verify the exact operation and layer rule.
- **WFS** supplies vector feature access and downloads. Download-only policy
  must not accidentally allow write operations such as transactions, locks, or
  feature-with-lock requests.
- **WCS** supplies raster coverage access and downloads. Confirm that the
  coverage exists, the requested CRS/axis order is supported, and the WCS
  extension is installed.
- **WPS** is optional and policy-sensitive. A download or edit permission does
  not by itself prove that every WPS process or output should be exposed.
- **GWC** is the cache path used with map access. Permission changes can alter
  cache filters or require invalidation; stale tiles are not proof that the
  current GeoFence rule is wrong.
- **CSW** is a catalogue assumption, not a generic GeoServer guarantee. GeoNode
  commonly uses a local pycsw-backed endpoint or a configured HTTP catalogue.
  Confirm the selected `CATALOGUE.default.ENGINE` and `URL`; do not infer CSW
  availability from a successful GeoServer WMS request.

A service-backed check should request capabilities first, then the smallest
safe operation for the intended permission. Record HTTP status, content type,
service/version, workspace/layer identifier, and whether the response was
served through `/gs/`, direct GeoServer, or a remote service.

## Workspace and layer lifecycle

1. Choose the GeoNode dataset's `alternate` identifier and determine its
   workspace (usually the dataset workspace, not an arbitrary user input).
2. Confirm the matching GeoServer workspace, store, resource, and default style.
   A layer name collision or wrong workspace can look like a permission failure.
3. For a local dataset, allow the normal GeoNode publication/signal/task path to
   create or update the catalog entry. For a remote dataset, do not attempt a
   local GeoServer cascade unless its service method explicitly supports it.
4. After a change, compare GeoNode metadata and GeoServer catalog metadata,
   attributes, style, bounds, and links. Use a narrow, reviewed synchronization
   command when repair is needed.
5. If permissions changed, verify guardian state, GeoFence rules, cache state,
   and asynchronous dirty-state processing separately.

Useful management entry points include `sync_security_rules` and
`sync_geonode_datasets`. Inspect `manage.py <command> --help` first. The latter
can update permissions, attributes, thumbnails, bounds, metadata, and duplicate
links depending on flags; do not combine broad mutation flags during diagnosis.
A command may succeed locally while a later GeoServer or Celery call remains
pending.

## Safe diagnostic sequence

1. Redact secrets and print effective URL settings.
2. Resolve the internal GeoServer hostname and make a non-mutating HTTP
   capabilities or health request from the GeoNode runtime.
3. Test the same public OGC URL from the intended client network.
4. Check one known workspace/layer in GeoServer and one corresponding GeoNode
   dataset; compare identifiers exactly.
5. Test an anonymous, allowed-user, and denied-user request only with a
   disposable or approved test layer.
6. Inspect GeoNode, GeoServer, reverse-proxy, and worker logs using a shared
   timestamp/request identifier.
7. Only then decide whether the fault is URL routing, authentication, role
   lookup, GeoFence authorization, cache, data publication, or service outage.

Do not use production data, real access tokens, or administrator secrets in a
copy-pasted diagnostic request.
