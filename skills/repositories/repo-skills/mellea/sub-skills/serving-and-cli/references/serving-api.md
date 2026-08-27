# OpenAI-compatible serving API

Use this reference to implement or call the HTTP boundary provided by Mellea
`0.8.0.dev0`. It is compatible with the OpenAI **Chat Completions** shape; it is
not a full OpenAI platform implementation.

## Served application contract

The application is a Python file with a callable named `serve`. A robust async
shape is:

```python
from typing import Any

from mellea.core import ModelOutputThunk
from mellea.serve import ChatMessage


async def serve(
    input: list[ChatMessage],
    requirements: list[str | None] | None = None,
    model_options: dict[str, Any] | None = None,
    format: type | None = None,
    client_options: dict[str, Any] | None = None,
) -> ModelOutputThunk:
    if not input:
        raise ValueError("messages must not be empty")
    prompt = input[-1].get_text_content()
    # Choose an allowlisted backend and return a Mellea output thunk.
    ...
```

The first three keyword names are part of the callback contract:

- `input`: parsed `ChatMessage` instances.
- `requirements`: request requirements, including `None` entries if supplied.
- `model_options`: supported generation fields translated to Mellea
  `ModelOption` keys, plus any unknown request fields.

The server always calls the callback with those three keywords. `format` and
`client_options` are optional and are passed only if their names appear in the
signature. A synchronous callback runs via `asyncio.to_thread`; an `async def`
callback is awaited directly. Return a `ModelOutputThunk` or a compatible
Mellea sampling result with output value, metadata, streaming state, and any
tool calls expected by the selected response path.

Top-level code executes while the script is imported. Keep imports deterministic
and avoid network calls, training, migration, secret printing, and irreversible
initialization at import time. Missing file, import failures, or a missing
`serve` callable prevent startup.

## Public message models

The stable `mellea.serve` namespace exports:

- `ChatMessage`
- `TextContent`
- `ImageUrlContent`
- `InputAudioData`
- `InputAudioContent`
- `MessageContent`

`ChatMessage.role` accepts `system`, `user`, `assistant`, `tool`, or `function`.
`content` may be a string, `null`, or a list of text, image URL, and input-audio
parts. It also has optional `name`, `tool_call_id`, and `function_call` fields.
Use its helpers instead of assuming string content:

- `get_text_content()` concatenates text parts with spaces.
- `get_image_urls()` returns declared image URLs.
- `get_image_blocks()` converts HTTP(S) URLs and data URIs to Mellea blocks and
  rejects malformed or unsupported URLs.
- `get_audio_blocks()` converts base64 audio parts to `AudioBlock` values and
  rejects malformed payloads.

Model capability, image fetching, audio transcription, and maximum payload size
are not guaranteed by the HTTP envelope. Route those concerns to the selected
backend and impose request-body limits at the deployment boundary.

## Endpoints

A running process registers:

```text
GET  /health
POST /v1/chat/completions
```

`GET /health` returns `{"status":"pass"}`. It is a liveness check only: it does
not prove that a backend, model, credentials, or downstream service works.
FastAPI documentation routes are also present under their defaults. There is no
built-in authentication.

A minimal request is:

```json
{
  "model": "local-default",
  "messages": [
    {"role": "user", "content": "Give one concise answer."}
  ]
}
```

Both `model` and `messages` are required by the request schema, but the current
schema does not require the message list to be non-empty. Validate that in the
callback and raise `ValueError` for a client-visible 400 rather than allowing an
indexing failure to become 500.

## Request fields and translation

| Request field | Validation/default | Callback behavior |
|---|---|---|
| `model` | required string | Excluded from `model_options`; included in `client_options` and echoed in responses |
| `messages` | required list | Passed as `input`; excluded from options |
| `requirements` | default empty list; list of string or null | Passed separately |
| `temperature` | default `1.0`, range 0-2 | Forwarded as `ModelOption.TEMPERATURE` |
| `max_tokens` | optional integer | Forwarded as `ModelOption.MAX_NEW_TOKENS` |
| `seed` | optional integer | Forwarded as `ModelOption.SEED` |
| `stream` | default false | Forwarded as `ModelOption.STREAM` only when true; also selects SSE |
| `tools` | optional function-tool list | Forwarded as `ModelOption.TOOLS` |
| `tool_choice` | `none`, `auto`, or object | Forwarded as `ModelOption.TOOL_CHOICE` |
| `n` | default 1, minimum 1 | Excluded; values over 1 receive 400 |
| `response_format` | text, json_object, or json_schema | Converted separately; never forwarded |
| `stream_options.include_usage` | default false | Controls final SSE usage only |
| `user` | optional string | Metadata only; excluded from generation options |

Accepted but currently **not forwarded** are `top_p`, `stop`,
`presence_penalty`, `frequency_penalty`, `logit_bias`, legacy `functions`, and
legacy `function_call`. Do not promise that these alter generation.

The request model allows unknown top-level fields. Current option-building code
forwards those unknown fields into `model_options`, and `client_options` receives
a full model dump including defaults. Therefore:

- do not treat either dictionary as trusted;
- allowlist options before passing them to a backend;
- never allow an extra field to select a URL, credential source, import, file,
  or executable;
- do not assume `client_options` contains only fields explicitly sent by the
  client.

## Non-streaming response and errors

A success contains one choice:

```json
{
  "id": "chatcmpl-...",
  "object": "chat.completion",
  "created": 1730000000,
  "model": "local-default",
  "choices": [
    {
      "index": 0,
      "message": {"role": "assistant", "content": "...", "tool_calls": null},
      "finish_reason": "stop"
    }
  ],
  "system_fingerprint": null,
  "usage": null
}
```

Usage is populated when the returned output contains generation usage metadata;
missing token fields default to zero and total tokens can be derived. Finish
reason is taken from tool calls or recognized Ollama/OpenAI/Watsonx/LiteLLM raw
metadata, otherwise it defaults to `stop`. The request's model string is echoed;
it is not proof of which backend actually ran. Only one completion is supported.

Validation errors are converted from FastAPI's usual 422 to an OpenAI-shaped
400. `n > 1`, invalid response schemas, and callback `ValueError` also become
400 `invalid_request_error`. A `ValueError` message is client-visible, so do not
include secrets or internals. Other callback/backend exceptions are logged and
returned as a generic 500:

```json
{
  "error": {
    "message": "Internal server error",
    "type": "server_error",
    "param": null,
    "code": null
  }
}
```

## Response formats

### Text and JSON object

`{"type":"text"}` and `{"type":"json_object"}` create no format model. In
this release, `json_object` sends no special generation signal and gives no JSON
guarantee. Add an instruction and validate/parse the returned value in the
application if JSON is required.

### JSON schema

The wire shape is:

```json
{
  "type": "json_schema",
  "json_schema": {
    "name": "Answer",
    "strict": true,
    "schema": {
      "type": "object",
      "properties": {
        "answer": {"type": "string"},
        "confidence": {"type": "number"}
      },
      "required": ["answer"],
      "additionalProperties": false
    }
  }
}
```

`name` and `schema` are required. `strict` is accepted but ignored by the server.
The converter creates a Pydantic model and passes it as `format` only when the
callback declares that parameter. The application must then pass `format` into
the Mellea generation call. If the callback omits or ignores it, the request can
still return arbitrary text.

Supported conversion features are:

- top-level and nested objects with named properties and required fields;
- string, integer, number, and boolean fields;
- homogeneous arrays;
- primitive enums;
- a single non-null type plus `null`;
- local `$ref` into `$defs` or `definitions`;
- simple object `allOf` merging;
- representable `anyOf` and `oneOf` unions;
- boolean `additionalProperties` on named objects;
- schema-valued `additionalProperties` for a pure nested map.

Important conversion semantics:

- The top level must be a non-empty object with properties.
- `additionalProperties: false` forbids unknown fields.
- `additionalProperties: true` maps to Pydantic's ignore behavior, not retention.
- A schema-valued `additionalProperties` cannot be combined with named
  properties.
- Optional properties become nullable Python fields with default `None`; this
  is a Pydantic representation and not a complete JSON Schema engine.
- Constraints such as lengths, regexes, numeric ranges, and every JSON Schema
  draft feature are not generally preserved.

Rejected cases include non-local references, recursive references, missing
explicit `type` on ordinary nodes, tuple-style array items, unsupported types,
empty object shapes, and conflicting `allOf` or additional-properties forms.
Validate a representative good and bad payload against the generated behavior
before spending on model inference.

## SSE streaming

A streaming request sets `"stream": true`. The response content type is
`text/event-stream`, with events in this order:

1. assistant-role chunk;
2. zero or more content chunks;
3. optional tool-call delta chunk with an `index` for each tool call;
4. final chunk with `finish_reason` and optional usage;
5. `data: [DONE]`.

Set `{"stream_options":{"include_usage":true}}` to request usage on the final
chunk. Without it, usage is null even if backend metadata exists. Non-streaming
usage is unaffected by `stream_options`.

The server distinguishes computed and uncomputed output:

- computed thunk: emits the complete value as one content chunk;
- uncomputed thunk: repeatedly awaits `output.astream()` and forwards non-empty
  deltas until the output reports itself computed.

For real incremental output, return an uncomputed thunk from an async callback.
A typical application checks `ModelOption.STREAM` in `model_options` and invokes
an async generation API with `await_result=False`. Backend support still
controls whether generation is actually incremental.

If failure occurs after the HTTP stream starts, status cannot be changed to 500.
The server emits an SSE error object followed by `[DONE]`. The current SSE error
message includes the exception text, unlike the generic non-streaming 500, so
do not raise exceptions containing credentials, full provider payloads, or
sensitive user data.

## Allowlisted model routing

The `model` field does not choose a Mellea backend automatically. Declare
`client_options`, map the requested string to an internal allowlist, and reject
unknown values with `ValueError`:

```python
ROUTES = {
    "fast": fast_session,
    "accurate": accurate_session,
}

requested = (client_options or {}).get("model")
session = ROUTES.get(requested)
if session is None:
    raise ValueError("unknown model route")
```

Prefer rejection over silent fallback when a client must know which capability
ran. Keep session creation, provider endpoints, and credentials server-side.
Omit `client_options` entirely when every request should use one fixed route.

## Tools and MCP boundary

Tool definitions and `tool_choice` pass through the HTTP envelope, and generated
tool calls can appear in normal or streaming responses. The server does not
provide a complete authorization/execution loop for arbitrary tools. Route tool
registration, argument validation, execution policy, result messages, and MCP
to `tools-and-agents`; keep this reference limited to serialization and SSE
reassembly.
