---
name: chat-api
description: "Use for DocsGPT chat and agent-facing HTTP APIs, streaming and SSE
  reconnects, OpenAI compatibility, conversations, and attachments."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Chat and API skill

Use this subskill for request/response flows, streaming, SSE reconnects, OpenAI-compatible integrations, conversation persistence, attachment handling, or any work centered on agent-facing HTTP endpoints.

## Primary surfaces

- `POST /api/answer` — non-streaming answer JSON.
- `POST /stream` — SSE chat stream.
- `POST /api/search` — fast retrieval search.
- `POST /api/store_attachment` and `GET /api/task_status` — upload + async attachment workflow.
- `POST /v1/chat/completions` and `GET /v1/models` — OpenAI-compatible API.
- `GET /api/events` and `GET /api/messages/<id>/events` — notification and reconnect streams.
- `GET /api/user/me` — current user identity/roles.

## When to choose this subskill

- The user asks how to call DocsGPT from an app or script.
- The task concerns streaming regressions, SSE reconnect behavior, conversation persistence, tool-call continuations, or response shape changes.
- You need to compare native DocsGPT endpoints with OpenAI-compatible clients.

## What to know first

- `/api/answer` returns a single JSON document with `conversation_id`, `answer`, `sources`, `tool_calls`, and `thought`.
- `/stream` is the preferred path for token-by-token rendering and file/image attachments.
- `/v1/chat/completions` follows the standard OpenAI chat-completions protocol and accepts `Authorization: Bearer <agent_api_key>`.
- Conversations are always persisted. `visibility="listed"` only controls sidebar listing.
- The legacy `save_conversation` request flag is deprecated and ignored.

## Common request fields

- `question`
- `api_key`
- `conversation_id`
- `history`
- `prompt_id`
- `chunks`
- `retriever`
- `agent_id`
- `visibility`
- `passthrough`
- `isNoneDoc`
- `model_id`
- `attachments` on streaming flows

## OpenAI-compatible notes

- Base URL is `/v1`, not `/api/v1`.
- Supported docs fields are exposed via a `docsgpt` object in requests/responses.
- DocsGPT-specific frames may appear on streaming responses; strict OpenAI clients should ignore them when they do not understand the extra key.
- If you need native docs-only controls such as `visibility` or prompt passthrough variables, use `/api/answer` or `/stream` instead.

## Safe checks and troubleshooting

Use these before editing transport code:

```bash
python skills/disco/docs-gpt/scripts/inspect_api_routes.py --repo . --contains /api/answer
python skills/disco/docs-gpt/scripts/inspect_api_routes.py --repo . --contains /v1/chat/completions
python -m pytest tests/api/test_async_sse_routes.py tests/test_asgi.py
```

If SSE reconnects fail, verify under `uvicorn application.asgi:asgi_app ...`, not `flask run`.

If attachment uploads fail, trace the `/api/store_attachment` → Celery task status → `/stream` path and check Redis/Postgres reachability first.

## Useful references

- `../references/repo-map.md`
- `../references/dev-environment.md`
- `docs/content/Agents/api.mdx`
- `docs/content/Agents/openai-compatible.mdx`
- `docs/runbooks/sse-notifications.md`
