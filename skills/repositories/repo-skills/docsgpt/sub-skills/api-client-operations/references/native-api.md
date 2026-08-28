# Native Agent API

## Authentication and resolution

- Agent-key flow: include `api_key` in JSON/form payload.
- JWT flow: `Authorization: Bearer <token>` and optionally `agent_id`.
- An agent key loads its prompt, sources, tools and default model.

Resolution precedence is API key, authorized agent id, then request-level fields.

## Non-streaming answer

```bash
curl -X POST "$DOCSGPT_URL/api/answer" \
  -H "Content-Type: application/json" \
  -d '{"question":"Summarize the policy","api_key":"..."}'
```

Response can include `conversation_id`, `answer`, `sources`, `tool_calls`, `thought`, and structured-output metadata.

Common fields: `question`, `api_key`, `conversation_id`, JSON-encoded `history` for new conversations, `model_id`, `visibility`, `passthrough`, `prompt_id`, `active_docs`, `retriever`, `chunks`, `isNoneDoc`, and `agent_id`.

`save_conversation` is deprecated/no-op. Conversations persist; `visibility="listed"` controls sidebar listing while omitted/other values remain hidden.

## Native stream

```bash
curl -N -X POST "$DOCSGPT_URL/stream" \
  -H "Accept: text/event-stream" \
  -H "Content-Type: application/json" \
  -d '{"question":"Summarize the policy","api_key":"..."}'
```

Each `data:` JSON frame has a `type`, including `answer`, `source`, `tool_calls`, `thought`, `structured_answer`, `id`, `error`, or `end`. Treat frame order as a stream; do not assume one TCP chunk equals one event.

Streaming-only fields include attachment ids and an optional `index` for updating an existing query; index update also requires `conversation_id`.

## Attachment flow

1. `POST /api/store_attachment` as multipart with one or more `file` fields and matching auth/API key.
2. Capture `task_id`.
3. Poll `GET /api/task_status?task_id=...` until `SUCCESS` or `FAILURE`.
4. Read `result.attachment_id` only after success.
5. Send ids in `/stream` as `attachments`.

Attachments are user-scoped. Upload and stream must resolve to the same owner. Unsupported native file MIME can fall back to extracted text; PDF may be converted to images for suitable providers.

## Error handling

- Validate HTTP status before parsing expected JSON.
- Treat task `PENDING` as non-terminal and set a bounded poll deadline.
- Surface server `error` frames and do not report success until `end`/terminal state.
- Preserve conversation/message ids for recovery, but do not log keys or attachment contents.
