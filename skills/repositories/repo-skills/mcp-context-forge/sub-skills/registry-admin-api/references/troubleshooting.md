# Registry/Admin API troubleshooting

Use this reference for common failures around ContextForge registry entities,
Admin/API route families, pagination, schemas, catalog/tags, import/export, and
safe smoke checks.

## Fast triage checklist

1. Confirm liveness: `GET /health`.
2. Confirm route family: canonical `/v1/...`, legacy alias, or Admin `/v1/admin/...`.
3. Confirm feature flags: Admin API/UI, A2A, catalog, legacy aliases.
4. Confirm bearer token is present for protected routes.
5. Confirm endpoint pagination shape: main cursor/array vs Admin page object.
6. Confirm payload wrapper key: `tool`, `server`, `resource`, `prompt`, or
   `agent` where required.
7. Confirm visibility/team filters and inactive rows.
8. Confirm duplicate/conflict key: tool/server/gateway/prompt `name`, resource/root `uri`.

## 401/403 authentication and authorization symptoms

| Symptom | Likely cause | What to check |
|---|---|---|
| `401` with message like authorization token required | Missing bearer token or malformed `Authorization` header | Send `Authorization: Bearer <token>`; do not pass tokens in query params. |
| `401` after token refresh | Token expired, signed with wrong secret/issuer/audience, or not accepted by server mode | Mint/obtain a token from the running environment. |
| `403` on create/update/delete | RBAC denied or token lacks permission | Use the auth/RBAC sub-skill for permission interpretation; from this sub-skill, verify the route and entity operation. |
| `403` with team mismatch/access issue | Request body `team_id` conflicts with token team scope | Remove `team_id`, use the token's team, or obtain a token for the intended team. |
| `403` for private/team create with public-only token | Token scope is public-only | Use `visibility: "public"` or obtain team-scoped credentials. |

Keep security semantics centralized: do not re-implement token interpretation in
registry route fixes.

## Admin API/UI disabled or wrong path

| Symptom | Likely cause | Fix |
|---|---|---|
| `/v1/admin/tools` returns `404` | `MCPGATEWAY_ADMIN_API_ENABLED=false` | Enable Admin API or use main `/v1/tools` if Admin features are not required. |
| `/admin/tools` returns `404` but `/v1/admin/tools` works | Legacy aliases disabled | Switch clients to `/v1/admin/...`. |
| `/` does not redirect to Admin UI | `MCPGATEWAY_UI_ENABLED=false` or static UI missing | Use API endpoints directly or enable/build UI. |
| Admin HTML partial works but JSON client parsing fails | Client called an HTMX partial route | Use the JSON list route, not `/partial`. |
| Admin form route fails CSRF | Admin route has Admin CSRF dependency | Use programmatic `/v1/...` API route when possible, or provide the Admin session/CSRF flow. |

Admin UI routes are not the service source of truth. If behavior differs between
UI and API, compare which service method each route calls.

## Main array vs cursor vs Admin page shape

| Received shape | Endpoint family | Fix if client expected another shape |
|---|---|---|
| `[...]` | Main API default | Add `include_pagination=true` or parse array. |
| `{ "tools": [...], "nextCursor": "..." }` | Main API with cursor | Read the route-specific entity key and `nextCursor`; do not look for `data`. |
| `{ "data": [...], "pagination": {...}, "links": {...} }` | Admin API page list | Use `page`/`per_page`, `pagination.has_next`, and `links.next`; do not look for `nextCursor`. |

Difficult case: a client assumes cursor pagination but calls an Admin endpoint.
Do not add `nextCursor` to Admin responses as a quick fix. Either switch the
client to the main endpoint or teach it page pagination.

## Duplicate names and conflicts

| Entity | Conflict key | Typical status | Resolution |
|---|---|---|---|
| Tool | `name` | `409` | Reuse/update existing tool, reactivate inactive tool, or choose a new name. |
| Gateway | `name`, URL, or visible name/slug ambiguity depending on operation | `409` | Poll by ID where possible; keep names/slugs unique in visible scope. |
| Server | `name` | `409` | Reuse/update existing virtual server or choose a new name. |
| Prompt | `name` | `409` | Reuse/update existing prompt or choose a new name. |
| Resource | `uri` within visibility/team scope | `409` | Choose a new URI or update the existing resource. Resource names may repeat. |
| Root | `uri` | validation/conflict | Use an allowed URI and update/delete intentionally. |
| Import | per-entity key | status errors/warnings | Choose `skip`, `update`, `rename`, or `fail`. |

For duplicate REST tool registration, first list visible active/inactive tools
with `gateway_id=null` and matching `name`. If the existing tool is intended,
reuse it in server associations rather than deleting and recreating it.

## Tool/server association mistakes

Symptoms:

- Server create succeeds but `GET /v1/servers/{id}/tools` returns no tools.
- Tool appears in `/v1/tools` but not through a virtual server.
- Deactivating A2A agent unexpectedly removes a tool from a server.

Checks:

1. Server associations usually expect entity IDs in `associated_tools`,
   `associated_resources`, and `associated_prompts`.
2. Confirm the tool is enabled; default lists hide inactive rows.
3. Confirm token visibility can see both the tool and server.
4. Confirm the tool is not deactivated through a gateway or A2A state cascade.
5. For gateway-derived tools, refreshing or disabling the gateway can alter child
   tool state.
6. Route live MCP transport/session failures for the virtual server to the
   transport sub-skill; registry association checks stop at list/read state.

## Visibility/team filter surprises

Symptoms:

- Admin sees an entity but API token does not.
- A list is empty for a team token.
- `team_id` query returns public rows outside the expected team.

Checks:

- Token scoping controls what rows are visible before explicit filters apply.
- Public rows can be visible across team contexts depending on the route/service.
- `team_id` query narrows team-owned rows but does not mean "hide all public".
- Private rows generally require owner/admin visibility.
- Imported rows may be assigned to the importing user's team context.

Use the auth/RBAC sub-skill for exact permission derivation; use this sub-skill
for endpoint, filter, and service ownership diagnosis.

## Lock and concurrent update conflicts

Possible surfaces:

- Gateway async lifecycle: creates/updates/deletes can return `202 Accepted` and
  pending/deleting status. Poll `GET /v1/gateways/{id}` and respect `Retry-After`.
- Gateway refresh: concurrent refresh/init work may be serialized by gateway
  locks; retry after current lifecycle work completes.
- Resource update: concurrent update/content locks can return bad-request style
  failures.
- Import: long-running import tracks status by `import_id`; do not assume failure
  just because a client timed out.

Safe approach:

1. Poll the status/read route by stable ID.
2. Do not retry create blindly if the first response may have been lost; list or
   get by ID/name first to avoid duplicates.
3. For async gateway pending records, let lifecycle finish or delete intentionally.

## JSON Schema/OpenAPI generation failures

| Symptom | Likely cause | Fix |
|---|---|---|
| `400` security validation failed | Target URL or OpenAPI URL blocked/invalid | Use an allowed HTTP(S) URL reachable from ContextForge. |
| `404` path/method not found | Exact path or method absent from spec | Match the path parsed from `url` and correct `request_type`. |
| `502` fetching spec | Spec server unreachable or returned an error | Check `openapi_url`, DNS/network, and that it returns JSON. |
| `input_schema` is null | Operation has no JSON request body or only query params | Author schema manually or adjust integration mapping. |
| `output_schema` is null | No JSON 200/201 response schema | Decide whether output schema is optional for the tool. |
| Tool create `422` after schema generation | Generated schemas inserted into an invalid tool payload | Check required tool fields and JSON types. |

## Import/export issues

| Symptom | Likely cause | Fix |
|---|---|---|
| Import validation failed | Missing top-level `version`, `exported_at`, `entities`, or required entity fields | Validate envelope before calling import. |
| Imported server lacks tools | Export excluded dependencies or selected entities omitted tools | Re-export with dependencies or select referenced tools/resources/prompts. |
| Conflict during import | Existing entity has same key | Select conflict strategy intentionally. |
| Root export/import denied | Root operations are system-config/admin scope | Use proper admin credentials or exclude roots. |
| A2A agents missing from export | Standard export/import entity coverage excludes A2A agents | Use A2A API separately unless repository behavior changed. |

## Catalog and tags issues

- Catalog route returns disabled/not found: check `MCPGATEWAY_CATALOG_ENABLED`.
- Catalog registration returns `409`: catalog server already registered as a
  visible gateway; reuse existing gateway or choose a custom name if supported.
- Catalog list empty: relax `category`, `provider`, `auth_type`, `tags`,
  `show_registered_only`, and `show_available_only` filters.
- Tag list empty: check entity type filter and token visibility.
- Tag appears in entity payload but not tag API: confirm cache invalidation after
  recent mutations, or read the entity directly to verify persisted tags.

## Safe API smoke helper failures

The bundled smoke helper is read-only by default.

- Health fails: wrong `--base-url`, server not running, reverse proxy path issue,
  or `/health` blocked by infrastructure.
- Health succeeds, version/list fails `401`: token missing or invalid.
- Version/list fails `403`: token valid but lacks permission.
- List endpoint fails `404`: wrong path, feature disabled, or legacy/canonical
  mismatch.
- JSON parse fails: response is HTML/redirect/error page; print status/body and
  verify URL/path and Admin UI vs API route.

Run:

```bash
python scripts/contextforge_api_smoke.py --help
```

from any current directory; the script has no source-checkout dependency.
