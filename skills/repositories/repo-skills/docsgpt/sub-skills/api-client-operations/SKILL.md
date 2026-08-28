---
name: api-client-operations
description: "Guides DocsGPT native answer and attachment APIs, SSE and reconnect behavior, OpenAI-compatible clients, structured output, multimodal input, idempotency, and MCP routing."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# API and Client Operations

Use this sub-skill to call DocsGPT from a client, choose native versus OpenAI-compatible endpoints, parse streams, recover connections, upload attachments, or validate ASGI/MCP exposure.

## Choose the surface

- **Native non-streaming/streaming/attachments**: read [native API](references/native-api.md).
- **OpenAI SDK or compatible client**: read [OpenAI-compatible API](references/openai-compatible-api.md).
- **SSE notifications, chat reconnect, proxy behavior, `/mcp`**: read [streaming, events, and MCP](references/streaming-events-and-mcp.md).
- **401/403/404/409/429, duplicate runs, malformed stream, stalled attachment**: read [troubleshooting](references/troubleshooting.md).

## Endpoint selection

| Need | Surface |
|---|---|
| simple blocking answer with DocsGPT fields | `POST /api/answer` |
| native answer deltas, sources, thoughts, tool results, attachments | `POST /stream` |
| OpenAI SDK/client compatibility | `POST /v1/chat/completions` |
| agent listing for an API key | `GET /v1/models` |
| upload turn-specific file | `POST /api/store_attachment`, then poll `/api/task_status` |
| per-user realtime notifications | `GET /api/events` |
| resume interrupted native answer | `GET /api/messages/<message_id>/events` |
| MCP server | `/mcp` on the full ASGI app |

Native endpoints support DocsGPT-specific prompt passthrough, explicit conversation reuse, attachment ids, and visibility. `/v1` is best when a client already speaks Chat Completions.

## Native request resolution

1. `api_key` loads the bound agent configuration.
2. Otherwise `agent_id` can resolve an authorized agent.
3. Otherwise request-level prompt/source/retriever fields apply.

Do not assume request fields override an API-key-owned agent. Use the same owner context for attachment upload and answer.

## Safe smoke checks

Read-only deployment checks:

```bash
python scripts/api_smoke.py --base-url http://localhost:7091
```

Authenticated model listing:

```bash
DOCSGPT_API_KEY=... python scripts/api_smoke.py \
  --base-url http://localhost:7091 \
  --token-env DOCSGPT_API_KEY \
  --require-models
```

`--question` performs a real non-streaming agent run and persists a hidden conversation; use it only against a test agent/deployment.

## Deterministic provider mock

To test DocsGPT outbound OpenAI-compatible provider wiring without a cloud call, run:

```bash
python scripts/mock_openai_server.py --port 8090
```

Point a disposable DocsGPT model/provider configuration at `http://127.0.0.1:8090/v1`. The mock handles model listing and streaming/non-streaming chat completions with deterministic content. It is not a security or load-test server.

## Reliability rules

- Buffer SSE by lines/frames; network chunks do not align to event boundaries.
- Persist the last delivered event id/sequence only after processing the event.
- Back off on `429`; reset state on `backlog.truncated` and refetch current resources.
- Use `Idempotency-Key` only where supported: `/v1` non-streaming and agent webhooks have specific replay semantics.
- A timeout after a state-changing tool call is ambiguous; check tool/run state before retry.
- Conversations are persisted server-side; visibility controls listing, not persistence.

## Cross-skill routes

- Create/configure agent and API key: [agents-workflows](../agents-workflows/SKILL.md)
- Deploy ASGI/proxy/Redis: [deploy-configure](../deploy-configure/SKILL.md)
- Tool/MCP server configuration: [tools-integrations](../tools-integrations/SKILL.md)
