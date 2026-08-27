# Troubleshooting OpenAI-Compatible LitServe Specs

## Quick diagnosis table

| Symptom or message | Likely cause | Fix |
| --- | --- | --- |
| `predict is not a generator` | `OpenAISpec` is attached, but sync `LitAPI.predict` returns a value. | Change `return ...` to `yield ...` or `yield from ...`. Chat must be generator-based even for non-streaming clients. |
| `encode_response is not a generator` | Custom sync `encode_response` returns a value while using `OpenAISpec`. | Make custom `encode_response` yield `ChatMessage`/dict items, or remove the override and yield compatible items from `predict`. |
| `predict must be an async generator` | `enable_async=True` with `async def predict` that returns instead of yielding. | Use `async def predict(...): yield ...`. |
| `encode_response is neither a generator nor an async generator` | Async chat mode with a custom `encode_response` that returns one value. | Make it a sync generator or async generator. |
| `'<method>' is defined as async/coroutine, but 'enable_async' is not set in LitAPI.` | A LitAPI method is async, but the API was constructed with default `enable_async=False`. | Set `enable_async=True` or convert methods to sync functions. |
| `Malformed output from LitAPI.predict` | Chat `predict` yielded an unsupported object such as `{"hello": "world"}` or a scalar number. | Yield a string, `None`, a dict with `content`, a dict with `role` and `content`, or a compatible chat message. |
| Chat tool call missing or rejected | Tool call shape is wrong, often `function.arguments` is a dict instead of a JSON string. | Yield `tool_calls=[{"type":"function","function":{"name":"...","arguments":"{...}"}}]`. |
| JSON response format ignored | LitServe parsed `response_format`, but your model returned ordinary text. | Read `context["response_format"]` and emit a JSON string yourself. |
| Audio request returns 422 with `Input should be 'wav' or 'mp3'` | `input_audio.format` is not supported. | Send base64 audio with `format="wav"` or `format="mp3"`. |
| Image/audio request returns 422 | Multimodal content item shape does not match the accepted Pydantic models. | Use `{"type":"text","text":"..."}`, `{"type":"image_url","image_url":"..."}` or object `{url, detail}`, and `{"type":"input_audio","input_audio":{"data":"...","format":"wav"}}`. |
| `You are using yield in your predict method` with embeddings | `OpenAIEmbeddingSpec` does not support streaming. | Replace `yield` with `return` in `predict`. |
| `You are using yield in your encode_response method` with embeddings | Embedding `encode_response` was written as a generator. | Return `{"embeddings": output}` instead of yielding. |
| `Expected response to be a dictionary` | Custom embedding `encode_response` returned a list, tensor, string, or other non-dict response. | Return a dict with key `embeddings`, or rely on the default spec wrapper. |
| `The response does not contain the key 'embeddings'` | Embedding response dict is missing the required key. | Return `{"embeddings": vectors}` plus optional usage. |
| `Mismatch between requested and returned embeddings` | The number of vectors does not equal the number of input items in the request. | Return one vector for one string input; return one vector per list item for `list[str]` input. |
| HTTP 400: dynamic batching with client-side batching unsupported | Embedding API has `max_batch_size>1` and client sends multiple input items. | Set `max_batch_size=1` for list inputs, or send one input per request when dynamic batching is enabled. |
| Warning: `Custom API path detected` | A custom `api_path` overrides the default OpenAI-compatible path. | Use the default path for OpenAI SDK clients, or use raw HTTP for the custom path. |
| OpenAI SDK 404s while direct HTTP works | SDK base URL/path does not match the registered default route, often after custom `api_path`. | Set `base_url="http://host:port/v1"` and keep default spec path, or switch to direct HTTP for custom routes. |

## Chat generator validation

`OpenAISpec` always expects generator-style chat production. This is true even
when the client sends `stream=False`; LitServe assembles a non-streaming JSON
response from the generated items.

Bad:

```python
class BadChatAPI(ls.LitAPI):
    def predict(self, request):
        return "This is a generated output"
```

Good:

```python
class GoodChatAPI(ls.LitAPI):
    def predict(self, request):
        yield "This is a generated output"
```

Bad custom encoder:

```python
class BadEncoderAPI(ls.LitAPI):
    def predict(self, request):
        yield "raw"

    def encode_response(self, output):
        return {"role": "assistant", "content": "encoded"}
```

Good custom encoder:

```python
class GoodEncoderAPI(ls.LitAPI):
    def predict(self, request):
        yield "raw"

    def encode_response(self, output_stream):
        for output in output_stream:
            yield {"role": "assistant", "content": output}
```

## Async mode validation

Use async mode only when the `LitAPI` is constructed with `enable_async=True`.

Good:

```python
class AsyncAPI(ls.LitAPI):
    async def predict(self, request):
        yield "This is async output"

api = AsyncAPI(enable_async=True, spec=OpenAISpec())
```

If `enable_async=True`, `predict` must be an async generator. Returning a string
from `async def predict` is not enough.

If `enable_async=False`, none of `decode_request`, `predict`, or
`encode_response` may be coroutine/async-generator methods.

## Malformed chat output

Default `OpenAISpec.encode_response` accepts these yielded items:

```python
yield "text"
yield {"content": "text"}
yield {"role": "assistant", "content": "text"}
yield {"role": "assistant", "content": "", "tool_calls": [...]}  # tool call
yield {"role": "assistant", "content": "", "prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}
```

It rejects unsupported values:

```python
yield 123
yield {"hello": "world"}
yield []
```

When debugging, first print or log the exact yielded items from `predict` before
custom encoders transform them.

## Tool call problems

A tool call is assistant message metadata, not a separate response object.

Correct:

```python
yield {
    "role": "assistant",
    "content": "",
    "tool_calls": [
        {
            "id": "call_abc123",
            "type": "function",
            "function": {
                "name": "get_current_weather",
                "arguments": "{\"location\": \"Boston, MA\"}",
            },
        }
    ],
}
```

Common mistakes:

- Returning `function.arguments` as `{"location": "Boston"}` instead of the
  JSON string `"{\"location\": \"Boston\"}"`.
- Forgetting `content`; include `content=""` when the assistant is only calling
  a tool.
- Expecting LitServe to execute the tool. `OpenAISpec` only formats the chat
  completion response. MCP tool exposure belongs to the MCP sub-skill.

## `response_format` problems

`response_format` is request metadata. LitServe validates the shape and makes it
available through context, but your implementation must generate matching JSON
content.

Pattern:

```python
def predict(self, request, context):
    fmt = context.get("response_format")
    if fmt:
        yield {"role": "assistant", "content": '{"ok": true}'}
    else:
        yield "plain text"
```

If the client requests `json_schema` and receives plain text, fix the model or
encoder logic; this is not a LitServe routing error.

## Multimodal request validation

Accepted image forms:

```python
{"type": "image_url", "image_url": "https://example.test/image.png"}
{"type": "image_url", "image_url": {"url": "https://example.test/image.png", "detail": "low"}}
```

Accepted audio form:

```python
{"type": "input_audio", "input_audio": {"data": "<base64>", "format": "wav"}}
```

Use `format="mp3"` for MP3. Do not use `flac`, `ogg`, or arbitrary format
labels unless you add your own non-OpenAI route outside this spec.

## Embedding response rejection

For embeddings, decide whether the spec default encoder is enough.

Default encoder pattern:

```python
class EmbedAPI(ls.LitAPI):
    def predict(self, inputs):
        return [[0.1, 0.2, 0.3]]
```

Custom encoder pattern:

```python
class EmbedAPI(ls.LitAPI):
    def predict(self, inputs):
        return [[0.1, 0.2, 0.3]]

    def encode_response(self, output):
        return {"embeddings": output, "prompt_tokens": 3, "total_tokens": 3}
```

Do not write:

```python
def predict(self, inputs):
    yield [0.1, 0.2, 0.3]

def encode_response(self, output):
    yield {"embeddings": output}
```

If the response is rejected:

1. Confirm the custom `encode_response` returns a dict.
2. Confirm the dict has `embeddings`.
3. Confirm `embeddings` is a list of vectors, or a single 1-D vector only when
   the request has exactly one input item.
4. Confirm vector count equals requested item count.
5. If using NumPy/Torch vectors, ensure those libraries are actually imported in
   the process so the spec can detect and convert them.

## Embedding batching conflict

This fails:

```python
api = EmbedAPI(max_batch_size=2, spec=OpenAIEmbeddingSpec())
# Client sends one request with multiple inputs:
client.embeddings.create(model="lit", input=["a", "b"])
```

Use one of these instead:

```python
# Client-side batching only:
api = EmbedAPI(max_batch_size=1, spec=OpenAIEmbeddingSpec())
client.embeddings.create(model="lit", input=["a", "b"])
```

```python
# Server dynamic batching only:
api = EmbedAPI(max_batch_size=2, batch_timeout=0.1, spec=OpenAIEmbeddingSpec())
client.embeddings.create(model="lit", input="a")
client.embeddings.create(model="lit", input="b")
```

## Custom path and OpenAI SDK compatibility

OpenAI SDK clients should use:

```python
client = OpenAI(base_url="http://127.0.0.1:8000/v1", api_key="lit")
client.chat.completions.create(...)
client.embeddings.create(...)
```

That maps to `/v1/chat/completions` and `/v1/embeddings`.

If a server uses `api_path="/v2/chat/completions"`, the OpenAI SDK will not
magically discover it. Use direct HTTP:

```python
import requests
requests.post("http://127.0.0.1:8000/v2/chat/completions", json={...})
```
