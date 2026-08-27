# ContextForge registry/Admin API route map

This reference is the self-contained route map for registry and Admin API work.
Use it to choose the correct route family before editing clients or payloads.

## Route surface summary

| Surface | Typical path | Mounted when | Notes |
|---|---|---|---|
| Canonical API | `/v1/tools`, `/v1/gateways`, `/v1/servers` | Always for core routes | Primary programmatic surface. |
| Legacy aliases | `/tools`, `/gateways`, `/servers`, `/admin/...` | `LEGACY_API_ENABLED=true` | Deprecated shims for `/v1/*`; may include Sunset/Deprecation headers. |
| Admin API/UI router | `/v1/admin/...` and legacy `/admin/...` | `MCPGATEWAY_ADMIN_API_ENABLED=true` | HTMX/template-backed UI plus JSON endpoints; protected by permissions and Admin CSRF dependency. |
| Admin UI static/root | `/`, `/static/...`, `/favicon.ico` | `MCPGATEWAY_UI_ENABLED=true` and static files present | Root redirects to Admin UI. If UI disabled, root returns API info. |
| Health/readiness | `/health`, `/ready`, `/health/security` | Always root-level | `/health` is the safest unauthenticated liveness check. |
| Version diagnostics | `/v1/version`, legacy `/version` | Core router; auth/permission protected | Use for build/runtime diagnostics when token has permission. |
| OpenAPI docs | `/docs`, `/redoc`, `/openapi.json` | FastAPI docs config | Usually auth-protected by default. |
| OpenAPI schema generation | `/v1/tools/generate-schemas-from-openapi` | Direct app-mounted router | Versioned API endpoint for deriving tool schemas from an OpenAPI spec. |
| Catalog | `/v1/catalog` | `MCPGATEWAY_CATALOG_ENABLED=true` for behavior | v1-only catalog router; Admin twin is under `/admin/mcp-registry`. |

## Bearer-token request pattern

Most registry routes expect:

```http
Authorization: Bearer <token>
Content-Type: application/json
Accept: application/json
```

Use `/health` first because it does not prove credentials. Use `/v1/version` or
a read-only list endpoint next to prove the token and permissions. Route exact
RBAC/token-scope interpretation to the security sub-skill.

## Main entity routes

Canonical paths below use `/v1`. If legacy aliases are enabled, remove the
`/v1` prefix for the deprecated path. Main list endpoints are cursor-capable but
return plain arrays by default unless `include_pagination=true` is present.

| Entity | Main routes | Notes |
|---|---|---|
| Gateways | `GET /v1/gateways`, `POST /v1/gateways`, `GET /v1/gateways/{gateway_id}`, `PUT /v1/gateways/{gateway_id}`, `DELETE /v1/gateways/{gateway_id}`, `POST /v1/gateways/{gateway_id}/state`, `POST /v1/gateways/{gateway_id}/tools/refresh` | Gateway IDs, exact names, or exact slugs may resolve in some reads; ambiguous visible name/slug conflicts return `409`. Async lifecycle can return `202` and pending/deleting status. |
| Tools | `GET /v1/tools`, `POST /v1/tools`, `GET /v1/tools/{tool_id}`, `PUT /v1/tools/{tool_id}`, `DELETE /v1/tools/{tool_id}`, `POST /v1/tools/{tool_id}/state` | Tools support REST integration fields, schemas, tags, visibility, gateway filters, and invocation via RPC. |
| Resources | `GET /v1/resources`, `POST /v1/resources`, `GET /v1/resources/{resource_id}`, `GET /v1/resources/{resource_id}/info`, `PUT /v1/resources/{resource_id}`, `DELETE /v1/resources/{resource_id}`, `POST /v1/resources/{resource_id}/state`, `GET /v1/resources/templates/list`, `POST /v1/resources/subscribe` | Resource `uri` is the uniqueness key by scope; `name` is display text and may repeat. |
| Prompts | `GET /v1/prompts`, `POST /v1/prompts`, `GET /v1/prompts/{prompt_id}`, `POST /v1/prompts/{prompt_id}`, `PUT /v1/prompts/{prompt_id}`, `DELETE /v1/prompts/{prompt_id}`, `POST /v1/prompts/{prompt_id}/state` | `POST /v1/prompts/{prompt_id}` renders/executes a prompt with arguments. |
| Roots | `GET /v1/roots`, `POST /v1/roots`, `GET /v1/roots/export`, `GET /v1/roots/changes`, `GET /v1/roots/{root_uri:path}`, `PUT /v1/roots/{root_uri:path}`, `DELETE /v1/roots/{uri:path}` | Root management is an admin/system-config capability; roots are also part of export/import. |
| Servers | `GET /v1/servers`, `POST /v1/servers`, `GET /v1/servers/{server_id}`, `PUT /v1/servers/{server_id}`, `DELETE /v1/servers/{server_id}`, `POST /v1/servers/{server_id}/state`, `GET /v1/servers/{server_id}/tools`, `GET /v1/servers/{server_id}/resources`, `GET /v1/servers/{server_id}/prompts` | Virtual servers bundle associated tools/resources/prompts/A2A agents. Route live SSE/message behavior elsewhere. |
| A2A agents | `GET /v1/a2a`, `POST /v1/a2a`, `GET /v1/a2a/{agent_id}`, `PUT /v1/a2a/{agent_id}`, `DELETE /v1/a2a/{agent_id}`, `POST /v1/a2a/{agent_id}/state`, `POST /v1/a2a/{agent_name}/invoke`, `POST /v1/a2a/invoke`, `POST /v1/a2a/{agent_name}/jsonrpc` | Mounted only when A2A is enabled. State changes cascade to the associated tool. |
| Tags | `GET /v1/tags`, `GET /v1/tags/{tag_name}/entities` | Tags categorize gateways, servers, tools, resources, prompts, and A2A agents. |
| Export/import | `GET /v1/export`, `POST /v1/export/selective`, `POST /v1/import`, `GET /v1/import/status/{import_id}`, `GET /v1/import/status`, `POST /v1/import/cleanup` | Import supports `conflict_strategy`, `dry_run`, optional selection, and status tracking. |
| Search/version/metrics | `GET /v1/search`, `GET /v1/version`, `GET /v1/metrics`, `POST /v1/metrics/reset` | Covered here only as adjacent API smoke/diagnostic surfaces. |

## Admin route families

Admin routes live under `/v1/admin` canonically. With legacy aliases enabled the
same admin router is also available under `/admin`, which is the common Admin UI
path. Admin list routes use page pagination, not cursors.

| Admin family | Representative routes | Notes |
|---|---|---|
| Entity lists | `GET /v1/admin/tools`, `/servers`, `/resources`, `/prompts`, `/gateways`, `/a2a`, `/tags` | Return `data`, `pagination`, `links`. Support `page`, `per_page`, and entity-specific filters. |
| Entity partials/search/ids | `GET /v1/admin/tools/partial`, `/tools/search`, `/tools/ids`, and equivalent families | HTMX/UI support endpoints. Treat service layer as source of truth. |
| Entity CRUD | `POST /v1/admin/tools`, `POST /v1/admin/tools/{id}/edit`, `POST /v1/admin/tools/{id}/state`, `POST /v1/admin/tools/{id}/delete`; analogous gateway/resource/prompt/server/A2A routes | Admin UI often accepts JSON or form-compatible payloads. Some delete routes use POST for UI flows; REST-style delete routes also exist for gateways/tokens. |
| Gateway helpers | `POST /v1/admin/gateways/test`, `POST /v1/admin/gateways/discover-oauth` | Use for Admin UI connectivity/OAuth discovery checks. |
| OpenAPI schema generation | `POST /v1/admin/tools/generate-schemas-from-openapi` | Admin twin of the v1 API route, with Admin CSRF dependency. |
| Roots | `GET /v1/admin/roots/search`, `/roots/export`, `/roots/{uri:path}`, `POST /v1/admin/roots`, `/roots/{uri:path}/update`, `/roots/{uri:path}/delete` | Admin/system-config surface. |
| Import/export | `GET /v1/admin/export/configuration`, `POST /v1/admin/export/selective`, `POST /v1/admin/import/preview`, `POST /v1/admin/import/configuration`, `GET /v1/admin/import/status...` | UI wrappers around export/import services. |
| MCP registry catalog | `GET /v1/admin/mcp-registry/servers`, `POST /v1/admin/mcp-registry/{server_id}/register`, `GET /v1/admin/mcp-registry/{server_id}/status`, `POST /v1/admin/mcp-registry/bulk-register` | Admin catalog twin; v1 programmatic catalog route is `/v1/catalog`. |
| Plugins/observability/runtime | `/v1/admin/plugins...`, `/v1/admin/observability...`, `/v1/admin/runtime...` | Route plugin policy and observability details to the plugins/observability sub-skill. |

## Feature flags that change route presence

- `MCPGATEWAY_ADMIN_API_ENABLED=false`: Admin router is not mounted; Admin API/UI
  requests return missing-route style failures such as `404`.
- `MCPGATEWAY_UI_ENABLED=false`: static Admin UI/root redirect is not mounted;
  root returns API info instead.
- `LEGACY_API_ENABLED=false`: unversioned aliases are absent; use `/v1/...`.
- `MCPGATEWAY_A2A_ENABLED=false`: `/v1/a2a` is not included.
- `MCPGATEWAY_CATALOG_ENABLED=false`: catalog handlers return disabled/not-found
  behavior even though the v1 catalog router is known to the app.
- Optional routers such as observability, reverse proxy, ToolOps, cancellation,
  LLM, teams/tokens/RBAC, and plugins appear only under their feature flags.

## Health/version smoke sequence

1. `GET /health` without auth: proves process liveness only.
2. `GET /ready`: proves readiness; returns `503` when not ready.
3. `GET /v1/version` with bearer token: proves authenticated diagnostics route.
4. `GET /v1/tools?include_pagination=false` with bearer token: proves a normal
   registry list route and clarifies whether the token can see any tools.

Use the bundled `../scripts/contextforge_api_smoke.py` helper for this sequence.
