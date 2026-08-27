# Memory API Reference

## Successful envelope

Most successful business responses use:

```json
{"request_id":"<32-hex>","data":{}}
```

Error responses use the same top-level `request_id` plus an `error` object with `code`, `message`, `timestamp`, and `path`.

## `POST /api/v2/memory/add`

Request fields:

| Field | Required | Notes |
|---|---|---|
| `session_id` | yes | 1-128 chars; groups buffered messages. |
| `app_id` | no | Default `default`; path-safe. |
| `project_id` | no | Default `default`; path-safe. |
| `messages` | yes | 1-500 message items. |

Message item essentials:

| Field | Notes |
|---|---|
| `sender_id` | Stable sender; for user messages this becomes the search `user_id`. |
| `sender_name` | Optional display name used by extraction. |
| `role` | `user`, `assistant`, or `tool`. |
| `timestamp` | Positive Unix epoch milliseconds. |
| `content` | Either a string or a list of content items. |
| `tool_calls`, `tool_call_id` | OpenAI-style tool-call metadata for agent traces. |

Response `data.status` is `accumulated` or `extracted`; `message_count` is the number of submitted messages.

## `POST /api/v2/memory/flush`

Request requires `session_id`; `app_id` and `project_id` default to `default`. Flush forces boundary detection over the current session tail. Response `data.status` is `extracted` or `no_extraction`.

## `POST /api/v2/memory/search`

Important request fields:

| Field | Notes |
|---|---|
| `user_id` / `agent_id` | Exactly one is required. |
| `query` | Required non-empty string. |
| `method` | `keyword`, `vector`, `hybrid`, or `agentic`; default `hybrid`. |
| `top_k` | `-1` for unlimited or 1..100. |
| `radius` | Optional cosine threshold for vector paths. |
| `min_score` | Optional calibrated score floor for episode hybrid path. |
| `include_profile` | Adds profile for user owners when available. |
| `enable_llm_rerank` | Applies to agent case/skill hybrid fusion only. |
| `filters` | Recursive filter DSL. |

Response `data` always has arrays: `episodes`, `profiles`, `agent_cases`, `agent_skills`, and `unprocessed_messages`. Routes not applicable to the owner type stay empty.

## `POST /api/v2/memory/get`

Use for paginated listing rather than ranked search.

| Request field | Notes |
|---|---|
| `user_id` / `agent_id` | Exactly one required. |
| `memory_type` | `episode` or `profile` for `user_id`; `agent_case` or `agent_skill` for `agent_id`. |
| `page`, `page_size` | `page>=1`, `1<=page_size<=100`. |
| `sort_by` | `timestamp` or `updated_at`; profile/agent_skill may use `updated_at`. |
| `filters` | Same DSL as search. |

## Content items for multimodal input

A message `content` list contains objects with `type` in `text`, `image`, `audio`, `doc`, `pdf`, `html`, or `email`. Exactly one of `text`, `uri`, or `base64` should carry the payload. Non-text items require parser/multimodal capability and may return `415` or capability errors if unsupported.

Use `uri` for large assets. Use `base64` only for small assets and provide `ext` when MIME inference may be ambiguous.

## Filter DSL

Filters allow scalar field predicates and recursive `AND`/`OR` arrays. Keep filters tied to fields present for the selected memory type and owner. Invalid filters map to an `INVALID_INPUT` error with a human-readable compile reason.
