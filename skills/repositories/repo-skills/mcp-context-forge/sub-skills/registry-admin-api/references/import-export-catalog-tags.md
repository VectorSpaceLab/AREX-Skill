# Import/export, catalog, and tags

Use this reference for configuration portability, MCP registry catalog work, and
cross-entity tag discovery. These workflows are registry/Admin API work; route
plugin policy or observability details elsewhere.

## Export/import entity coverage

Configuration export/import covers these entity types:

- `tools`
- `gateways`
- `servers`
- `prompts`
- `resources`
- `roots`

A2A agent CRUD is part of this sub-skill's registry API coverage, but the
standard configuration import/export service does not treat A2A agents as a
supported import entity type in the same envelope. Do not promise A2A import
unless the repository has been updated and verified.

## Export routes

Canonical API routes:

| Route | Purpose |
|---|---|
| `GET /v1/export` | Export configuration, optionally filtered by entity types, excluded types, tags, active state, and dependency inclusion. |
| `POST /v1/export/selective` | Export selected entities by type/name/id with optional dependencies. |

Admin/UI wrappers:

| Route | Purpose |
|---|---|
| `GET /v1/admin/export/configuration` | Download a JSON export file from Admin UI/API. |
| `POST /v1/admin/export/selective` | Selective export from Admin UI/API. |

Common query parameters for full export:

| Parameter | Meaning |
|---|---|
| `types=tools,gateways` | Include only these supported entity types. |
| `exclude_types=roots` | Exclude supported entity types. |
| `tags=prod,weather` | Export entities matching tags. |
| `include_inactive=true` | Include disabled entities. |
| `include_dependencies=true` | Include dependent entities such as tools referenced by servers. |

Export envelope shape:

```json
{
  "version": "2025-03-26",
  "exported_at": "2026-01-01T00:00:00Z",
  "exported_by": "admin@example.com",
  "source_gateway": "http://host:port",
  "encryption_method": "AES-256-GCM",
  "entities": {
    "gateways": [],
    "tools": [],
    "resources": [],
    "prompts": [],
    "servers": [],
    "roots": []
  },
  "metadata": {
    "entity_counts": {},
    "dependencies": {},
    "export_options": {}
  }
}
```

## Import routes

Canonical API routes:

| Route | Purpose |
|---|---|
| `POST /v1/import` | Validate and apply an import envelope. |
| `GET /v1/import/status/{import_id}` | Fetch status for one import. |
| `GET /v1/import/status` | List import status records. |
| `POST /v1/import/cleanup` | Clean old completed import status records. |

Admin/UI wrappers:

| Route | Purpose |
|---|---|
| `POST /v1/admin/import/preview` | Preview import file and conflicts without applying it. |
| `POST /v1/admin/import/configuration` | Apply import via Admin API/UI. |
| `GET /v1/admin/import/status/{import_id}` | Admin import status. |
| `GET /v1/admin/import/status` | Admin import status list. |

Main import request shape:

```json
{
  "import_data": {
    "version": "2025-03-26",
    "exported_at": "2026-01-01T00:00:00Z",
    "entities": {"tools": []}
  },
  "conflict_strategy": "update",
  "dry_run": false,
  "rekey_secret": null,
  "selected_entities": null
}
```

Import status response shape:

```json
{
  "import_id": "uuid",
  "status": "completed",
  "total_entities": 3,
  "processed_entities": 3,
  "created_entities": 2,
  "updated_entities": 1,
  "skipped_entities": 0,
  "failed_entities": 0,
  "errors": [],
  "warnings": []
}
```

## Conflict strategies

| Strategy | Behavior |
|---|---|
| `skip` | Leave existing entity unchanged and count it as skipped. |
| `update` | Update existing entity using import data. This is the default. |
| `rename` | Create an imported entity with a generated/new non-conflicting name where supported. |
| `fail` | Treat the conflict as an import failure. |

Entity identifiers used for conflicts:

| Entity type | Identifier |
|---|---|
| `tools` | `name` |
| `gateways` | `name` |
| `servers` | `name` |
| `prompts` | `name` |
| `resources` | `uri` |
| `roots` | `uri` |

For duplicate REST API registration tasks, do not blindly retry `POST /v1/tools`.
First decide whether the existing tool should be reused, updated, renamed, or
left alone; that mirrors import conflict choices.

## Import validation rules

The import envelope must include top-level `version`, `exported_at`, and
`entities`. Supported entity lists must be arrays. Required entity fields:

| Entity type | Required fields |
|---|---|
| `tools` | `name`, `url`, `integration_type` |
| `gateways` | `name`, `url` |
| `servers` | `name` |
| `prompts` | `name`, `template` |
| `resources` | `name`, `uri` |
| `roots` | `uri`, `name` |

Processing order is roots, gateways, tools, resources, prompts, then servers so
that associations can resolve. After import, service logic assigns imported
items to the importing user/team context when applicable.

Use `dry_run=true` for previews in automation when available. Use Admin
`/import/preview` when building UI workflows because it returns categorized
preview details.

## Catalog API

Catalog routes expose MCP registry server discovery and registration. They are
not the same as gateway list routes, but successful registration creates a
gateway through the gateway service.

Programmatic v1 catalog:

| Route | Purpose |
|---|---|
| `GET /v1/catalog` | List catalog servers. |
| `POST /v1/catalog/{catalog_id}/register` | Register a catalog server as a gateway. |

Catalog list filters:

| Parameter | Meaning |
|---|---|
| `category` | Filter by catalog category. |
| `auth_type` | Filter by auth type. |
| `provider` | Filter by provider. |
| `search` | Search name/description. |
| `tags` | One or more tag filters. |
| `show_registered_only=true` | Show only catalog servers already registered and visible to caller. |
| `show_available_only=true` | Show only available servers; default is true. |
| `limit` / `offset` | Offset pagination for catalog listing. |

Catalog registration body:

```json
{
  "name": "optional-custom-name",
  "api_key": "optional-api-key-or-secret-ref"
}
```

Catalog registration outcomes:

- Unknown catalog ID: `404`.
- Already registered visible server: `409`.
- Other business failures such as unreachable server may return a success=false
  envelope, depending on route family.
- Requires both server creation and gateway creation capability.

Admin catalog twins:

| Route | Purpose |
|---|---|
| `GET /v1/admin/mcp-registry/servers` | Admin catalog list. |
| `POST /v1/admin/mcp-registry/{server_id}/register` | Admin catalog registration. |
| `GET /v1/admin/mcp-registry/{server_id}/status` | Availability/status check. |
| `POST /v1/admin/mcp-registry/bulk-register` | Bulk catalog registration. |
| `GET /v1/admin/mcp-registry/partial` | HTMX partial for UI. |

If `MCPGATEWAY_CATALOG_ENABLED=false`, catalog handlers report disabled/not
found behavior. Verify the flag before debugging catalog data.

## Tags API

Main tag routes:

| Route | Purpose |
|---|---|
| `GET /v1/tags` | List tags with counts/stats and optionally included entities. |
| `GET /v1/tags/{tag_name}/entities` | List entities carrying a tag. |

Common parameters:

| Parameter | Meaning |
|---|---|
| `entity_types=gateways,servers,tools,resources,prompts` | Restrict tag aggregation to entity families. |
| `include_entities=true` | Include tagged entity details in tag list responses. |

Tag entity shape includes an entity type, ID/name, and basic display metadata.
Use tag APIs to discover what is tagged; use the entity API to mutate the tag
list on a specific tool/resource/prompt/server/gateway.

## Troubleshooting import/export/catalog/tag issues

- `400` or validation error on import: check the envelope has `version`,
  `exported_at`, `entities`, and required fields per entity type.
- `409` on import or create: identify the entity conflict key (`name`, `uri`) and
  choose skip/update/rename/fail semantics intentionally.
- Imported server missing associations: confirm the referenced tools/resources/
  prompts were included or `include_dependencies=true` was used during export.
- Root import/export denied: roots are admin/system-config scope and may require
  stronger permission than normal entity export.
- Catalog returns no servers: check `MCPGATEWAY_CATALOG_ENABLED`, filters,
  `show_available_only`, and token visibility for already registered gateways.
- Tag not found: confirm whether the tag is stored on the entity family being
  queried and whether token/team visibility filters hide tagged entities.
