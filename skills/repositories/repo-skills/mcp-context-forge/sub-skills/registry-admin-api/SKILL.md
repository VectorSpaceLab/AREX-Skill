---
name: registry-admin-api
description: "Operate ContextForge registry and Admin/REST APIs for entities,
  schemas, pagination, catalog, tags, and import/export."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Registry and Admin API

Use this sub-skill when the task is about ContextForge registry entities,
Admin/REST API behavior, entity schemas, service boundaries, catalog/tag
workflows, import/export, JSON Schema/OpenAPI tool generation, or safe API smoke
checks.

Do **not** use this sub-skill for MCP transport/session protocol behavior,
RBAC policy interpretation, plugin policy chains, or broad pre-merge validation.
Route those to sibling skills when available:
`../mcp-transports-federation/SKILL.md`, `../auth-rbac-security/SKILL.md`,
`../plugins-observability/SKILL.md`, and
`../development-validation/SKILL.md`.

## Fast route choice

- Need endpoint names, versioned vs legacy paths, or Admin API families: read
  [references/api-route-map.md](references/api-route-map.md).
- Need request/response payload shapes, Pydantic schema names, SQLAlchemy model
  ownership, or which service owns CRUD: read
  [references/entity-schemas-services.md](references/entity-schemas-services.md).
- Need cursor pagination, Admin page pagination, filters, or a client pagination
  bug: read [references/pagination-and-filtering.md](references/pagination-and-filtering.md).
- Need catalog, tags, export/import, conflict strategy, dry-run, or status
  tracking: read
  [references/import-export-catalog-tags.md](references/import-export-catalog-tags.md).
- Need REST/OpenAPI tool schema generation or REST API registration patterns:
  read [references/openapi-tool-generation.md](references/openapi-tool-generation.md).
- Need failure triage: read
  [references/troubleshooting.md](references/troubleshooting.md).
- Need a safe non-mutating live check: run
  [scripts/contextforge_api_smoke.py](scripts/contextforge_api_smoke.py).

## ContextForge API mental model

ContextForge is a FastAPI gateway for MCP/A2A/REST/gRPC federation. Registry
state is modeled as gateways, tools, resources, prompts, roots, virtual servers,
A2A agents, tags, catalog entries, and import/export envelopes. The Admin UI is
HTMX/templates-backed; API and service truth lives in routers, Pydantic schemas,
SQLAlchemy models, and services.

There are two main HTTP route surfaces:

1. Canonical `/v1/...` API routes for programmatic clients.
2. Backward-compatible unversioned aliases such as `/tools` and `/admin/...`
   when legacy route shims are enabled.

Root health endpoints `/health` and `/ready` are unversioned. The diagnostics
version endpoint is `/v1/version`, with a legacy `/version` alias when legacy
routes are mounted.

Most API calls require:

```text
Authorization: Bearer <jwt-or-session-token>
Content-Type: application/json
```

Leave token-scoping and RBAC semantics to the auth/security sub-skill; for this
sub-skill it is enough to know that missing or insufficient bearer credentials
usually surface as `401` or `403`, and list/create results are visibility/team
filtered by request context.

## Main registry entities

Use the entity names consistently:

- **Gateways**: upstream MCP servers or peer gateways; creating or refreshing a
  gateway can synchronize child tools/resources/prompts.
- **Tools**: executable operations; can be REST integrations or gateway/A2A
  derived tools. REST tools carry URL, method, schema, and passthrough mapping
  fields.
- **Resources**: readable data items or templates; URI is the important unique
  identifier.
- **Prompts**: reusable prompt templates and arguments.
- **Roots**: configured filesystem roots for resource policy/export.
- **Servers**: virtual servers that bundle associated tools, resources, prompts,
  and A2A agents.
- **A2A agents**: Agent-to-Agent integrations; activation/deactivation also
  affects the associated MCP tool.
- **Tags**: cross-entity categorization and discovery.
- **Catalog**: MCP registry catalog discovery and registration into gateways.
- **Export/import**: configuration envelopes for tools, gateways, servers,
  prompts, resources, and roots.

## Common workflow: register a REST API as a tool and bundle it

1. Check the service is alive: `GET /health`.
2. Obtain a bearer token with permissions for `tools.create`, `tools.read`,
   `servers.create`, and `servers.read`.
3. Optionally generate `input_schema` and `output_schema` from an OpenAPI spec
   with `/v1/tools/generate-schemas-from-openapi`; see
   [OpenAPI tool generation](references/openapi-tool-generation.md).
4. `POST /v1/tools` with body `{"tool": {...}, "team_id": null}` for REST
   tool creation. Handle `409` by reading existing tools and either reuse/update
   the existing tool or choose a new name.
5. `POST /v1/servers` with body `{"server": {"name": ..., "associated_tools":
   ["<tool-id>"]}}`.
6. Confirm with `GET /v1/servers/{server_id}/tools`.
7. Route actual MCP server connection/session debugging to the transport
   sub-skill; this sub-skill owns only registry/API state.

## Common workflow: fix a pagination mismatch

1. Identify the endpoint family.
2. Main endpoints such as `/v1/tools`, `/v1/servers`, `/v1/gateways`,
   `/v1/resources`, `/v1/prompts`, and `/v1/a2a` return plain arrays by default.
   Add `include_pagination=true` to get a cursor response with entity key plus
   `nextCursor`.
3. Admin endpoints such as `/v1/admin/tools` and `/admin/tools` use
   `page`/`per_page` and always return `data`, `pagination`, and `links`.
4. If a client expects `nextCursor` from an Admin endpoint, change the client to
   read `pagination.has_next` and `links.next` or call the matching main endpoint.

## Safe smoke check

The bundled helper is non-mutating by default and uses only Python stdlib:

```bash
cd <registry-admin-api skill directory>
python scripts/contextforge_api_smoke.py \
  --base-url http://localhost:4444 \
  --token "$MCPGATEWAY_BEARER_TOKEN" \
  --check-version
```

Without a token, it checks only `/health`. With a token, it can also read
`/v1/version` and list a read-only endpoint. Use `--help` for flags.

## Edit rules for future maintainers

- Keep this `SKILL.md` router-like; put route tables, schemas, long examples,
  and troubleshooting matrices in `references/`.
- Do not add links to a local checkout or generated verification reports.
- Keep scripts safe by default: read-only unless an explicit mutating flag is
  added and documented.
- If ContextForge moves inline routes out of the main app into module routers,
  update [references/api-route-map.md](references/api-route-map.md) and
  [references/entity-schemas-services.md](references/entity-schemas-services.md)
  together.
