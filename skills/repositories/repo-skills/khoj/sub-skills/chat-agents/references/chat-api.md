# Chat API, Streaming, and Conversation State

## Route Prefix

Khoj mounts the chat router at `/api/chat`. All endpoints below require an authenticated request unless explicitly marked as public.

## Main Chat Payload

`POST /api/chat` accepts a `ChatRequestBody` JSON body:

| Field | Type | Default | Meaning |
| --- | --- | --- | --- |
| `q` | string, required | none | User query. May start with one slash command. URL-decoded before processing. |
| `n` | integer or null | `7` | Number of note references requested when the notes path runs. |
| `d` | float or null | `null` | Optional search distance threshold passed to note search. |
| `stream` | boolean | `false` | When true, REST returns a `text/plain` stream separated by the Khoj end-event sentinel. |
| `title` | string or null | `null` | Optional title for a newly created or selected conversation. |
| `conversation_id` | string or null | `null` | Existing conversation/session id. If missing, the adapter resolves or creates the current conversation. |
| `turn_id` | string or null | generated UUID | Client-provided turn id used in metadata and persisted chat logs. |
| `city`, `region`, `country`, `country_code`, `timezone` | strings or null | `null` | Location hints for online/research/model context. Country fields can be derived from timezone. |
| `images` | list of strings or null | `null` | Base64/data-URI images. They are converted to WebP and uploaded when possible; otherwise inline WebP data is used. |
| `files` | list of file attachments | `[]` | Chat-attached files with `name`, `content`, `file_type`, and `size`; content is used as context for the turn. |
| `create_new` | boolean | `false` | Requests a new conversation when resolving the conversation session. |

`files` are not content-indexing uploads. They are turn-local chat context. Route long-lived ingestion or sync work to `content-indexing`.

## REST Chat Response Modes

`POST /api/chat` uses the same event generator for streaming and non-streaming responses.

- With `stream=false`, the route aggregates events and returns JSON with `response`, `references`, `usage`, `images`, `files`, and `mermaidjsDiagram`.
- With `stream=true`, the route returns `text/plain` chunks. Plain message text may be streamed directly. Structured events are JSON objects such as `{"type":"status","data":"..."}`.
- Every logical stream event is followed by the sentinel `␃🔚␗`.
- Empty queries return the normal response path with `Please ask your query to get started.`.
- Missing or inaccessible `conversation_id` yields a normal chat response string like `Conversation <id> not found`, not a 404 from the main chat route.

## Stream Event Types

The event names are:

- `metadata`: sent early with `conversationId` and `turnId`.
- `status`: progress text, also persisted as train-of-thought/status metadata.
- `references`: object with `inferredQueries`, note `context`, `onlineContext`, and `codeContext`.
- `generated_assets`: currently carries `images`, `files`, or `mermaidjsDiagram` when generated.
- `start_llm_response` and `end_llm_response`: delimit the model answer.
- `message`: answer text; REST aggregation appends these into `response`.
- `thought`: streamed model thought/reasoning chunks when the provider path emits them.
- `usage`: token/cost metadata from the tracer when available.
- `end_response`: final logical response marker.
- `interrupt`: accepted by WebSocket control flow.
- `␃🔚␗`: internal end-event separator; clients should split on it, not render it.

## WebSocket Chat

`/api/chat/ws` is the WebSocket endpoint.

Handshake and limits:

- The `Origin` header must be present and its hostname must be in Khoj `ALLOWED_HOSTS`; otherwise the socket closes with code `1008` and reason `Origin not allowed`.
- Per-user open connections are limited to 5 for trial users and 10 for subscribed users in production-like mode.
- WebSocket chat always streams, regardless of the `stream` field in `ChatRequestBody`.
- WebSocket message and thought chunks are buffered for roughly 100 ms or 512 characters, then sent followed by the end-event sentinel.

Message shapes:

```json
{"q":"/online Summarize today's news", "conversation_id":"..."}
```

```json
{"type":"interrupt"}
```

```json
{"type":"interrupt", "query":"Narrow that to official sources only"}
```

An interrupt with no `query` asks the running turn to stop. An interrupt with `query` appends follow-up instructions into the running query and forwards them to child research/operator tasks. Acknowledgement frames use `interrupt_acknowledged` or `interrupt_message_acknowledged`.

## Command Resolution in Chat

The main chat route detects one leading command with prefix checks in this order: `/notes`, `/general`, `/online`, `/webpage`, `/image`, `/automated_task`, `/diagram`, `/code`, `/research`, `/operator` when operator is enabled, otherwise `default`.

Important behavior:

- `/automated_task` is removed and rate-limited before normal command selection, so it can combine with another command.
- `default` asks the model to select input sources and an output mode from available tools, bounded by the selected agent's allowed tools/output modes.
- If selected tools include `research`, chat reduces the command set to only `research`.
- After command validation/rate-limit checks, each command token like `/online` is stripped from the query before retrieval/model calls.
- If notes are selected but no note references are found, the notes command is removed unless it was the only command and the user has no entries, in which case Khoj returns the no-entries message.

## Conversation History and Sessions

- `GET /api/chat/history?conversation_id=<id>&n=<int>` returns `{"status":"ok","response":<conversation_log>}`. `n > 0` returns the latest `n` messages; `n < 0` returns all except the latest `abs(n)` messages.
- `DELETE /api/chat/history?conversation_id=<id>` deletes the user's conversation for the current client application and returns `{"status":"ok","message":"Conversation history cleared"}`.
- `GET /api/chat/sessions?recent=true|false` returns conversation summaries with `conversation_id`, `slug`, `agent_name`, timestamps, and agent style metadata.
- `POST /api/chat/sessions?agent_slug=<slug>` creates a session and returns `{"conversation_id":"..."}`.
- `PATCH /api/chat/title?conversation_id=<id>&title=<title>` trims the title to 200 characters and returns `success`.
- `POST /api/chat/title?conversation_id=<id>` generates a title from history unless an explicit title already exists.
- `DELETE /api/chat/conversation/message` accepts a body with `conversation_id` and `turn_id`; it returns `{"status":"ok"}` or 404 `{"status":"error","message":"Message not found"}`.

## Sharing Conversations

- `POST /api/chat/share?conversation_id=<id>` copies a private conversation into a public conversation and returns `{"status":"ok","url":"<scheme>://<host>/share/chat/<slug>/"}`.
- The share route rejects hosts whose domain is not in `ALLOWED_HOSTS` with `401 Unauthorized domain`.
- `GET /api/chat/share/history?public_conversation_slug=<slug>&n=<int>` is public and returns a scrubbed public conversation log.
- `POST /api/chat/share/fork?public_conversation_slug=<slug>` copies a public conversation into the authenticated user's private sessions and returns `next_url` plus `conversation_id`.
- `DELETE /api/chat/share?public_conversation_slug=<slug>` deletes a public conversation owned by the user and redirects to the chat page.
- Public shared histories preserve hidden-agent metadata by substituting the default agent when the hidden private agent cannot be exposed.

## Conversation File Filters

These endpoints manipulate persistent file filters on a conversation; use `search-retrieval` for query filter semantics and ranking internals.

- `GET /api/chat/conversation/file-filters/{conversation_id}` returns filenames that are both on the conversation and still present in the user's computer-source file list.
- `POST /api/chat/conversation/file-filters` with `conversation_id` and `filename` adds one file.
- `DELETE /api/chat/conversation/file-filters` with `conversation_id` and `filename` removes one file.
- `POST /api/chat/conversation/file-filters/bulk` with `conversation_id` and `filenames` adds many files.
- `DELETE /api/chat/conversation/file-filters/bulk` with `conversation_id` and `filenames` removes many files.

## Supporting Chat Endpoints

- `GET /api/chat/options` returns available slash command descriptions. It omits `operator` unless the operator feature is enabled.
- `GET /api/chat/stats` returns `num_conversations` for the authenticated user.
- `GET /api/chat/export?page=<n>` returns exportable conversation logs.
- `GET /api/chat/starters` returns conversation starter questions for the user.
- `POST /api/chat/feedback` forwards query feedback with `uquery`, `kquery`, and `sentiment`.
- `POST /api/chat/speech?text=<text>` streams `audio/mpeg` text-to-speech using the configured voice model or default voice id.

## Persistence Shape

Each completed or interrupted chat turn persists two messages: a user message and a Khoj message. Metadata can include `turnId`, query `images`, `queryFiles`, note `context`, `onlineContext`, `codeContext`, `operatorContext`, `researchContext`, generated `images`, `mermaidjsDiagram`, `trainOfThought`, and usage/tracer metadata. This is why history/share responses can contain richer data than the non-streaming chat aggregate.
