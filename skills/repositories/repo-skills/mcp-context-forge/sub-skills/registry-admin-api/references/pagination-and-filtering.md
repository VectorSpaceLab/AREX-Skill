# Pagination and filtering

Use this reference when a client receives a shape it did not expect, when a list
endpoint returns too few/many entities, or when main API cursor pagination is
confused with Admin page pagination.

## The key distinction

| Family | Example path | Request parameters | Response shape |
|---|---|---|---|
| Main registry API | `/v1/tools`, `/v1/servers`, `/v1/gateways`, `/v1/resources`, `/v1/prompts`, `/v1/a2a` | `include_pagination`, `cursor`, `limit`, filters | Plain array by default; cursor object only when `include_pagination=true`. |
| Admin API/UI lists | `/v1/admin/tools`, `/v1/admin/servers`, `/v1/admin/gateways` | `page`, `per_page`, filters | Always page object with `data`, `pagination`, and `links`. |
| Catalog API | `/v1/catalog` | `limit`, `offset`, catalog filters | Catalog-specific response with server list and metadata. |
| Tags API | `/v1/tags`, `/v1/tags/{tag}/entities` | `entity_types`, `include_entities` | Tag info or tagged entity arrays. |

Main endpoints use keyset/cursor pagination because they are registry APIs.
Admin endpoints use page/offset pagination because the UI needs numbered pages.

## Main endpoint default: plain arrays

Core list routes declare `include_pagination=false` by default. A plain request
therefore returns a JSON array:

```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  "$BASE_URL/v1/tools" | jq type
# "array"
```

Add `include_pagination=true` to get cursor metadata:

```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  "$BASE_URL/v1/tools?include_pagination=true&limit=50" | jq .
```

Tool response shape:

```json
{
  "tools": [
    {"id": "tool-id", "name": "weather-current"}
  ],
  "nextCursor": "opaque-cursor-or-null"
}
```

The top-level entity key changes by route:

| Route | Cursor response entity key |
|---|---|
| `/v1/tools` | `tools` |
| `/v1/servers` | `servers` |
| `/v1/gateways` | `gateways` |
| `/v1/resources` | `resources` |
| `/v1/prompts` | `prompts` |
| `/v1/a2a` | `agents` |

`nextCursor` is camelCase in the HTTP JSON shape. The Pydantic field name is
`next_cursor`; do not use internal Python names in raw client JSON parsing.

## Main cursor parameters

| Parameter | Meaning |
|---|---|
| `include_pagination=true` | Return `{entityKey: [...], nextCursor: ...}` instead of a plain array. |
| `cursor=<opaque>` | Fetch the page after a cursor from the previous response. |
| `limit=<n>` | Maximum items in one response; `0` means all results/no page limit. |
| `include_inactive=true` | Include disabled entities where supported. |
| `tags=a,b` | Return entities matching any listed tag where supported. |
| `visibility=public|team|private` | Filter by visibility where supported. |
| `team_id=<id>` | Narrow to a team where supported. |
| `gateway_id=<id>` | For tools/resources/prompts: filter by gateway. Use literal `null` for entities without a gateway. |

Main routes apply token/user/team visibility filtering before returning data, so
an empty page can mean either no data or no visible data for the token.

## Main cursor loop pattern

```bash
cursor=""
while :; do
  if [ -n "$cursor" ]; then
    qs="include_pagination=true&cursor=$cursor"
  else
    qs="include_pagination=true"
  fi
  body=$(curl -s -H "Authorization: Bearer $TOKEN" "$BASE_URL/v1/tools?$qs")
  echo "$body" | jq '.tools[]? | {id, name}'
  cursor=$(echo "$body" | jq -r '.nextCursor // empty')
  [ -z "$cursor" ] && break
done
```

For programmatic clients, preserve the cursor exactly as returned. It is opaque;
do not decode or synthesize it.

## Admin page response shape

Admin list routes return page objects, for example:

```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  "$BASE_URL/v1/admin/tools?page=1&per_page=10" | jq .
```

Expected shape:

```json
{
  "data": [
    {"id": "tool-id", "name": "weather-current"}
  ],
  "pagination": {
    "total_items": 25,
    "page": 1,
    "per_page": 10,
    "total_pages": 3,
    "has_next": true,
    "has_prev": false
  },
  "links": {
    "self": "/admin/tools?page=1&per_page=10",
    "first": "/admin/tools?page=1&per_page=10",
    "last": "/admin/tools?page=3&per_page=10",
    "next": "/admin/tools?page=2&per_page=10",
    "prev": null
  }
}
```

Admin validation rules:

- `page` is 1-indexed and must be `>= 1`.
- `per_page` must be `>= 1` and within the configured max page size.
- Defaults are configuration-driven; typical defaults are 50 items per page and
  max page size 500.
- Oversized `per_page` or `page=0` returns FastAPI validation errors (`422`).

## Admin list families

| Admin route | Notes |
|---|---|
| `/v1/admin/tools` | Page list of tools; `include_inactive` supported. |
| `/v1/admin/servers` | Page list of virtual servers. |
| `/v1/admin/resources` | Page list of resources. |
| `/v1/admin/prompts` | Page list of prompts. |
| `/v1/admin/gateways` | Page list of gateways. |
| `/v1/admin/a2a` | Page list of A2A agents when A2A is enabled. |
| `/v1/admin/tags` | Admin tag list; use main `/v1/tags` for simple tag API reads. |
| `/v1/admin/grpc` | gRPC services Admin list; detailed gRPC behavior is outside this sub-skill. |

With legacy route shims enabled, `/admin/tools` and similar aliases are also
available.

## Filtering gotchas

### `gateway_id=null`

For tools/resources/prompts, `gateway_id=null` is a literal filter value meaning
"entities not associated with a gateway". This is useful for REST tools and A2A
agent tools that are not child rows of an upstream MCP gateway.

```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  "$BASE_URL/v1/tools?gateway_id=null&include_pagination=false"
```

### Visibility and team filters

Visibility/team filters are not a substitute for authorization. Services first
apply access rules derived from the request and then apply explicit filters.
An admin token can still be narrowed by an explicit `team_id` query.

### Inactive rows

Default list behavior hides disabled entities. Use `include_inactive=true` when
triaging a conflict that mentions an inactive existing entity.

### Tags

Tag filtering matches any requested tag. If a task needs exact all-tags matching,
confirm service behavior before changing it because current list filters are
optimized for "match any" registry discovery.

## Troubleshooting pagination mismatch

Symptom: client expects `.nextCursor` but receives an array.

- Cause: it called a main endpoint without `include_pagination=true`.
- Fix: add `include_pagination=true` or parse the array shape.

Symptom: client expects `.nextCursor` but receives `{data, pagination, links}`.

- Cause: it called an Admin endpoint.
- Fix: use `pagination.has_next`/`links.next`, or switch to the main endpoint.

Symptom: client expects a plain array but receives an object with `tools` and
`nextCursor`.

- Cause: `include_pagination=true` is present.
- Fix: either remove the parameter or update parsing to read the entity key.

Symptom: page request returns `422`.

- Cause: invalid `page` or `per_page` value.
- Fix: use `page>=1` and a `per_page` within configured bounds.

Symptom: a list returns fewer rows than the database contains.

- Causes: token scoping, RBAC/visibility filters, `include_inactive=false`,
  tags, `gateway_id`, `team_id`, or `visibility` query parameters.
- Fix: remove optional filters, check token visibility, and list inactive rows
  while debugging.
