# Entity schemas, payloads, models, and services

Use this reference when a task asks which schema to use, how a request body is
shaped, where CRUD logic belongs, or why a field is owned by authenticated
context rather than by client input.

## Source-of-truth layers

| Layer | What it owns | Working rule |
|---|---|---|
| FastAPI routers | Route paths, HTTP methods, dependency injection, status-code mapping, feature-flag mounting, and request-body embedding | Change route behavior here only when the HTTP contract changes. |
| Pydantic schemas | Create/update/read validation and JSON aliases | Check schema names before changing payloads; many read models emit aliases. |
| SQLAlchemy models | Persisted columns, relationships, uniqueness, ownership, visibility, and metrics relationships | Schema changes require migrations in normal repo work. |
| Services | CRUD/business logic, cache invalidation, gateway sync, import/export conversion, access-filtered queries | Prefer service changes over route duplication. |
| Admin UI templates/HTMX | Presentation and form/partial rendering | Do not treat templates as the API source of truth. |

## Main schema families

| Entity | Create schema | Update schema | Read schema | DB model | Service owner |
|---|---|---|---|---|---|
| Tool | `ToolCreate` | `ToolUpdate` | `ToolRead` | `Tool` | `ToolService` |
| Resource | `ResourceCreate` | `ResourceUpdate` | `ResourceRead` | `Resource` | `ResourceService` |
| Prompt | `PromptCreate` | `PromptUpdate` | `PromptRead` | `Prompt` | `PromptService` |
| Gateway | `GatewayCreate` | `GatewayUpdate` | `GatewayRead` | `Gateway` | `GatewayService` |
| Server | `ServerCreate` | `ServerUpdate` | `ServerRead` | `Server` | `ServerService` |
| Root | `RootCreate` | `RootUpdate` | `Root` | root service state | `RootService` |
| A2A agent | `A2AAgentCreate` | `A2AAgentUpdate` | `A2AAgentRead` | `A2AAgent` | `A2AAgentService` |
| Tags | `TagInfo`, `TaggedEntity` | n/a | `TagInfo`, `TaggedEntity` | tags stored on entity rows | `TagService` |
| Catalog | `CatalogListRequest`, `CatalogServerRegisterRequest`, `CatalogServerRegisterBody`, response schemas | n/a | `CatalogListResponse`, `CatalogServerRegisterResponse` | catalog file/config plus gateway rows for registrations | `CatalogService` |
| Pagination | `PaginationMeta`, `PaginationLinks`, cursor response schemas | n/a | `PaginatedResponse`, `CursorPaginated*Response` | service query helpers | `unified_paginate` via services |

## Request body shapes for main creates

FastAPI embeds body fields when a route has more than one body parameter. This
is why many main create endpoints use an entity wrapper key plus `team_id` or
`visibility`.

### Gateway create: raw schema body

`POST /v1/gateways` uses a raw `GatewayCreate` body because the route has only
one entity body parameter.

```json
{
  "name": "weather-mcp",
  "url": "http://localhost:9000/mcp",
  "description": "Weather MCP server",
  "transport": "STREAMABLEHTTP",
  "visibility": "public",
  "team_id": null,
  "tags": ["weather"]
}
```

### Tool create: wrapped body

`POST /v1/tools` uses `tool` plus optional root `team_id`. REST tool-specific
fields live inside `tool`.

```json
{
  "tool": {
    "name": "weather-current",
    "description": "Get current weather",
    "url": "https://api.example.test/weather/current",
    "integration_type": "REST",
    "request_type": "GET",
    "input_schema": {
      "type": "object",
      "properties": {"city": {"type": "string"}},
      "required": ["city"]
    },
    "output_schema": {"type": "object"},
    "visibility": "public",
    "tags": ["weather", "rest"]
  },
  "team_id": null
}
```

`ToolCreate` also accepts schema aliases `inputSchema` and `outputSchema` where
configured, but use snake_case in examples unless matching an existing client.

### Resource create: wrapped body

```json
{
  "resource": {
    "name": "service-config",
    "uri": "file:///srv/config.json",
    "description": "Service config",
    "mime_type": "application/json",
    "content": "{\"debug\": false}",
    "tags": ["config"]
  },
  "team_id": null,
  "visibility": "public"
}
```

`uri` is the unique identifier within the target visibility/team scope; `name`
is display text and may repeat.

### Prompt create: wrapped body

```json
{
  "prompt": {
    "name": "summarize-ticket",
    "description": "Summarize a support ticket",
    "template": "Summarize: {{ticket}}",
    "arguments": [{"name": "ticket", "required": true}],
    "tags": ["support"]
  },
  "team_id": null,
  "visibility": "public"
}
```

### Server create: wrapped body

```json
{
  "server": {
    "name": "support-assistant-server",
    "description": "Virtual server for support tools",
    "associated_tools": ["tool-id-1"],
    "associated_resources": [],
    "associated_prompts": [],
    "tags": ["support"]
  },
  "team_id": null,
  "visibility": "public"
}
```

The read schema exposes association names and IDs such as `associated_tools`,
`associated_tool_ids`, `associated_resources`, `associated_prompts`, and
`associated_a2a_agents`.

### A2A agent create: wrapped body

```json
{
  "agent": {
    "name": "research-agent",
    "agent_type": "openai",
    "endpoint_url": "https://agent.example.test/v1/chat/completions",
    "description": "External research agent",
    "auth_type": "bearer",
    "auth_value": "SECRET_REF_OR_ENV_NAME",
    "tags": ["a2a"]
  },
  "team_id": null,
  "visibility": "public"
}
```

A2A state changes cascade to the associated tool: deactivation removes it from
virtual server listings; reactivation restores it.

### Root create/update

Root routes use root schema fields directly:

```json
{"uri": "file:///workspace", "name": "workspace"}
```

Root operations are system-config/admin style operations. Do not treat root
management as ordinary user-owned content.

## Update, state, and delete patterns

- Update routes use the corresponding `*Update` schema and usually accept only
  changed fields.
- State routes use `POST /v1/<entity>/{id}/state?activate=false` for main API.
  Deprecated `/toggle` aliases may exist but should not be used in new clients.
- Delete routes use `DELETE /v1/<entity>/{id}` in main API. Admin UI may expose
  POST-based delete routes for form workflows.

## Ownership, team, and visibility fields

ContextForge entities commonly carry:

- `owner_email`: authenticated user who owns the entity.
- `team_id`: team owning or narrowing the entity.
- `visibility`: `private`, `team`, or `public`.
- `tags`: entity tags for filtering/cataloging.
- creation metadata: creator, IP, user agent, import batch, federation source.

Important operating rules:

1. Route handlers derive `owner_email`, final `team_id`, and creation metadata
   from authenticated request context. Do not trust a client-provided ownership
   field as authority.
2. Public-only tokens cannot create `team` or `private` registry entities; the
   route returns a forbidden response and asks for `visibility='public'` or a
   team-scoped token.
3. If a token carries a specific team and a request body names a different
   `team_id`, creates are rejected as access issues.
4. List services receive `user_email`, `token_teams`, `team_id`, and
   `visibility` filters; they apply access control before returning results.
5. Exact RBAC permission meaning belongs to the auth/security sub-skill; this
   sub-skill only preserves where the registry layer consumes the derived
   context.

## Service ownership map

| Service | Primary responsibilities |
|---|---|
| `GatewayService` | Register/update/delete gateways, async lifecycle state, refresh/catalog sync, create/update child tools/resources/prompts from gateway capabilities, gateway cache invalidation. |
| `ToolService` | Register/list/get/update/delete tools, REST integration handling, tool invocation support, A2A-derived tool creation/update/deletion, schema and mapping validation. |
| `ResourceService` | Register/list/get/update/delete resources, resource reads/templates/subscriptions, content size/type/pattern validation, resource cache invalidation. |
| `PromptService` | Register/list/get/update/delete prompts, template validation/rendering, prompt argument checks, prompt cache invalidation. |
| `ServerService` | Register/list/get/update/delete virtual servers and maintain associations to tools/resources/prompts/A2A agents. |
| `A2AAgentService` | Register/list/get/update/delete/invoke A2A agents, agent cards/tasks, and state cascade to associated tools. |
| `RootService` | Validate and manage configured roots and root export/change streams. |
| `TagService` | Aggregate tag information across entity tables and return entities by tag. |
| `CatalogService` | Load MCP registry catalog, filter catalog servers, and register catalog servers as gateways. |
| `ExportService` | Build export envelopes for tools, gateways, servers, prompts, resources, and roots, with tag/type filtering and dependency inclusion. |
| `ImportService` | Validate import envelopes, apply conflict strategy, convert imported entities into create/update schemas, track import status, and assign imported rows to user/team context. |

## Model/relationship notes

- `Gateway` rows hold gateway identity, URL, transport/auth/config fields, tags,
  lifecycle status, visibility/team/owner metadata, and relationships to child
  tools/resources/prompts.
- `Tool` rows hold original/custom names, URL, integration type, request type,
  input/output schema, auth/header/mapping fields, gateway association,
  visibility/team/owner, and metric relationships.
- `Resource` rows hold name, URI/content/template metadata, MIME/content fields,
  gateway association, tags, visibility/team/owner, and subscriptions/metrics.
- `Prompt` rows hold original/custom/display/name fields, template, arguments,
  gateway association, tags, visibility/team/owner, and metrics.
- `Server` rows hold name/config/tags and association tables/relationships to
  tools, resources, prompts, and A2A agents.
- `A2AAgent` rows hold endpoint/auth/agent metadata, tags, visibility/team/owner,
  associated tool identity, task/push/event relationships, and metrics.

## Admin UI boundary

Admin routes frequently return either JSON responses or HTML partials. The Admin
UI is HTMX/templates-backed, but entity truth remains the same services and
schemas listed above. When fixing behavior:

1. Fix service/schema logic first when the rule is shared by API and UI.
2. Fix Admin route/form parsing only when the issue is specific to Admin input
   compatibility or partial rendering.
3. Fix templates only when the data is correct but UI presentation is wrong.
