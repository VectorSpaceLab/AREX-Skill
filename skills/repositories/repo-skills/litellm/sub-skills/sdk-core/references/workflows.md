# SDK Workflows

## Convert an OpenAI SDK Call

Original OpenAI-style code usually maps directly to `litellm.completion`:

```python
import litellm

response = litellm.completion(
    model="openai/gpt-4o-mini",
    messages=[{"role": "user", "content": "Summarize this release note."}],
    temperature=0.2,
    max_tokens=300,
)
```

Migration checklist:

- Keep `messages`, `temperature`, `max_tokens`, `tools`, `tool_choice`, and `response_format` in OpenAI format first.
- Prefix `model` with the provider, such as `openai/`, `anthropic/`, `azure/`, `bedrock/`, or the provider-specific prefix documented for the endpoint.
- Preserve provider-specific endpoint settings with per-call `base_url` or `api_base`, `api_version`, `api_key`, and `extra_headers`.
- Use `mock_response` for unit tests and local diagnostics that should not contact a provider.
- If the target model is managed through LiteLLM Router, route to the routing sub-skill instead of embedding Router setup here.

## Azure/OpenAI-Compatible Endpoint

```python
response = litellm.completion(
    model="azure/my-deployment",
    messages=[{"role": "user", "content": "Return one JSON object."}],
    api_key=os.environ["AZURE_API_KEY"],
    api_version="2024-10-21",
    base_url="https://example-resource.openai.azure.com",
    response_format={"type": "json_object"},
)
```

If a provider expects `api_base` rather than `base_url`, use the spelling accepted by that endpoint. When diagnosing endpoint issues, verify the deployment/model name separately from the base URL and API version.

## Streaming With Structured Output

Streaming and structured output are provider-dependent. When both are required, validate the provider path explicitly:

```python
stream = litellm.completion(
    model="openai/gpt-4o-mini",
    messages=[{"role": "user", "content": "Stream JSON lines with status updates."}],
    stream=True,
    stream_options={"include_usage": True},
    response_format={"type": "json_object"},
    timeout=60,
)

parts = []
for chunk in stream:
    if not chunk.choices:
        continue
    delta = chunk.choices[0].delta.content
    if delta:
        parts.append(delta)
text = "".join(parts)
```

Validation tips:

- Iterate chunks; do not index the stream as if it were a final response.
- Accumulate `delta.content`; final `message.content` is not available until you build it yourself.
- `stream_options={"include_usage": True}` may produce usage metadata only on providers that support it.
- Pydantic `response_format` may not be compatible with every streaming provider path; use JSON mode plus post-validation if needed.

## Async SDK Calls

```python
import asyncio
import litellm

async def main() -> None:
    response = await litellm.acompletion(
        model="openai/gpt-4o-mini",
        messages=[{"role": "user", "content": "Give one tip."}],
        timeout=30,
    )
    print(response.choices[0].message.content)

asyncio.run(main())
```

For async streaming:

```python
stream = await litellm.acompletion(
    model="openai/gpt-4o-mini",
    messages=[{"role": "user", "content": "Stream three words."}],
    stream=True,
)
async for chunk in stream:
    if chunk.choices:
        delta = chunk.choices[0].delta.content
        if delta:
            print(delta, end="")
```

Avoid running blocking sync callbacks in event-loop hot paths. Prefer async callback implementations for async-heavy applications.

## Embeddings

```python
response = litellm.embedding(
    model="openai/text-embedding-3-small",
    input=["contract summary", "invoice summary"],
    dimensions=512,
    timeout=30,
)
vectors = [item["embedding"] for item in response.data]
```

Embedding checklist:

- Use a list input for batching when the provider supports it.
- Set `dimensions` only for models that support dimensionality reduction.
- Use `encoding_format="base64"` only when downstream storage expects base64.
- For Azure or custom endpoints, pass `api_base`/`base_url`, `api_version`, and `api_key` explicitly.
- If `caching=True`, configure `litellm.cache` first and ensure backend dependencies are installed.

## Safe Mock Tests

Use `mock_response` for no-network tests:

```python
response = litellm.completion(
    model="openai/gpt-4o-mini",
    messages=[{"role": "user", "content": "This should not call a provider."}],
    mock_response="mocked answer",
)
assert response.choices[0].message.content == "mocked answer"
```

Run the bundled mock check:

```bash
python sub-skills/sdk-core/scripts/sdk_smoke.py --checks mock
```

This is the best first diagnostic for import, response-shape, and callback side effects without spending provider credits.

## Token and Cost Guardrails

```python
messages = [{"role": "user", "content": "Summarize the attached text."}]
num_tokens = litellm.token_counter(model="openai/gpt-4o-mini", messages=messages)
if num_tokens > 6000:
    raise ValueError("Prompt is too large for this workflow")

response = litellm.completion(model="openai/gpt-4o-mini", messages=messages)
cost = litellm.completion_cost(completion_response=response)
```

Use custom pricing or route to provider documentation if `completion_cost` cannot price a custom or newly released model.

## Caching

LiteLLM exposes cache classes through `litellm.caching`, including in-memory, disk, Redis, Redis semantic, S3, GCS, Azure Blob, Qdrant semantic, and dual cache backends. For simple SDK tests:

```python
from litellm.caching import Cache

litellm.cache = Cache(type="local")
response = litellm.completion(
    model="openai/gpt-4o-mini",
    messages=[{"role": "user", "content": "Cache this."}],
    mock_response="cached answer",
    caching=True,
)
```

Operational notes:

- Install optional dependencies for non-core backends, such as disk or Redis caches.
- Scope cache keys carefully when user-specific data is present.
- Clear or isolate `litellm.cache` in tests to avoid cross-test coupling.
- Semantic cache backends may require vector database configuration and model-specific embedding behavior.

## Callbacks and Logging

LiteLLM supports global callback lists and `CustomLogger` subclasses:

```python
from litellm.integrations.custom_logger import CustomLogger

class AuditLogger(CustomLogger):
    async def async_log_success_event(self, kwargs, response_obj, start_time, end_time):
        payload = kwargs.get("standard_logging_object")
        if payload:
            print(payload.get("model"))

litellm.callbacks = [AuditLogger(turn_off_message_logging=True)]
```

Callback checklist:

- Use `litellm.callbacks` for both success and failure callback registration.
- Use `litellm.success_callback` or `litellm.failure_callback` only when you intentionally want one side.
- Use async hook methods for async workloads.
- Set `turn_off_message_logging=True` on custom loggers or the global LiteLLM setting when sensitive message/response payloads should be redacted.
- Reset `litellm.callbacks`, `litellm.success_callback`, `litellm.failure_callback`, `_async_success_callback`, and `_async_failure_callback` in tests that mutate them.

## Optional Live Provider Smoke

Only run a live call when the user explicitly supplies a model and a key-bearing environment variable:

```bash
python sub-skills/sdk-core/scripts/sdk_smoke.py \
  --provider-smoke \
  --model openai/gpt-4o-mini \
  --api-key-env OPENAI_API_KEY
```

The script sends a minimal prompt, uses an explicit timeout, and prints a compact success/failure result. Do not place secrets in command history as literal arguments.
