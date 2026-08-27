# Permissions, identity, and authentication reference

## Two authentication systems and one authorization bridge

| Layer | What it authenticates or authorizes | Evidence to collect |
|---|---|---|
| GeoNode Django | local users, sessions, OAuth2 tokens, allauth/OIDC login, Django backends | authenticated user, session/token status, `is_staff`/`is_superuser`, and login configuration |
| GeoNode guardian/security | object-level resource permissions and computed group/virtual permissions | resource permission specification, user/group membership, cache state, and resource subtype |
| GeoServer security | internal GeoServer users, OAuth2 relying-party filter, filter chains, and role services | selected filter, chain, principal, resolved roles, and GeoServer log entry |
| GeoFence | layer/service/request/area authorization after GeoServer identifies the principal | matching workspace/layer/user/group rule, service/request decision, cache state, and rule-sync timestamp |
| GeoNode proxy/bridge | URL safety, host allowlisting, header/token forwarding, and GeoServer path mediation | normalized target URL, safe-host decision, forwarded route, and response status |

A browser session at GeoNode is not a GeoServer internal account. GeoNode uses
an internal GeoServer administrator identity for catalog and rule management;
that identity must never be substituted for an end user or exposed to a client.
End-user access normally crosses the GeoServer OAuth2 filter, while GeoNode's
Django/guardian decision remains the source for resource permissions.

## GeoServer REST role service

The role service is a separate authorization lookup from OAuth2 token
validation. Configure a role service named exactly as the deployment expects
(for the bundled GeoNode integration, `geonode REST role service`) and point it
at the same canonical GeoNode base URL used by the GeoServer process.

| Role-service field | GeoNode route or value | Expected JSON selection |
|---|---|---|
| Base server URL | GeoNode base URL | must be reachable from GeoServer, including the deployed path prefix |
| Roles endpoint | `/api/roles` | `$.groups` |
| Admin-role endpoint | `/api/adminRole` | `$.adminRole` |
| Users endpoint | `/api/users` | `$.users[0].groups` for the selected user response |
| Administrator role | deployment role mapping | normally the role returned as `admin`; verify rather than guessing |
| Group administrator role | deployment role mapping | use the role chosen by the GeoServer security policy |

The current endpoints return all known group names plus an administrator role;
user lookup accepts the path's username and can fall back to email lookup. They
are protected by the configured API-auth mechanism when `OAUTH2_API_KEY` is
set, and the deployment must also restrict network access as appropriate. If
that key is absent, the code path intentionally does not require the API-key
header; treat that as an unsafe production condition, not as a successful
security setup. Never print or embed the key in a public recipe.

Before blaming GeoServer, inspect the three endpoint responses in a protected,
non-production context and validate JSON shape, user name, group names, and
admin role. A role response can be correct while a GeoFence layer rule still
denies access.

## OAuth2/OIDC bridge

GeoNode acts as an OAuth2/OIDC provider for the GeoServer relying party. The
exact paths depend on the deployment prefix, but the default contract contains:

| Concern | GeoNode-side contract | GeoServer-side counterpart |
|---|---|---|
| token issuance | `/o/token/` | access-token URI in `geonode-oauth2` |
| authorization | `/o/authorize/` | user authorization URI |
| token inspection | `/api/o/v4/tokeninfo/` | check-token endpoint |
| browser login | GeoServer login endpoint named by `LOGIN_ENDPOINT` | OAuth2 filter login endpoint |
| browser logout | GeoServer logout endpoint named by `LOGOUT_ENDPOINT` | OAuth2 filter logout and form logout chain |
| scopes | `read`, `write`, `groups` unless deliberately changed | filter scope list compatible with the client |
| client registration | Django OAuth Toolkit application for GeoServer | same client identifier and secret, obtained through secret management |
| redirect | canonical GeoServer UI URL | registered redirect URI must match scheme, host, prefix, and slash policy |

The OAuth2 filter should be named `geonode-oauth2` for the documented
integration. Its redirect-entry-point choice, endpoint names, client material,
role source, and TLS settings must be reviewed together. Do not solve a
redirect mismatch by accepting arbitrary redirect URIs.

## Filter-chain checklist

Review and save the GeoServer authentication configuration after each coherent
change. Confirm the deployment's intended filter order for:

- `web` — browser login and logout behavior;
- `rest` — authenticated REST/catalog calls;
- `gwc` — cache requests with the intended token/cookie behavior;
- `default` — fallback OGC and other routes;
- `webLogin` and `webLogout` — include the GeoNode login/logout endpoints;
- `formLogoutChain` in the form logout configuration — include the same logout
  endpoint, with and without a trailing slash only if the deployment requires
  both forms.

A filter can authenticate a principal while a missing role service leaves the
principal with no useful roles. A role service can return roles while the wrong
filter chain never invokes it. Diagnose those as separate stages.

## Resource permissions and compact rights

GeoNode's UI commonly exposes compact rights. The effective permissions are
expanded by resource type and subtype:

| Compact right | Typical effective permissions |
|---|---|
| `view` | `view_resourcebase` |
| `download` | view plus `download_resourcebase` for downloadable resources |
| `edit` | view/download plus metadata, dataset-data, and/or dataset-style changes where supported |
| `manage` | change metadata, delete, change permissions, and publish/unpublish capabilities |
| `owner` | owner permissions plus dataset administration and download as applicable |
| `none` | no effective permission |

Dataset subtypes matter. Vector and vector-time datasets can expose data edits;
raster/vector datasets can expose style edits; documents and maps do not gain
those dataset-specific rights. Review the effective expanded list rather than
assuming every `edit` right has the same meaning.

Resource permission views are under `/security/permissions/<resource-id>`;
bulk updates are under `/security/bulk-permissions/`. The conceptual payload
has `users` and `groups` mappings to extended permission names. Apply changes
only as the owner, administrator, or a principal with
`change_resourcebase_permissions`; check the response and then verify the
GeoServer-side rule result.

GeoFence maps effective permissions to service decisions. The normal policy
shape is:

| Effective permission | Typical GeoFence consequence |
|---|---|
| view or style change | WMS and GWC allowed |
| view/download/edit | WPS allowed, with download restrictions where supported |
| download without edit on vector | WFS allowed but transaction, lock, and feature-with-lock requests denied |
| download or edit | WFS for vector, WCS for raster |
| download plus view/edit | may include a wildcard service allowance; review the generated rule rather than granting it manually |

This is an implementation-oriented default, not a substitute for the
organization's policy. WPS/GWC extensions, GeoServer version, cache behavior,
and GeoFence rule precedence can change the observed result.

## Groups and roles

A GeoNode `GroupProfile` has an underlying Django `Group`, a slug, access mode,
and `GroupMember` rows with `member` or `manager` roles. Group managers receive
computed management permissions for resources in their group. Private group
visibility and resource permissions are separate decisions: a group can be
allowed to view a resource while its private profile remains hidden from
non-members.

If social login group mapping is enabled, make provider claims and local slugs
agree. The group-role mapper accepts names shaped like `group` or
`group.role`; a role containing `manager` promotes the local member. Configure
exactly one synchronization policy:

- `FULL_SYNC`: every login mirrors provider group/role data and removes local
  memberships not present in the claim;
- `SAFE_SYNC`: missing group/role keys preserve existing memberships, but a
  present empty list still performs a full removal;
- `NO_SYNC`: provider group data is ignored and local administration remains the
  source of truth.

A missing claim, an empty claim, and a claim with an unknown slug are different
cases. Record which case occurred before repairing a stale or unexpectedly
removed membership.

## Remote services and proxy safety

Service registration validates a safe URL and probes the selected service type.
The `Service` record stores a unique base URL, service method/type/version, and
optional encrypted/auth-config-backed access details. Use the supported auth
handler rather than embedding credentials in a URL or creating ad-hoc headers.

The generic proxy combines:

- `SAFE_URL_CHECK_ENABLED` and the common safe-URL validator;
- a registry containing the GeoNode host, configured `PROXY_ALLOWED_HOSTS`, the
  GeoServer host, and hosts from registered remote OGC links;
- optional path/query needles that can allow a carefully reviewed endpoint;
- host validation after URL normalization and private-address protections;
- request header/token forwarding and response handling.

A host may be registered because a remote link exists, then become stale after
that link is deleted; the registry periodically reinitializes. Never use a
needles setting as a general bypass, and never set the internal GeoServer proxy
path's `safe_url` behavior on a generic user-controlled route.
