# REST API And Data Models

Use this reference when translating between Python SDK calls, CLI commands,
TypeScript client calls, and raw REST requests. The package uses shared Pydantic
models in `memmachine_common` for most Python client/server contracts.

## Endpoint Families

The self-hosted server exposes REST API v2 endpoint families under `/api/v2`.
The cloud TypeScript client defaults to a base URL ending in `/v2`; when using a
self-hosted server, set the client base URL to include the path prefix expected
by that client or route.

| Family | Representative endpoints | Purpose |
| --- | --- | --- |
| Health/metrics | `GET /api/v2/health`, `GET /api/v2/metrics` | Readiness and Prometheus metrics. |
| Projects | `POST /api/v2/projects`, `/projects/get`, `/projects/list`, `/projects/delete`, `/projects/episode_count/get` | Project lifecycle and counts. |
| Memories | `POST /api/v2/memories`, `/memories/search`, `/memories/list`, `/memories/episodic/delete`, `/memories/semantic/delete` | Add, search, list, and delete episodic/semantic memory. |
| Semantic memory | `/memories/semantic/feature`, `/set_type`, `/set_id`, `/category`, `/category/template`, `/category/tag` | Profile/semantic set, category, feature, and tag management. |
| Memory config | `/memory/episodic/config`, `/memory/episodic/long_term/config`, `/memory/episodic/short_term/config` | Per-project memory configuration APIs. |
| Runtime config | `/config`, `/config/resources`, `/config/memory`, `/config/resources/embedders`, `/config/resources/language_models`, `/config/resources/rerankers/{name}/retry` | Server-level resource and memory configuration APIs when enabled. |
| MCP | stdio or HTTP server entry points | Tool-style add/search/delete memory for MCP-compatible clients. |

## Core Model Concepts

| Concept | Key fields | Notes |
| --- | --- | --- |
| Project context | `org_id`, `project_id` | Required by most project/memory operations. Defaults such as `universal` may exist in raw models but explicit values are safer. |
| Memory context metadata | `user_id`, `agent_id`, `group_id`, `session_id`, plus custom metadata | Python `Project.memory(metadata=...)` stores default metadata for later memory calls. |
| Memory type | `episodic`, `semantic` | Add/search can target one or both, depending on SDK/API surface. |
| Episode type | `message` | Current public enum value for conversation-like episodes. |
| Project config | `backend`, `embedder`, `reranker`, `vector_graph_store`, `vector_store`, `segment_store`, `properties_schema` | `backend` is `declarative` or `event`; event backend needs vector + segment stores. |
| Search request | `query`, `top_k`/`limit`, `filter`, `set_metadata`, `expand_context`, `score_threshold`, `types`, `agent_mode` | SDKs may use slightly different option names; translate carefully. |
| List request | `page_size`, `page_num`, `filter`, `set_metadata`, `type` | Use pagination for large memory sets. |

## Python SDK To REST Payload Shape

Python SDK:

```python
result = memory.search(
    "aisle seat preference",
    limit=5,
    filter="metadata.category = 'travel'",
    set_metadata={"user_id": "alice"},
    agent_mode=False,
)
```

REST-style fields:

```json
{
  "org_id": "my-org",
  "project_id": "my-project",
  "query": "aisle seat preference",
  "top_k": 5,
  "filter": "metadata.category = 'travel'",
  "set_metadata": {"user_id": "alice"},
  "expand_context": 0,
  "agent_mode": false,
  "types": ["episodic", "semantic"]
}
```

CLI equivalent shape:

```bash
mem-cli memory search "aisle seat preference" \
  --org-id "my-org" --project-id "my-project" \
  --filter "metadata.category = 'travel'" \
  --set-metadata '{"user_id":"alice"}' --limit 5
```

## Filter Guidance

The modern filter string parser supports comparisons, parentheses, `AND`, `OR`,
`IN`, `IS NULL`, and date expressions. Use a single equals sign:

```text
metadata.category = 'travel'
status = OPEN AND (owner = alice OR priority = HIGH)
created_at < date('2026-01-19T01:56:41.513342Z')
```

For legacy dictionary filters, user metadata fields can be prefixed with
`m.`/`metadata.` when needed. Prefer explicit filter strings for complex logic.
If a user writes `==`, rewrite it to `=` before calling the filter parser.

## Error Handling Expectations

- SDK methods raise request/client exceptions for transport failures and server
  errors; handle connection refused, timeout, 401/403, 404, 422, and 5xx
  separately.
- API validation errors usually indicate missing project context, invalid
  filter syntax, unsupported memory type, bad resource ID, or mismatched backend
  fields.
- API key or provider credentials must be loaded from a secure location and
  masked in logs.
- A successful client import does not prove the server is reachable; run a
  health check against the intended base URL before live memory operations.
