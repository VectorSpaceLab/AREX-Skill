# Workflows

This page turns the provider matrix into practical routing and call patterns.

## 1) Configure aliases once, then call by alias/model

Use `LLMClient` when you need multiple aliases, environment indirection, or
explicit cache control.

```python
from giskard.llm import LLMClient

client = LLMClient()
client.configure(
    "openai-prod",
    provider="openai",
    api_key="os.environ/OPENAI_API_KEY",
)
client.configure(
    "gemini-prod",
    provider="google",
    api_key="os.environ/GEMINI_API_KEY",
)
client.configure(
    "anthropic-relaxed",
    provider="anthropic",
    api_key="os.environ/ANTHROPIC_API_KEY",
    merge_system=True,
)

chat = await client.acompletion(
    "openai-prod/gpt-4o",
    [{"role": "user", "content": "Hello"}],
)
```

Key rules:

- Alias names are arbitrary, but later calls must use the alias as the prefix.
- Reconfiguring an alias clears its cached provider instance.
- `reset()` clears the module-level default client and its caches.

## 2) Use the right provider for the model family

- OpenAI-style models and OpenAI-compatible Azure Foundry v1 endpoints:
  `provider="openai"`
- Classic Azure OpenAI deployments that require API versioning:
  `provider="azure"`
- Azure AI Foundry resource endpoints on `*.services.ai.azure.com`:
  `provider="azure_ai"`
- Google Gemini models and Interactions API:
  `provider="google"` or `provider="gemini"`
- Anthropic Claude models: `provider="anthropic"`

Examples:

```python
client.configure(
    "foundry-v1",
    provider="openai",
    api_key="os.environ/AZURE_OPENAI_API_KEY",
    base_url="https://example.openai.azure.com/openai/v1/",
)

client.configure(
    "classic-azure",
    provider="azure",
    api_key="os.environ/AZURE_API_KEY",
    base_url="os.environ/AZURE_API_BASE",
    api_version="2024-10-21",
)

client.configure(
    "azure-foundry",
    provider="azure_ai",
    api_key="os.environ/AZURE_AI_API_KEY",
    base_url="os.environ/AZURE_AI_ENDPOINT",
)
```

## 3) Run chat completions

Use `acompletion(...)` for standard chat-style responses.

```python
messages = [
    {"role": "system", "content": "Be concise."},
    {"role": "user", "content": "Explain retries in one sentence."},
]
response = await client.acompletion("openai-prod/gpt-4o", messages)
print(response.choices[0].message.content)
```

Practical notes:

- OpenAI supports multiple system messages.
- Anthropic requires alternating user/assistant content unless tool turns are
  present, and multiple system/developer messages require `merge_system=True`.
- Google extracts system/developer messages into `system_instruction`.
- Tool calls should use nested `ToolDefParam` inputs; the provider translators
  will flatten them as needed.

## 4) Run embeddings only on embedding-capable providers

```python
embedding = await client.aembedding(
    "openai-prod/text-embedding-3-small",
    ["first text", "second text"],
)
```

Choose OpenAI, Google, or Azure OpenAI for embeddings. Do not route an
embedding request to Anthropic; the provider will raise `UnsupportedOperationError`.

## 5) Use Responses / Interactions when you need tool-result continuation

```python
result = await client.aresponse(
    "openai-prod/gpt-4o",
    "Call the calculator tool if needed.",
    tools=[
        {
            "type": "function",
            "function": {
                "name": "add",
                "description": "Add two numbers",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "a": {"type": "number"},
                        "b": {"type": "number"},
                    },
                    "required": ["a", "b"],
                },
            },
        }
    ],
)
```

For function-result continuation:

```python
await client.aresponse(
    "gemini-prod/gemini-2.0-flash",
    [
        {"type": "message", "role": "user", "content": "Continue with the tool result."},
        {"type": "function_call_output", "call_id": "call_1", "name": "add", "output": "7"},
    ],
)
```

Notes:

- OpenAI Responses and Gemini Interactions use provider-specific flattened wire
  payloads, but the public input stays in Giskard's shared types.
- Google requires the `name` field on function-call outputs when serializing
  tool results.
- The OpenAI provider currently exposes the Responses API through `aresponse(...)`.

## 6) Request structured JSON output

Pass a Pydantic model class when the provider supports structured output.
The provider converts the model to a provider-specific schema request.

```python
from pydantic import BaseModel

class Answer(BaseModel):
    short_answer: str

response = await client.acompletion(
    "openai-prod/gpt-4o",
    [{"role": "user", "content": "Answer in JSON."}],
    response_format=Answer,
)
```

Provider behavior:

- OpenAI: model classes are converted to a JSON schema request.
- Anthropic: model classes are converted to `output_config` with JSON schema.
- Google: model classes are converted to `response_schema` and JSON MIME type.

## 7) Retry safely

```python
from giskard.llm import should_retry
from giskard.llm.errors import LLMError

try:
    await client.acompletion("openai-prod/gpt-4o", messages)
except LLMError as err:
    if should_retry(err):
        # retry policy here
        ...
```

Retry only for timeout, rate-limit, and server errors. Do not retry
authentication or malformed-request failures.

## 8) Inspect routing without keys

Run the bundled inspector from the sub-skill root with:

```bash
python scripts/inspect_llm_routing.py
```

You can also invoke the script by absolute path if you are running from another
working directory. The script prints signatures, provider prefixes, SDK
availability, alias routing behavior, response-model facts, and retry
classification. It does not call a live provider.
