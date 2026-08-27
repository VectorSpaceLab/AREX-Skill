# Workflows for OpenAI-Compatible LitServe Endpoints

## 1. Make a chat completions server

Use `OpenAISpec` and keep `predict` generator-based.

```python
import litserve as ls
from litserve import OpenAISpec

class ChatAPI(ls.LitAPI):
    def setup(self, device):
        self.model = None

    def predict(self, request):
        # request is a ChatCompletionRequest
        yield "This is a generated output"

if __name__ == "__main__":
    server = ls.LitServer(ChatAPI(spec=OpenAISpec()))
    server.run(port=8000)
```

Client:

```python
from openai import OpenAI

client = OpenAI(base_url="http://127.0.0.1:8000/v1", api_key="lit")
response = client.chat.completions.create(
    model="lit",
    messages=[
        {"role": "system", "content": "You are helpful."},
        {"role": "user", "content": "How are you?"},
    ],
)
print(response.choices[0].message.content)
```

Direct HTTP equivalent:

```bash
curl -s http://127.0.0.1:8000/v1/chat/completions \
  -H 'content-type: application/json' \
  -d '{"model":"lit","messages":[{"role":"user","content":"hello"}]}'
```

## 2. Stream chat completions

Do not add a separate streaming route. The same `OpenAISpec` endpoint streams
when the request has `stream=True`.

```python
response = client.chat.completions.create(
    model="lit",
    messages=[{"role": "user", "content": "Stream one sentence."}],
    stream=True,
)
for chunk in response:
    print(chunk.choices[0].delta.content)
```

Implementation pattern:

```python
class StreamingChatAPI(ls.LitAPI):
    def predict(self, request):
        for token in ["This", " is", " streamed", "."]:
            yield {"role": "assistant", "content": token}
        yield {
            "role": "assistant",
            "content": "",
            "prompt_tokens": 4,
            "completion_tokens": 4,
            "total_tokens": 8,
        }
```

For non-streaming requests, LitServe concatenates yielded content into one
assistant message. For streaming requests, LitServe emits SSE chunks and a final
chunk containing usage.

## 3. Return usage accounting

Attach usage fields to any yielded chat message dict. LitServe aggregates usage
across generated items and choices.

```python
class UsageChatAPI(ls.LitAPI):
    def predict(self, request):
        yield {
            "role": "assistant",
            "content": "10 + 6 is equal to 16.",
            "prompt_tokens": 25,
            "completion_tokens": 10,
            "total_tokens": 35,
        }
```

For token-by-token usage, include per-token increments:

```python
for token in ["1", "2", "3"]:
    yield {
        "role": "assistant",
        "content": token,
        "prompt_tokens": 0,
        "completion_tokens": 1,
        "total_tokens": 1,
    }
```

## 4. Return tool calls

Read `tools` from the request or context, then yield a message with `tool_calls`.
The tool call arguments must be a JSON string.

```python
import json

class ToolCallingAPI(ls.LitAPI):
    def predict(self, request, context):
        tools = context.get("tools") or []
        if tools:
            first = tools[0]
            function = first["function"] if isinstance(first, dict) else first.function
            name = function["name"] if isinstance(function, dict) else function.name
            yield {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": "call_abc123",
                        "type": "function",
                        "function": {
                            "name": name,
                            "arguments": json.dumps({"location": "Boston, MA"}),
                        },
                    }
                ],
            }
            return
        yield "No tool was supplied."
```

OpenAI client:

```python
response = client.chat.completions.create(
    model="lit",
    messages=[{"role": "user", "content": "Weather in Boston?"}],
    tools=[
        {
            "type": "function",
            "function": {
                "name": "get_current_weather",
                "description": "Get the current weather",
                "parameters": {
                    "type": "object",
                    "properties": {"location": {"type": "string"}},
                    "required": ["location"],
                },
            },
        }
    ],
)
print(response.choices[0].message.tool_calls[0].function.name)
```

## 5. Honor `response_format` JSON requests

LitServe parses OpenAI-style `response_format`, including `json_schema`, and
exposes it in context. Your API is responsible for emitting JSON text that
matches the user's expectation.

```python
import json

class StructuredOutputAPI(ls.LitAPI):
    def predict(self, request, context):
        if context.get("response_format"):
            yield {
                "role": "assistant",
                "content": json.dumps(
                    {
                        "name": "Science Fair",
                        "date": "Friday",
                        "participants": ["Alice", "Bob"],
                    },
                    separators=(",", ":"),
                ),
            }
            return
        yield "No structured format was requested."
```

Client:

```python
response = client.chat.completions.create(
    model="lit",
    messages=[
        {"role": "system", "content": "Extract event information."},
        {"role": "user", "content": "Alice and Bob go to a fair Friday."},
    ],
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "calendar_event",
            "schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "date": {"type": "string"},
                    "participants": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["name", "date", "participants"],
            },
            "strict": True,
        },
    },
)
```

## 6. Handle image and audio chat messages

The request object has parsed message content. A message `content` may be a
string or a list of Pydantic content items.

```python
def iter_content_parts(message):
    content = message.content
    if isinstance(content, str) or content is None:
        yield {"type": "text", "text": content or ""}
        return
    for item in content:
        if hasattr(item, "model_dump"):
            yield item.model_dump()
        else:
            yield item

class MultimodalChatAPI(ls.LitAPI):
    def predict(self, request):
        seen = []
        for message in request.messages:
            for part in iter_content_parts(message):
                seen.append(part.get("type", "text"))
        yield {"role": "assistant", "content": f"received: {', '.join(seen)}"}
```

Valid client message examples:

```python
messages = [
    {
        "role": "user",
        "content": [
            {"type": "text", "text": "What's in this image?"},
            {
                "type": "image_url",
                "image_url": {
                    "url": "https://example.test/image.png",
                    "detail": "low",
                },
            },
        ],
    }
]
```

```python
messages = [
    {
        "role": "user",
        "content": [
            {"type": "text", "text": "What is in this recording?"},
            {"type": "input_audio", "input_audio": {"data": base64_audio, "format": "wav"}},
        ],
    }
]
```

Only `wav` and `mp3` audio formats are accepted by the request model.

## 7. Use async chat methods

Set `enable_async=True` and make `predict` an async generator.

```python
class AsyncChatAPI(ls.LitAPI):
    async def decode_request(self, request):
        return request

    async def predict(self, request):
        for token in ["Async", " response"]:
            yield token

    async def encode_response(self, output_stream, context):
        async for output in output_stream:
            yield {"role": "assistant", "content": output}

api = AsyncChatAPI(enable_async=True, spec=OpenAISpec())
server = ls.LitServer(api)
```

If any method is async but `enable_async` is false, LitServe raises a validation
error before serving.

## 8. Make an embeddings server

Use `OpenAIEmbeddingSpec`. Do not yield from embedding methods.

```python
import hashlib
import litserve as ls
from litserve import OpenAIEmbeddingSpec

DIMENSIONS = 768

def embed(text):
    digest = hashlib.sha256(str(text).encode("utf-8")).digest()
    return [digest[i % len(digest)] / 255.0 for i in range(DIMENSIONS)]

class EmbeddingAPI(ls.LitAPI):
    def predict(self, inputs):
        items = inputs if isinstance(inputs, list) else [inputs]
        return [embed(item) for item in items]

    def encode_response(self, output):
        return {"embeddings": output, "prompt_tokens": 0, "total_tokens": 0}

server = ls.LitServer(EmbeddingAPI(spec=OpenAIEmbeddingSpec()))
```

Client:

```python
response = client.embeddings.create(
    model="lit",
    input="The food was delicious and the waiter was friendly.",
    encoding_format="float",
)
print(response.data[0].embedding)
```

Client-side list input:

```python
response = client.embeddings.create(
    model="lit",
    input=["first sentence", "second sentence"],
    encoding_format="float",
)
assert len(response.data) == 2
```

## 9. Choose embedding batching mode

Choose one batching mode per endpoint:

| Desired behavior | LitServe setup | Client input |
| --- | --- | --- |
| One response with many vectors from one request | `max_batch_size=1` | `input=["a", "b"]` |
| Server batches many concurrent requests | `max_batch_size>1` | each request sends a single input |

Do not send `input=["a", "b"]` to an embedding API that also has
`max_batch_size>1`; LitServe returns HTTP 400 because client-side batching and
server dynamic batching are mutually exclusive for `OpenAIEmbeddingSpec`.

## 10. Use a custom API path only for raw HTTP

The OpenAI SDK constructs paths from `base_url="http://host:port/v1"` and the
API resource name. It is compatible with the defaults:

- `/v1/chat/completions`
- `/v1/embeddings`

If you set `api_path="/v2/chat/completions"` or `api_path="/v2/embeddings"`,
LitServe can register the route, but use a direct HTTP client:

```python
import requests

requests.post(
    "http://127.0.0.1:8000/v2/chat/completions",
    json={"model": "lit", "messages": [{"role": "user", "content": "hello"}]},
)
```
