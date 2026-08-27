# Authentication and Error Handling

RAGFlow public APIs generally return standard HTTP statuses plus JSON payloads with a RAGFlow `code`, `message`, and optional `data`. Client code should inspect both the HTTP status and the JSON body because application-level failures can appear in a successful HTTP response.

## Authentication

Use an API key in a Bearer header for protected endpoints:

```http
Authorization: Bearer <RAGFLOW_API_KEY>
```

Guidelines:

- Keep keys in environment variables or secret stores, never in committed examples or logs.
- Redact keys when printing prepared curl commands; show only a fixed prefix/suffix if absolutely necessary.
- Do not add auth headers to `/api/v1/system/healthz`; it is documented as not requiring authorization.
- For the Python SDK, pass `RAGFlow(api_key="...", base_url="http://server:port")`; the SDK constructs the Bearer header internally.
- For OpenAI-compatible clients, pass the same RAGFlow API key as the OpenAI client `api_key`.

## HTTP status codes

| Status | Meaning | Typical client action |
| --- | --- | --- |
| `400 Bad Request` | Invalid request parameters or malformed payload | Validate JSON shape, required fields, enum values, and content type. |
| `401 Unauthorized` | Missing, malformed, expired, or wrong API key | Verify `Authorization: Bearer ...`, key source, tenant, and that no whitespace/newline was copied. |
| `403 Forbidden` | Authenticated but not allowed | Check resource ownership, team permissions, tenant context, and API key scope. |
| `404 Not Found` | Endpoint or resource not found | Check `/api/v1` prefix, resource IDs, server version, and deprecated endpoint migrations. |
| `500 Internal Server Error` | Server or dependency failure | Check `/api/v1/system/healthz`, server logs, database/Redis/document engine/storage health, and retry only after the dependency issue is addressed. |

## RAGFlow response codes

| Code | Meaning | Notes |
| --- | --- | --- |
| `0` | Success | `data` may be an object, list, boolean, stream event data, or omitted. |
| `100` | Resource-level failure in some endpoints | Example: chunk not found. Treat as a missing or invalid resource ID. |
| `101` | Validation failure | Example: missing required dataset name or upload file part. Surface field details to the user. |
| `102` | Common request/resource/auth semantic failure | Examples: resource does not exist, no authorization, required field missing, invalid conversation state. Message text is important. |
| `108` | Permission failure for selected datasets | Usually indicates the user lacks access to one or more dataset IDs. |
| `1001` | Invalid Chunk ID | Confirm chunk ID belongs to the requested document and dataset. |
| `1002` | Chunk update failed | Retry only after checking chunk existence, update payload, index state, and server health. |

## Robust client handling

Raw HTTP clients should follow this pattern:

1. Send the correct method, URL, headers, and JSON/form body.
2. If the HTTP status is not 2xx, capture status, response body, and request ID headers if available.
3. If the body is JSON and has `code`, require `code == 0` before treating the call as success.
4. Preserve `message` in raised exceptions; RAGFlow uses it for precise failures such as missing `document_ids` or wrong ownership.
5. When downloading files, handle non-JSON successful bodies and JSON error bodies separately.

Example Python helper:

```python
import requests

class RAGFlowAPIError(RuntimeError):
    pass

def require_ragflow_success(response: requests.Response):
    try:
        payload = response.json()
    except ValueError:
        response.raise_for_status()
        return response.content

    if response.status_code >= 400 or payload.get("code", 0) != 0:
        message = payload.get("message") or response.text
        raise RAGFlowAPIError(f"RAGFlow API failed: http={response.status_code} code={payload.get('code')} message={message}")
    return payload.get("data", payload)
```

## Content types

- JSON endpoints require `Content-Type: application/json` and a JSON body.
- Dataset document upload and file upload use multipart form data; let the HTTP library set the multipart boundary.
- Some `GET` endpoints accept query strings with JSON-encoded filters such as `metadata_condition`; URL-encode those values.
- `DELETE` endpoints for bulk deletion often require JSON bodies. Ensure the HTTP client actually sends a body with `DELETE` requests.

## Common protected request shapes

Dataset delete:

```json
{"ids": ["dataset-id-1"], "delete_all": false}
```

Document delete:

```json
{"ids": ["document-id-1"], "delete_all": false}
```

Chunk delete:

```json
{"chunk_ids": ["chunk-id-1"], "delete_all": false}
```

Stop parsing documents:

```json
{"document_ids": ["document-id-1"]}
```

Retrieval with metadata filter:

```json
{
  "question": "What does the contract say about renewal?",
  "dataset_ids": ["dataset-id-1"],
  "metadata_condition": {
    "logic": "and",
    "conditions": [
      {"name": "author", "comparison_operator": "is", "value": "alice"}
    ]
  }
}
```

## Streaming error handling

For streaming APIs:

- Parse `data:` lines; ignore blank keepalive lines.
- Treat `data:[DONE]` as terminal for OpenAI-compatible and native agent streams.
- Treat `data: {"code": 0, "data": true}` as terminal for native chat streams.
- If a streamed JSON payload contains `code` and it is nonzero, stop reading and raise the `message`.
- References may arrive only in the final chunk/event; do not conclude there are no citations until the terminal event has been processed.
- Preserve partial output separately from final success/failure status so callers can decide whether to display partial answers.

## Safe logging

Log these fields:

- HTTP method.
- URL origin and path, with query values redacted when they contain secrets.
- RAGFlow `code` and `message`.
- Resource type and ID labels, not whole request bodies for upload or secret-bearing calls.
- Stream terminal condition and whether references were present.

Do not log:

- API keys or full `Authorization` headers.
- Uploaded document contents by default.
- Full memory/message contents in shared logs unless the user explicitly requests it.
- Local machine paths, private environment paths, or deployment secrets.
