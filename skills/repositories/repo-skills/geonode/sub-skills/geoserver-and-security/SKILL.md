---
name: geoserver-and-security
description: "Configure and troubleshoot GeoServer-backed OGC publication,
  OAuth2, permissions, groups, remote services, and the GeoNode proxy."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# GeoServer and security

Use this skill when a GeoNode task crosses the GeoNode Django boundary into
GeoServer, GeoFence, an OAuth2/OIDC provider, a remote OGC service, or the
GeoNode proxy. Route general installation and container readiness to the
setup-and-configuration skill; route resource payloads and upload validation to
resource-and-api; route harvest scheduling to harvesting-and-admin.

## First classify the boundary

Before changing anything, identify which plane is failing:

1. **GeoNode/Django plane** — session or OAuth2 token validation, Django
   authentication backends, guardian object permissions, GroupProfile membership,
   and `/security/` views.
2. **GeoServer plane** — GeoServer's internal users, OAuth2 authentication
   filter, filter chains, role service, GeoFence rules, workspaces, stores, and
   OGC operations.
3. **Bridge plane** — the URLs and secrets that let GeoNode and GeoServer call
   one another, the reverse proxy, TLS trust, and the remote-service registry.

A successful Django login is not proof that GeoServer authentication,
GeoServer authorization, or GeoFence synchronization is working. Conversely, a
GeoServer administrator credential is not a GeoNode user credential.

## Gate the work

Ask for or verify the target topology before making a live change:

- GeoServer is running and reachable from GeoNode; GeoNode is reachable from
  GeoServer; external PostgreSQL/PostGIS, Redis/Celery, reverse proxy, and
  remote OGC services are available where the workflow needs them.
- The deployment owns a secret-management path for GeoServer admin credentials,
  OAuth2 client material, API keys, and remote-service credentials. Never place
  secrets in this skill, source control, shell history, URLs, or diagnostic
  output.
- GeoServer has compatible OAuth2 and GeoFence extensions when those features
  are enabled. Browser, live GeoServer, TLS, remote endpoint, and service-backed
  tests are optional gates, not package-import checks.
- The operator has a rollback or backup plan before changing GeoServer security,
  filter chains, or authorization rules.

The supplied CPU/Python environment does not verify any external service gate.
Treat all live publication, OAuth2 handshake, TLS trust, GeoFence, Redis/Celery,
PostgreSQL/PostGIS, reverse-proxy, browser, and remote OGC observations as
unverified until tested in the target deployment.

## Choose the configuration path

- For URL or topology work, read [the GeoServer reference](references/geoserver-reference.md)
  and compare internal, public, and browser UI URLs before editing settings.
- For identity, roles, resource permissions, or group synchronization, read
  [permissions and auth](references/permissions-and-auth.md).
- For an error or unexpected access result, use the status-code decision tree in
  [troubleshooting](references/troubleshooting.md), preserving the failing URL,
  request type, user/group context, and service logs without secrets.

## Configure the URL contract

Keep these values intentional and coherent:

- `GEOSERVER_LOCATION`: GeoNode's server-to-server GeoServer base URL; it must
  resolve from the GeoNode process and normally end in `/`.
- `GEOSERVER_PUBLIC_LOCATION`: the canonical externally reachable GeoServer
  base URL used in capabilities, links, and browser-facing OGC URLs.
- `GEOSERVER_WEB_UI_LOCATION`: the browser/admin UI base URL; it may differ
  from the public OGC URL behind a reverse proxy.
- `OGC_SERVER["default"]`: align `BACKEND`, `LOCATION`, `PUBLIC_LOCATION`,
  `WEB_UI_LOCATION`, login/logout endpoint names, security toggles, write mode,
  timeout/retry values, and GeoFence URL.

Do not “fix” a bad base URL by making the proxy accept arbitrary hosts. Normalize
scheme, host, path prefix, port, and trailing slash together, then test both a
capabilities request and a browser redirect.

## Operate safely

For publication or synchronization, establish the workspace and layer
identifier first, then distinguish local GeoServer-managed datasets from
remote-service resources. Inspect command help and select a narrow filter
before using synchronization commands. Permission updates can write GeoFence
rules and invalidate caches; style, layer, thumbnail, attribute, and metadata
synchronization can call GeoServer and may enqueue work.

For remote services, register only a safe, reachable base URL, use the service's
supported type and version, and use an auth configuration backed by a secret
store when authentication is required. The generic proxy must remain protected
by safe-URL validation and an allowlisted hostname registry. A remote link being
stored in GeoNode is not proof that the endpoint is available or trustworthy.

## Validate the outcome

A complete validation records:

- the effective settings (with secrets redacted), canonical URL normalization,
  and whether the target service gate was available;
- GeoNode-side authentication and guardian permission result;
- GeoServer-side authentication result, resolved roles, workspace/layer rule,
  and the exact OGC operation tested;
- expected status/content type, relevant GeoNode and GeoServer log correlation,
  and any cache or asynchronous synchronization delay;
- unverified prerequisites and the next service-backed check.

Prefer a mocked helper or URL-construction test when no service is provisioned.
Never report a mock, import, or static check as proof of live WMS/WFS/WCS/CSW,
OAuth2, GeoFence, TLS, or proxy behavior.

## Hard safety rules

- Do not generate GeoServer launchers, password-bearing curl commands, sample
  client secrets, API keys, or plaintext credential examples.
- Do not disable TLS verification, safe-URL checks, GeoFence, or the OAuth2 API
  key merely to make a test pass.
- Do not grant anonymous or wildcard access while diagnosing a private layer.
- Do not use destructive rule purges, broad permission rewrites, or unscoped
  synchronization without explicit approval and a recovery plan.
