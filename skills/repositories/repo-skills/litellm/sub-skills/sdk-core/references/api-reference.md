# SDK API Reference

This reference covers direct Python SDK calls in LiteLLM 1.90.0 on Python 3.10 through 3.13.

## Import Surface

```python
import litellm
from litellm import completion, acompletion, embedding, aembedding, text_completion
```

The package also exposes CLI entry points named `litellm`, `lite`, and `litellm-proxy`, but server operation belongs in the proxy-server sub-skill.

## Chat Completion

Primary sync call:

```python
response = litellm.completion(model="openai/gpt-4o-mini", messages=[...])
```

Primary async call:

```python
response = await litellm.acompletion(model="openai/gpt-4o-mini", messages=[...])
```

Important parameters supported by both sync and async chat completion include:

- `model`: Provider/model identifier. Prefer explicit provider prefixes for cross-provider clarity.
- `messages`: OpenAI-format chat messages.
- `timeout`: Float/int seconds or an HTTP timeout object for sync `completion`.
- `temperature`, `top_p`, `n`, `stop`, `presence_penalty`, `frequency_penalty`, `seed`, `user`.
- `stream`: Return a stream wrapper instead of a final response.
- `stream_options`: Commonly used with `{"include_usage": True}` when provider supports usage in stream.
- `max_tokens` and `max_completion_tokens`: Use the parameter expected by the target model family; reasoning models often prefer `max_completion_tokens`.
- `response_format`: A JSON schema/object dict or a Pydantic `BaseModel` subclass when supported.
- `tools`, `tool_choice`, `parallel_tool_calls`: OpenAI-format tool calling controls.
- `base_url`, `api_version`, `api_key`, `extra_headers`: Per-call provider configuration.
- `model_list`: Direct model/deployment list input for compatible flows; use the routing sub-skill for full Router patterns.
- `thinking`: Anthropic-style thinking parameter when supported by the provider.
- `web_search_options`: OpenAI-style web search options when supported.
- `enable_json_schema_validation`: Per-request override for LiteLLM JSON schema validation.
- `mock_response`: LiteLLM-specific safe testing parameter that returns a local mocked response.
- `custom_llm_provider`: Override provider inference when the model string is ambiguous.
- `**kwargs`: Provider-specific or LiteLLM-specific extras.

The response is OpenAI-like. For non-streaming chat, read `response.choices[0].message.content`. For tool calls, inspect `response.choices[0].message.tool_calls`. Usage normally appears at `response.usage` when the provider returns it.

## Streaming

Sync streaming returns an iterable:

```python
stream = litellm.completion(
    model="openai/gpt-4o-mini",
    messages=[{"role": "user", "content": "Stream a haiku."}],
    stream=True,
)
for chunk in stream:
    if chunk.choices:
        delta = chunk.choices[0].delta.content
        if delta:
            print(delta, end="")
```

Async streaming returns an async iterable:

```python
stream = await litellm.acompletion(
    model="openai/gpt-4o-mini",
    messages=[{"role": "user", "content": "Stream a haiku."}],
    stream=True,
)
async for chunk in stream:
    if chunk.choices:
        delta = chunk.choices[0].delta.content
        if delta:
            print(delta, end="")
```

Do not treat streamed chunks as final responses. Chunks usually contain `choices[0].delta`, not `choices[0].message`.

## Embeddings

Sync embeddings:

```python
response = litellm.embedding(
    model="openai/text-embedding-3-small",
    input=["first text", "second text"],
    dimensions=512,
)
embeddings = [item["embedding"] for item in response.data]
```

Async embeddings:

```python
response = await litellm.aembedding(
    model="openai/text-embedding-3-small",
    input="hello world",
)
```

Key parameters are `model`, `input`, `dimensions`, `encoding_format`, `timeout`, `api_base`, `api_version`, `api_key`, `api_type`, `caching`, `user`, `custom_llm_provider`, `litellm_call_id`, `logger_fn`, and `**kwargs`.

Use `caching=True` only after configuring a compatible LiteLLM cache. Some cache backends require optional dependencies or external services.

## Text Completion

Use `litellm.text_completion(...)` for prompt-style completion APIs:

```python
response = litellm.text_completion(
    model="openai/gpt-3.5-turbo-instruct",
    prompt="Write a tagline for a docs site.",
    max_tokens=30,
)
```

Important parameters include `prompt`, `model`, `best_of`, `echo`, `frequency_penalty`, `logit_bias`, `logprobs`, `max_tokens`, `n`, `presence_penalty`, `stop`, `stream`, `stream_options`, `suffix`, `temperature`, `top_p`, `user`, `api_base`, `api_version`, `api_key`, `model_list`, and `custom_llm_provider`.

## Structured Output

For JSON object mode:

```python
response = litellm.completion(
    model="openai/gpt-4o-mini",
    messages=[{"role": "user", "content": "Return JSON with name and score."}],
    response_format={"type": "json_object"},
)
```

For Pydantic response formats, pass a Pydantic v2 `BaseModel` subclass when the target provider path supports it:

```python
from pydantic import BaseModel

class Answer(BaseModel):
    name: str
    score: int

response = litellm.completion(
    model="openai/gpt-4o-mini",
    messages=[{"role": "user", "content": "Return Alice with score 7."}],
    response_format=Answer,
    enable_json_schema_validation=True,
)
```

If a provider rejects schema mode, fall back to a dict `response_format`, provider-native schema parameter, or post-validate the returned text with Pydantic.

## Tool Calling

LiteLLM accepts OpenAI-format `tools` and `tool_choice`:

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "lookup_order",
            "description": "Look up an order by id.",
            "parameters": {
                "type": "object",
                "properties": {"order_id": {"type": "string"}},
                "required": ["order_id"],
            },
        },
    }
]

response = litellm.completion(
    model="openai/gpt-4o-mini",
    messages=[{"role": "user", "content": "Find order A123."}],
    tools=tools,
    tool_choice="auto",
)
```

Check provider support before assuming parallel calls or forced tool choice. Some providers need transformed parameter names or reject unsupported tool options.

## Tokens and Costs

Count tokens before a call:

```python
count = litellm.token_counter(
    model="openai/gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello"}],
)
```

Estimate cost after a call:

```python
cost = litellm.completion_cost(completion_response=response)
```

`completion_cost(...)` can also accept `model`, `prompt`, `messages`, `completion`, `custom_llm_provider`, custom pricing, and service-tier or regional parameters. It raises when pricing is unavailable unless custom pricing is supplied.

## Error Types

Common LiteLLM exceptions mirror OpenAI SDK-style errors. Catch specific classes when the recovery differs:

```python
try:
    response = litellm.completion(model=model, messages=messages, timeout=20)
except litellm.AuthenticationError:
    raise RuntimeError("Check provider API key or auth configuration")
except litellm.Timeout:
    raise RuntimeError("Provider request timed out")
except litellm.RateLimitError:
    raise RuntimeError("Retry later or switch model/provider")
except litellm.BadRequestError as exc:
    raise RuntimeError(f"Provider rejected request parameters: {exc}")
except litellm.APIError as exc:
    raise RuntimeError(f"Provider/API failure: {exc}")
```

Unknown provider/model-prefix failures may surface through bad-request/provider inference errors. Inspect the model string, `custom_llm_provider`, `api_base`, and provider key.

## Safe Signature Check

The bundled script validates installed signatures without network calls:

```bash
python sub-skills/sdk-core/scripts/sdk_smoke.py --checks signature
```

It verifies the presence of parameters used by this reference for `completion`, `acompletion`, and `embedding`.
