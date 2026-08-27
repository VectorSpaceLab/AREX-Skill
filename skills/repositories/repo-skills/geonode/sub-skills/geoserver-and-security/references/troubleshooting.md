# GeoServer and security troubleshooting

Use the smallest reproducible request and keep four facts together: effective
URL, HTTP method/service/request, authenticated principal or test persona, and
workspace/layer. Redact tokens, cookies, passwords, API keys, and auth headers.
Compare GeoNode, GeoServer, reverse-proxy, and worker logs by timestamp or a
non-secret correlation identifier.

## Status-code decision tree

| Symptom | First boundary to inspect | Likely causes | Safe next checks |
|---|---|---|---|
| `401` from `/api/roles`, `/api/users`, or `/api/adminRole` | GeoNode role-service gate | missing/incorrect API-key auth, wrong path prefix, ingress policy, or request not from an allowed service network | Check effective base URL, protected request policy, reverse-proxy access log, and redacted JSON response. Do not disable the key. |
| `401` from `/gs/ows` or GeoServer REST | GeoServer authentication bridge | absent/expired token, wrong OAuth2 filter, wrong filter chain, or invalid internal catalog credentials | Separate browser OAuth2 from server-side catalog access; inspect the relevant GeoServer log and token lifecycle. |
| `403` for a known layer | authorization, not necessarily authentication | GeoFence rule mismatch, stale guardian-to-GeoFence sync, wrong workspace/layer name, group membership, or anonymous policy | Compare effective GeoNode permissions, resolved roles, exact rule, and cache state with a disposable test persona. |
| `403` from `/proxy/` | proxy safety | unsafe scheme/URL, host not in registry, private DNS/IP, or needles policy not matched | Normalize the URL, inspect allowed-host inputs, and test a harmless approved host. Never bypass safe-URL checks. |
| `404` or HTML at an OGC route | base URL/reverse proxy | duplicated path prefix, wrong trailing slash, service not installed, or route sent to the wrong application | Compare internal and public base URLs and request a capabilities document from each network position. |
| `5xx`, timeout, or connection refused | service availability | GeoServer/Tomcat down, DNS/TLS failure, firewall, PostgreSQL/PostGIS dependency, overloaded service, or worker outage | Check DNS/TCP/HTTP readiness from the calling process and inspect service health/logs. Retries do not prove availability. |

A `401` proves only that one boundary rejected the request. A `403` can be
correct policy. Always identify which application generated the response and
whether the response passed through the GeoNode bridge.

## OAuth2 redirect mismatch

**Symptoms:** login returns to the wrong host/path, GeoServer reports an
invalid redirect, login loops, or the callback succeeds but the user is not a
GeoServer administrator.

1. Compare `SITEURL`, `GEOSERVER_PUBLIC_LOCATION`, and
   `GEOSERVER_WEB_UI_LOCATION` with the externally visible reverse-proxy
   scheme, host, port, and path prefix.
2. Compare the OAuth2 application's registered redirect URI with the GeoServer
   OAuth2 filter value character-for-character. Check the slash policy and
   whether a proxy strips or adds a prefix.
3. Verify the filter's authorization/token/check-token/logout endpoints point to
   the same GeoNode instance and prefix.
4. Verify the GeoNode `LOGIN_ENDPOINT` and `LOGOUT_ENDPOINT` names equal the
   GeoServer filter and saved logout-chain names.
5. Re-authenticate in a clean browser session after configuration changes; an
   old session/token can obscure a fixed redirect.

Do not broaden redirect registration or turn off TLS verification to hide a
mismatch. If GeoServer cannot validate an HTTPS GeoNode endpoint, install the
correct CA chain in the GeoServer JVM/runtime trust store and retry the same
request.

## Role service returns stale or incomplete roles

**Symptoms:** a GeoNode administrator authenticates but lacks the GeoServer
administrator role; a newly added group is absent; or a removed membership
still appears.

1. Query the role endpoints through the protected service path in a controlled
   environment and confirm the user identifier and JSON paths.
2. Check that GeoServer's selected role service is the GeoNode REST role service
   and that the OAuth2 filter actually selects it.
3. Check the role-service base URL, network reachability, API-key policy, and
   ingress allowlist. A correct response from a developer workstation does not
   prove GeoServer can reach it.
4. Re-check the local `GroupProfile` slug, underlying Django group name, and
   `GroupMember` role. For social login, record whether the provider sent a
   missing, empty, or populated groups/roles claim.
5. Apply the configured `FULL_SYNC`, `SAFE_SYNC`, or `NO_SYNC` semantics and
   re-login only after confirming the desired source of truth.
6. Clear or expire only the relevant application/session/role caches using the
   deployment's supported procedure. Do not globally purge caches as a first
   response.

Role lookup and layer authorization are independent. After roles are repaired,
re-test the exact layer and inspect GeoFence precedence and cache invalidation.

## Private layer is unexpectedly public or denied

**Symptoms:** anonymous WMS/WFS access succeeds, or an allowed group receives
`403` after a permission edit.

- Compare the compact right with its expanded permissions. `download` is not
  merely view, and dataset `edit` may include data/style rights.
- Check direct user, group, anonymous, owner, and computed group-manager entries
  in the resource permission view.
- Check `GROUP_PRIVATE_RESOURCES`, group access mode, and whether the user is a
  member or manager of the expected `GroupProfile`.
- Confirm the dataset's `alternate` and workspace match the GeoFence rule. A
  rule for a similarly named layer in another workspace is not equivalent.
- If `DELAYED_SECURITY_SIGNALS` is enabled, expect a dirty-state/worker delay;
  verify that the worker ran before judging the result.
- Verify GWC cache behavior separately. A previously cached public tile can
  outlive a permission change until the supported invalidation path runs.

Do not “fix” denial by adding an anonymous allow rule or by setting a broad
wildcard service rule. Repair the source permission and synchronize narrowly.

## Missing extension or incompatible GeoServer feature

**Symptoms:** WPS/WCS/GWC requests are absent, filter type is unavailable, role
service cannot be created, or GeoFence calls return an unknown endpoint.

1. Record the GeoServer version and the enabled extension/plugin versions.
2. Check that the deployment's GeoServer distribution includes the OAuth2,
   GeoFence, GWC, WCS, and WPS components needed by its settings and workflow.
3. Compare the selected backend flags (`GEOFENCE_SECURITY_ENABLED`,
   `WPS_ENABLED`, `WMST_ENABLED`) with the installed components; do not enable a
   feature first and diagnose the resulting noise.
4. Read the GeoServer startup log for extension load errors and the request log
   for route-specific failures.
5. If the component is unavailable, mark the service gate blocked and route to
   deployment/package compatibility work. Do not copy an arbitrary extension
   into a live data directory or claim a CPU import verified it.

## Bad base URL, reverse proxy, or capabilities links

**Symptoms:** internal hostnames leak into capabilities, browser links point to
an unreachable port, URLs contain duplicate `/geoserver/`, or GeoNode proxies a
request back to the wrong service.

- Check internal `LOCATION` versus public `PUBLIC_LOCATION` versus UI location.
- Check `SITEURL`, `FORCE_SCRIPT_NAME`, proxy path rewriting, and forwarded
  scheme/host headers.
- Confirm all base values have the intended trailing-slash behavior and that
  workspace/layer path joining is not performed twice.
- Request capabilities through direct GeoServer, GeoNode `/gs/`, and the public
  client route; compare service URLs in each document.
- Confirm response rewriting replaces only the configured internal/public
  GeoServer locations, not unrelated hostnames.

Do not make every host allowed in `ALLOWED_HOSTS` or `PROXY_ALLOWED_HOSTS` as a
shortcut. Keep the smallest registry that supports the declared services.

## TLS certificate or hostname failure

**Symptoms:** GeoServer cannot exchange OAuth2 tokens, role lookups fail with a
certificate error, or a remote OGC probe fails only over HTTPS.

- Verify the certificate hostname matches the URL GeoServer actually uses and
  that the complete CA/intermediate chain is available to the calling runtime.
- Install trust material in the correct GeoServer JVM/container or worker trust
  store according to the deployment's change procedure.
- Check expiration, key usage, proxy termination, and whether the service
  redirects HTTP to a different HTTPS hostname.
- Retry a non-mutating token/role/capabilities request and capture only the
  error class and endpoint, not tokens or client secrets.

Never set `verify=False`, accept a self-signed certificate blindly, or change
OAuth2 HTTPS enforcement solely to make a diagnostic request pass.

## GeoServer or remote service unavailable

**Symptoms:** connection refused, repeated retries, service probe failure,
remote service marked unavailable, or uploads/publication remain pending.

1. From the calling component, check DNS, TCP connectivity, HTTP status, and
   TLS separately. A browser check from another host is not sufficient.
2. Check GeoServer/Tomcat, PostgreSQL/PostGIS, Redis/Celery, and reverse-proxy
   readiness according to the workflow. A functioning Django page does not
   imply any of them is ready.
3. Inspect `TIMEOUT`, retry/backoff, pool sizes, and service cache expiration;
   avoid increasing retries until the root outage is known.
4. For remote services, re-probe the base URL and capabilities with the
   configured service type/version and auth handler. Check whether a provider
   changed its capabilities URL or certificate.
5. For a publication task, inspect the GeoNode task/dirty state and GeoServer
   catalog separately. Retry only the narrow failed operation after the service
   is healthy.

Record the service-backed gate as unverified when the target endpoint, browser,
credentials, or worker is not provisioned.

## Synthetic case: OAuth base URL mismatch

Given a GeoNode URL under a reverse-proxy prefix while GeoServer is configured
with a bare host, predict failure before changing anything:

- identify which of token, authorization, check-token, redirect, or logout URLs
  has the wrong prefix/scheme;
- identify whether the failure is generated by GeoServer, the OAuth provider,
  or the proxy;
- propose one canonical public URL and update the paired GeoNode/GeoServer
  fields together;
- validate with a non-mutating capabilities request and a fresh OAuth2 login;
- leave TLS, secrets, and redirect allowlists unchanged except for the approved
  exact URI.

## Synthetic case: stale GeoServer role synchronization

Given a user who was removed from a GeoNode group but can still access a private
layer, or a newly added manager receiving `403`:

- inspect the provider claim policy and local `GroupProfile`/`GroupMember` state;
- query the protected role endpoint for the user and compare returned groups;
- determine whether the error is stale role cache, stale GeoFence rule, delayed
  worker state, or a wrong workspace/layer identifier;
- synchronize only the affected resource or approved filtered set;
- invalidate the relevant supported cache and test both allowed and denied
  personas, without adding anonymous access or purging all rules.
