# OpenAPI and JSON Schema tool generation

Use this reference when registering REST APIs as ContextForge tools or when a
client needs `input_schema` / `output_schema` derived from an OpenAPI document.

## Route family

| Route | Use case | Notes |
|---|---|---|
| `POST /v1/tools/generate-schemas-from-openapi` | Programmatic schema generation | Mounted directly at `/v1/tools`; does not require Admin UI route availability, but does require tool-create permission. |
| `POST /v1/admin/tools/generate-schemas-from-openapi` | Admin UI/API schema generation | Admin twin with Admin CSRF dependency and Admin route feature flag. |

Do not confuse these with FastAPI's own `/openapi.json`; that endpoint returns
ContextForge's API schema. The generation routes fetch another service's
OpenAPI spec and extract schemas for a REST tool.

## Request shape

```json
{
  "url": "https://api.example.test/v1/weather/current",
  "request_type": "GET",
  "openapi_url": "https://api.example.test/openapi.json"
}
```

Fields:

| Field | Meaning |
|---|---|
| `url` | Full target tool URL. Required. The route parses this into base URL and path. |
| `request_type` | HTTP method; defaults to `GET` when omitted in the v1 schema generation route. |
| `openapi_url` | Optional direct OpenAPI spec URL. Empty or omitted means auto-discover `<base-url>/openapi.json`. |

## Success response shape

```json
{
  "message": "Schemas generated successfully from OpenAPI spec",
  "success": true,
  "input_schema": {
    "type": "object",
    "properties": {}
  },
  "output_schema": {
    "type": "object",
    "properties": {}
  },
  "spec_url": "https://api.example.test/openapi.json"
}
```

Either schema may be `null`/absent from the upstream OpenAPI operation when the
operation has no JSON request body or no recognized JSON success response.

## Extraction rules

The service:

1. Validates the target URL and OpenAPI URL using ContextForge URL security
   validation.
2. Fetches the OpenAPI spec with redirects disabled.
3. Rejects OpenAPI responses larger than the configured safety cap.
4. Requires the response body to be JSON.
5. Finds the requested path and method under `paths`.
6. Extracts input schema from `requestBody.content.application/json.schema`.
7. Extracts output schema from a `200` response, then `201` response, using
   `content.application/json.schema`.
8. Resolves only top-level local `$ref` values like
   `#/components/schemas/WeatherRequest`.

Limitations to remember:

- External `$ref` files are not resolved.
- Nested `$ref` chains inside a resolved schema are not fully expanded.
- Non-JSON content types do not produce schemas.
- Path matching is exact. `/v1/weather/current` and `/weather/current` are
  different paths.
- The HTTP method must exist on that path.

## Error mapping

| Status | Typical cause | Fix |
|---|---|---|
| `400` | URL fails security validation, malformed/unsupported URL, OpenAPI response too large, or spec JSON invalid | Use an allowed HTTP(S) URL that points to a JSON OpenAPI spec and is reachable from ContextForge. |
| `404` | Path or method not found in the OpenAPI spec | Check the exact path extracted from `url` and the `request_type`. |
| `422` | Pydantic/FastAPI request validation failure on the v1 route | Send a JSON object with required string `url`. |
| `502` | Upstream spec fetch failed or returned an HTTP error | Confirm the spec URL is reachable and returns JSON. |
| `500` | Unexpected schema processing error | Check logs and minimize the spec/path to reproduce. |

## Register a generated REST tool

1. Generate schemas:

```bash
curl -s -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://api.example.test/v1/weather/current",
    "request_type": "GET",
    "openapi_url": "https://api.example.test/openapi.json"
  }' \
  "$BASE_URL/v1/tools/generate-schemas-from-openapi" | tee schemas.json
```

2. Register the REST tool using the generated schemas:

```bash
input_schema=$(jq '.input_schema // {"type":"object"}' schemas.json)
output_schema=$(jq '.output_schema // null' schemas.json)

jq -n \
  --arg name "weather-current" \
  --arg url "https://api.example.test/v1/weather/current" \
  --argjson input_schema "$input_schema" \
  --argjson output_schema "$output_schema" \
  '{
    tool: {
      name: $name,
      description: "Get current weather",
      url: $url,
      integration_type: "REST",
      request_type: "GET",
      input_schema: $input_schema,
      output_schema: $output_schema,
      visibility: "public",
      tags: ["weather", "rest"]
    },
    team_id: null
  }' |
curl -s -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d @- \
  "$BASE_URL/v1/tools" | jq .
```

3. Bundle the tool into a virtual server:

```bash
tool_id=$(curl -s -H "Authorization: Bearer $TOKEN" \
  "$BASE_URL/v1/tools?include_pagination=false&gateway_id=null" |
  jq -r '.[] | select(.name == "weather-current") | .id' | head -1)

jq -n --arg tool_id "$tool_id" '{
  server: {
    name: "weather-server",
    description: "Virtual server exposing weather REST tools",
    associated_tools: [$tool_id]
  },
  team_id: null,
  visibility: "public"
}' |
curl -s -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d @- \
  "$BASE_URL/v1/servers" | jq .
```

## Handling `409` duplicate tool registration

A `409` from `POST /v1/tools` usually means a conflicting tool name already
exists. The existing tool may be active or inactive.

Safe resolution sequence:

1. List visible matching tools:

```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  "$BASE_URL/v1/tools?include_pagination=false&include_inactive=true&gateway_id=null" |
  jq '.[] | select(.name == "weather-current") | {id, name, enabled, url}'
```

2. If the existing tool is the intended integration, reuse its `id` in the
   server association.
3. If the existing tool needs schema or URL changes, `PUT /v1/tools/{tool_id}`
   with only the changed fields.
4. If the existing tool is unrelated, choose a unique name such as
   `weather-current-v2`.
5. Do not delete an existing tool merely to make create succeed unless the task
   explicitly authorizes deletion and you understand virtual server associations.

## Common validation failures

- `url` has no scheme/host or uses an unsupported scheme: use a full `http://` or
  `https://` URL allowed by ContextForge security validation.
- `openapi_url` points to HTML docs instead of raw JSON: use the actual JSON spec
  URL.
- Spec path missing: inspect the upstream spec paths and match exactly.
- Generated `input_schema` is `null`: the operation may use query parameters
  rather than JSON request body; decide whether to author a schema manually.
- Tool register `422`: generated schema may be valid JSON but the tool payload is
  missing fields such as `name`, `url`, `integration_type`, or `request_type`.
- Tool/server association fails: verify you are using the tool `id` expected by
  server association, not just its name, and that token visibility can see it.
