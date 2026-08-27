# LitServe OpenAI Specs API Reference

This reference covers the installed LitServe OpenAI-compatible specs. It is
self-contained for runtime use and depends only on the installed package.

## Public imports

```python
import litserve as ls
from litserve import OpenAISpec, OpenAIEmbeddingSpec
from litserve.specs.openai import (
    AudioContent,
    ChatCompletionChunk,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
    ChatMessageWithUsage,
    Function,
    FunctionCall,
    ImageContent,
    ImageContentURL,
    InputAudio,
    ResponseFormatJSONSchema,
    ResponseFormatJSONObject,
    ResponseFormatText,
    TextContent,
    Tool,
    ToolCall,
    ToolChoice,
    UsageInfo as ChatUsageInfo,
)
from litserve.specs.openai_embedding import (
    Embedding,
    EmbeddingRequest,
    EmbeddingResponse,
    OpenAIEmbeddingSpec,
    UsageInfo as EmbeddingUsageInfo,
)
```

The top-level package exposes `OpenAISpec` and `OpenAIEmbeddingSpec`; detailed
Pydantic request/response classes live under `litserve.specs.openai` and
`litserve.specs.openai_embedding`.

## Endpoint registration

| Spec | Default path | Methods | OpenAI SDK base URL |
| --- | --- | --- | --- |
| `OpenAISpec()` | `/v1/chat/completions` | `POST`, `OPTIONS` | `http://host:port/v1` |
| `OpenAIEmbeddingSpec()` | `/v1/embeddings` | `POST`, health/options handler | `http://host:port/v1` |

Attach a spec to the `LitAPI` or `LitServer`:

```python
api = MyChatAPI(spec=OpenAISpec())
server = ls.LitServer(api)
```

or:

```python
server = ls.LitServer(MyChatAPI(), spec=OpenAISpec())
```

Prefer the default paths for OpenAI SDK compatibility. If a `LitAPI` is created
with a custom `api_path`, the spec registers that path and emits a warning that
the OpenAI SDK only supports the default path. Use raw HTTP clients for custom
paths.

## `OpenAISpec` chat completions

### Request model

`OpenAISpec.decode_request(request, context_kwargs=None)` returns the
`ChatCompletionRequest` object passed to the endpoint.

`ChatCompletionRequest` fields:

| Field | Type/shape | Notes |
| --- | --- | --- |
| `model` | `str | None` | Returned in completion/chunk responses. |
| `messages` | `list[ChatMessage]` | Required chat transcript. |
| `temperature` | `float | None` | Default `0.7`; copied into context. |
| `top_p` | `float | None` | Default `1.0`; copied into context. |
| `n` | `int | None` | Number of choices; LitServe queues one internal request per choice. |
| `max_tokens` | `int | None` | Backward-compatible field. |
| `max_completion_tokens` | `int | None` | Available to `predict`/context for stopping logic. |
| `stop` | `str | list[str] | None` | Copied into context. |
| `stream` | `bool | None` | Selects SSE chunks vs one JSON response. |
| `presence_penalty` | `float | None` | Copied into context. |
| `frequency_penalty` | `float | None` | Copied into context. |
| `user` | `str | None` | Copied into context. |
| `tools` | `list[Tool] | None` | OpenAI-style function tool schemas. |
| `tool_choice` | `"auto" | "none" | "any" | None` | Default `auto`. |
| `response_format` | text/json object/json schema union | Request-only hint; your API must produce matching content. |
| `reasoning_effort` | `"low" | "medium" | "high" | None` | Invalid values produce validation errors. |
| `metadata` | `dict[str, str] | None` | Copied into context. |

`OpenAISpec.populate_context` copies every request field except `messages` into
LitServe context. Define `predict(self, request, context)` or
`encode_response(self, output_stream, context)` when your implementation needs
`temperature`, `tools`, `response_format`, `metadata`, or token limits.

### Chat messages and content variants

`ChatMessage` fields:

| Field | Shape | Notes |
| --- | --- | --- |
| `role` | `str` | Usually `system`, `user`, `assistant`, or `tool`. |
| `content` | `str | list[TextContent | ImageContent | AudioContent] | None` | Multimodal lists are accepted for user messages. |
| `name` | `str | None` | Optional OpenAI-compatible name. |
| `tool_calls` | `list[ToolCall] | None` | Assistant tool calls. |
| `tool_call_id` | `str | None` | Tool response linkage. |

Content item shapes:

```python
{"type": "text", "text": "What is in this image?"}
{"type": "image_url", "image_url": "https://example.test/image.png"}
{"type": "image_url", "image_url": {"url": "https://example.test/image.png", "detail": "low"}}
{"type": "input_audio", "input_audio": {"data": "<base64>", "format": "wav"}}
```

Image detail is `auto`, `low`, or `high`. Audio format is limited to `wav` or
`mp3`; unsupported formats fail request validation.

Tool call shape:

```python
{
    "id": "call_abc123",
    "type": "function",
    "function": {
        "name": "get_current_weather",
        "arguments": "{\"location\": \"Boston, MA\"}",
    },
}
```

`function.arguments` must be a string containing JSON, not a Python dict.
`ToolCall.index` defaults to `0` when omitted.

### Response format models

Accepted `response_format` request variants:

```python
{"type": "text"}
{"type": "json_object"}
{
    "type": "json_schema",
    "json_schema": {
        "name": "calendar_event",
        "description": "optional",
        "schema": {"type": "object"},
        "strict": True,
    },
}
```

LitServe parses these request shapes and exposes the parsed value in context.
Your `predict`/`encode_response` still controls the response content. Return a
JSON string when the client requests JSON.

### Chat output contract

`OpenAISpec` is streaming internally. In synchronous mode:

- `LitAPI.predict` **must be a generator**.
- If you override `LitAPI.encode_response`, it **must be a generator**.
- Yielding strings is enough for basic assistant text.
- Yielding dicts or `ChatMessage`-compatible values lets you set roles,
  `tool_calls`, and usage.

Accepted default `OpenAISpec` output items from `predict`:

| Output item | Encoded as |
| --- | --- |
| `None` | assistant message with `content=None` |
| `"token"` | `{"role": "assistant", "content": "token"}` |
| `{"role": "assistant", "content": "token"}` | used as-is |
| `{"content": "token"}` | role set to `assistant` |
| non-empty list whose last item has `role` and `content` | last item used |

Anything else raises an HTTP 500 with a message beginning
`Malformed output from LitAPI.predict`.

Usage accounting keys may be included in yielded dicts or `ChatMessageWithUsage`:

```python
yield {
    "role": "assistant",
    "content": "10 + 6 is equal to 16.",
    "prompt_tokens": 25,
    "completion_tokens": 10,
    "total_tokens": 35,
}
```

`OpenAISpec` removes `prompt_tokens`, `completion_tokens`, and `total_tokens`
from the message body and aggregates them into response usage.

### Chat response assembly

For `stream=False`, LitServe returns a `ChatCompletionResponse`:

```json
{
  "id": "chatcmpl-...",
  "object": "chat.completion",
  "created": 1710000000,
  "model": "lit",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "concatenated content",
        "tool_calls": null
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
}
```

For `stream=True`, LitServe returns `text/event-stream` lines:

```text
data: {"object":"chat.completion.chunk", "choices":[{"delta": {...}}], ...}

data: {"object":"chat.completion.chunk", "choices":[{"delta": {}, "finish_reason":"stop"}], "usage": {...}, ...}

data: [DONE]
```

Usage is attached to the final chunk. The final finish reason emitted by the
current implementation is `stop`.

### Async chat validation

With `enable_async=True`:

- `predict` must be an async generator (`async def` containing `yield`).
- `decode_request` may be synchronous or asynchronous.
- The default `encode_response` is allowed; a custom `encode_response` must be a
  sync generator or async generator.

Without `enable_async=True`, do not define `decode_request`, `predict`, or
`encode_response` as coroutine/async generator methods.

## `OpenAIEmbeddingSpec` embeddings

### Request model

`OpenAIEmbeddingSpec.decode_request(request, context_kwargs=None)` passes through
the embedding request input for prediction. The request model accepts:

| Field | Type/shape | Notes |
| --- | --- | --- |
| `input` | `str | list[str] | list[int] | list[list[int]]` | Text or token inputs. For most implementations, support `str` and `list[str]`. |
| `model` | `str` | Returned in the final response. |
| `dimensions` | `int | None` | Request hint; your implementation must honor it if needed. |
| `encoding_format` | `"float" | "base64"` | Accepted by the request model; LitServe does not automatically transform vectors. |
| `user` | `str | None` | Client metadata. |

### Embedding output contract

`OpenAIEmbeddingSpec` is not a streaming spec:

- Do not use `yield` in `predict`.
- Do not use `yield` in a custom `encode_response`.
- Return an embeddings dict from `encode_response`, or rely on the default
  `encode_response` to wrap `predict` output as `{"embeddings": output}`.

Recommended custom response:

```python
def encode_response(self, output):
    return {
        "embeddings": output,
        "prompt_tokens": 10,
        "total_tokens": 10,
    }
```

Final response shape:

```json
{
  "object": "list",
  "model": "lit",
  "data": [
    {"object": "embedding", "index": 0, "embedding": [0.1, 0.2, 0.3]}
  ],
  "usage": {"prompt_tokens": 10, "total_tokens": 10}
}
```

The spec normalizes one-dimensional list/NumPy/Torch vector outputs into a
single embedding row when those libraries are already imported. It validates
that the number of returned vectors matches the number of requested input items.

### Embedding batching rules

- A client may send one input item, e.g. `input="hello"`.
- A client may send multiple input texts, e.g. `input=["a", "b"]`, when server
  dynamic batching is disabled (`max_batch_size=1`).
- Server dynamic batching can batch multiple concurrent single-input requests
  when `max_batch_size > 1`.
- Do not combine client-side batching with server dynamic batching. If a request
  has multiple input items and `max_batch_size > 1`, LitServe returns HTTP 400
  with the detail explaining to set `max_batch_size=1` or send one input from
  the client.
