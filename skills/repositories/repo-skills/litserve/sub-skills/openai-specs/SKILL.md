---
name: openai-specs
description: "Build and debug LitServe OpenAI-compatible chat completions and
  embeddings endpoints with OpenAISpec and OpenAIEmbeddingSpec."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# LitServe OpenAI-Compatible Specs

Use this sub-skill when the user wants a LitServe server that looks like the
OpenAI API, including `/v1/chat/completions`, `/v1/embeddings`, streaming chat,
tool calls, `response_format`, image/audio chat messages, or embedding response
shape debugging.

For the underlying LitServe server model, `LitAPI` lifecycle, `LitServer.run`,
ports, process settings, auth, middleware, and non-OpenAI routes, first load the
root LitServe router at `../../SKILL.md` and the server basics sub-skill at
`../server-basics/SKILL.md`.

Do not use this sub-skill for MCP tool exposure, GPU/Torch benchmark paths, or
throughput benchmark harnesses.

## Router

- **Chat completions**: use `OpenAISpec` for `/v1/chat/completions`.
  - Implement `LitAPI.predict` as a generator, even when clients send
    non-streaming requests.
  - Return simple text by yielding strings, or return richer messages by yielding
    dicts or `ChatMessage`-compatible objects with `role`, `content`,
    `tool_calls`, and optional token usage keys.
  - If you override `encode_response`, it must also be a generator in sync mode.
- **Async chat completions**: set `enable_async=True` on the `LitAPI` and make
  `predict` an async generator. `decode_request` may be sync or async;
  overridden `encode_response` must yield from either a sync generator or async
  generator.
- **Streaming chat**: keep the server implementation generator-based. The client
  request field `stream=True` selects SSE chunks; `stream=False` returns one
  JSON `chat.completion` response assembled from the same generated messages.
- **Tool calls**: yield a chat message with `tool_calls=[...]`; keep
  `function.arguments` as a JSON string.
- **Structured JSON output**: read `response_format` from the request/context and
  yield JSON text yourself. LitServe accepts OpenAI-style `text`, `json_object`,
  and `json_schema` request shapes, but it does not synthesize or validate model
  JSON for you.
- **Image and audio inputs**: accept `messages[*].content` as either text or a
  list of content items. Image items use `image_url`; audio items use
  `input_audio` with `format` limited to `wav` or `mp3`.
- **Embeddings**: use `OpenAIEmbeddingSpec` for `/v1/embeddings`.
  - `predict` and `encode_response` must return values, not generators.
  - Return `{"embeddings": <list-of-vectors>}` from custom `encode_response`,
    plus optional `prompt_tokens` and `total_tokens`.
  - Client-side batching (a request with multiple input items) is allowed only
    when server dynamic batching is not also enabled.
- **OpenAI SDK compatibility**: keep the default spec paths. A custom
  `api_path` registers the endpoint, but the OpenAI Python SDK only targets the
  default `/v1/chat/completions` and `/v1/embeddings` paths through
  `base_url="http://host:port/v1"`.

## Minimal implementation patterns

Chat completions:

```python
import litserve as ls
from litserve import OpenAISpec

class ChatAPI(ls.LitAPI):
    def predict(self, request):
        # request is a ChatCompletionRequest
        yield "This is a generated output"

if __name__ == "__main__":
    api = ChatAPI(spec=OpenAISpec())
    server = ls.LitServer(api)
    server.run(port=8000)
```

Embeddings:

```python
import litserve as ls
from litserve import OpenAIEmbeddingSpec

class EmbeddingAPI(ls.LitAPI):
    def predict(self, inputs):
        n = len(inputs) if isinstance(inputs, list) else 1
        return [[0.0, 1.0, 0.5] for _ in range(n)]

    def encode_response(self, output):
        return {"embeddings": output}

if __name__ == "__main__":
    api = EmbeddingAPI(spec=OpenAIEmbeddingSpec())
    server = ls.LitServer(api)
    server.run(port=8000)
```

Bundled runnable examples:

- `scripts/openai_chat_server.py` — chat completions server with streaming,
  usage, tool-call, `response_format`, image, and audio request handling hooks.
- `scripts/openai_embedding_server.py` — deterministic embeddings server with
  OpenAI-compatible response shape and optional usage accounting.

## References

- `references/api-reference.md` — request/response models, endpoint paths,
  response assembly rules, validation contracts, and import paths.
- `references/workflows.md` — implementation recipes for chat, streaming,
  tool calls, JSON response format, multimodal messages, embeddings, batching,
  and OpenAI SDK clients.
- `references/troubleshooting.md` — failure matrix for generator validation,
  async mode, malformed outputs, embedding response rejection, multimodal
  payload errors, batching conflicts, and custom path warnings.

## Handoff checklist for future agents

Before claiming an OpenAI-compatible LitServe endpoint is ready:

1. Confirm the correct spec is attached: `OpenAISpec()` for chat or
   `OpenAIEmbeddingSpec()` for embeddings.
2. Confirm the route is the spec default unless the user intentionally chose raw
   HTTP over OpenAI SDK compatibility.
3. For chat, confirm `predict` is generator-based and any custom
   `encode_response` is generator-based.
4. For async chat, confirm `enable_async=True` and `predict` is an async
   generator.
5. For embeddings, confirm no generator/yield is used and the response includes
   an `embeddings` key with one vector per requested input item.
6. Exercise both SDK-style clients and direct HTTP only within the user's target
   environment; do not rely on repository checkout paths at runtime.
