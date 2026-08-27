# Model Selection, Providers, Profiles, and Wrappers

Pydantic AI is model-agnostic: `Agent(model=...)` accepts a concrete `Model` instance, a known provider-prefixed model string, or another string that Pydantic AI can infer. The model adapter owns request translation, the provider owns authentication/client/base URL/lifecycle, and the profile records model-family capability facts such as schema quirks, output support, thinking support, and native-tool support.

## Model String Decision Guide

Use `provider:model-name` for ordinary app code and examples. The provider prefix selects the model class/provider/profile stack.

| Prefix | Typical model class | Typical provider | Notes |
| --- | --- | --- | --- |
| `openai:` | `OpenAIChatModel` | `OpenAIProvider` | Chat Completions API. Use `openai-responses:` when native OpenAI Responses tools/output behavior is required. |
| `openai-chat:` | `OpenAIChatModel` | `OpenAIProvider` | Explicit Chat Completions variant. |
| `openai-responses:` | `OpenAIResponsesModel` | `OpenAIProvider` | Required for OpenAI web search, file search, image generation, and other Responses-native features. |
| `anthropic:` | `AnthropicModel` | `AnthropicProvider` | Supports Anthropic-specific thinking, web search, web fetch, code execution, memory, and native MCP server tools. |
| `google:` | `GoogleModel` | `GoogleProvider` | Gemini API using API-key auth. `google-gla:` is deprecated; prefer `google:`. |
| `google-cloud:` | `GoogleModel` | `GoogleCloudProvider` | Google Cloud / Vertex AI auth and project/location routing. `google-vertex:` and `vertexai:` are deprecated aliases. |
| `bedrock:` | `BedrockConverseModel` | `BedrockProvider` | AWS Bedrock model ids often include region/model/version details, such as `us.anthropic...:0`. |
| `groq:` | `GroqModel` | `GroqProvider` | Groq-native SDK and Groq compound/web-search support. |
| `mistral:` | `MistralModel` | `MistralProvider` | Mistral SDK. |
| `cohere:` | `CohereModel` | `CohereProvider` | Cohere SDK. |
| `xai:` | `GrokModel` | `XaiProvider` | Current xAI path with native X search. `grok:` provider exists for compatibility but prefer `xai:` for new code. |
| `openrouter:` | `OpenRouterModel` or OpenAI-compatible path | `OpenRouterProvider` | Useful for hosted models from multiple upstream providers; profile may be inferred from names such as `google/...`. |
| `huggingface:` | `HuggingFaceModel` | `HuggingFaceProvider` | Hugging Face Inference Providers; requires token/provider configuration. |
| `ollama:` | `OpenAIChatModel`-compatible | `OllamaProvider` | Local or Ollama Cloud OpenAI-compatible endpoint. |
| `cerebras:`, `deepseek:`, `fireworks:`, `github:`, `heroku:`, `litellm:`, `moonshotai:`, `nebius:`, `ovhcloud:`, `sambanova:`, `together:`, `vercel:` | Mostly OpenAI-compatible model adapters | Matching provider class | Use when the endpoint is API-compatible but auth/base URL/profile behavior differs. |
| `gateway/<provider>:` or concrete provider with `provider='gateway'` | Provider-dependent | Pydantic AI Gateway | Requires gateway credentials; `gateway/google-vertex` is normalized to the Google Cloud provider path. |

Use `from pydantic_ai.models import known_model_names` and `known_model_names()` for a public, stable list of known model ids. In this checkout the live inspection reported 501 known names, but the exact list changes with releases and provider catalogs.

## When to Instantiate Classes Directly

Use direct model/provider classes when string inference is not enough:

```python
from httpx import AsyncClient
from openai import AsyncOpenAI

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

http_client = AsyncClient(timeout=30)
client = AsyncOpenAI(api_key='...', max_retries=0, http_client=http_client)
model = OpenAIChatModel(
    'gpt-5.2',
    provider=OpenAIProvider(openai_client=client),
    settings={'temperature': 0.2, 'max_tokens': 800},
)
agent = Agent(model)
```

Common reasons:

- custom `api_key`, `base_url`, `api_version`, project/location, or gateway configuration;
- custom SDK client such as `AsyncOpenAI`, `AsyncAnthropic`, or provider-specific clients;
- disabling provider SDK retries before `FallbackModel` so fallback activates immediately;
- custom `ModelProfile` or schema transformer for nonstandard hosted models;
- shared HTTP client lifecycle management, where the caller closes the client.

If the provider creates its own HTTP client, use `async with Agent(...)`, `async with model`, or `async with provider` around long-running async usage so owned HTTP clients close cleanly. If you pass your own `http_client` or SDK client, you own its cleanup.

## Profiles and Settings

Profiles are capability descriptions, not credentials. They capture model-family behavior such as JSON-schema transformations, structured-output support, thinking support, native tools, prompted-output templates, and provider/model quirks. Providers can infer profiles by model name; pass `profile=` only when overriding or supporting a custom endpoint.

`ModelSettings` is a typed dictionary of cross-provider settings. Common fields include:

- generation controls: `max_tokens`, `temperature`, `top_p`, `top_k`, `seed`, `stop_sequences`;
- request controls: `timeout`, `parallel_tool_calls`, `tool_choice`, `extra_headers`, `extra_body`;
- reasoning/priority controls: `thinking`, `service_tier`.

Provider-specific settings subclasses add provider-prefixed fields such as `openai_service_tier`, `anthropic_service_tier`, `bedrock_service_tier`, `google_cloud_service_tier`, and native-tool output toggles. Provider-specific fields take precedence over unified fields where both exist. Unsupported settings are provider/model-dependent; expect ignored fields or provider errors according to the adapter's documented behavior.

## Wrappers

### `FallbackModel`

`FallbackModel(default_model, *fallback_models, fallback_on=(ModelAPIError,))` tries models in order. Each argument can be a model string or a `Model` instance. `fallback_on` accepts exception types, exception handlers, response handlers typed as `ModelResponse -> bool`, or a sequence mixing them.

```python
from pydantic_ai import Agent
from pydantic_ai.exceptions import ModelHTTPError
from pydantic_ai.models.fallback import FallbackModel

model = FallbackModel(
    'openai:gpt-5.2',
    'anthropic:claude-opus-4-6',
    fallback_on=(ModelHTTPError,),
)
agent = Agent(model)
```

Fallback is not a global provider configuration object: configure auth, base URLs, clients, retry counts, and profiles on each wrapped model individually. Provider SDK retries happen before Pydantic AI sees the failure; disable or lower SDK retries on each SDK client when immediate fallback matters.

### `ConcurrencyLimitedModel`

`ConcurrencyLimitedModel(wrapped, limiter)` limits concurrent requests, streaming requests, and token counting for one model. `limiter` can be an integer, `ConcurrencyLimit`, or a shared `ConcurrencyLimiter`.

```python
from pydantic_ai import Agent, ConcurrencyLimitedModel, ConcurrencyLimiter

shared = ConcurrencyLimiter(max_running=8, name='primary-provider')
primary = ConcurrencyLimitedModel('openai:gpt-5.2', limiter=shared)
backup = ConcurrencyLimitedModel('anthropic:claude-opus-4-6', limiter=2)
agent = Agent(FallbackModel(primary, backup))
```

Place the concurrency wrapper around each model whose provider quota you need to protect. If wrapping a `FallbackModel`, the limiter protects the whole sequence; if wrapping each child model, each provider has its own quota behavior.

### `InstrumentedModel`

`InstrumentedModel(wrapped, options=None)` adds OpenTelemetry spans around model requests and streams. Use it when the app already configures Logfire/OpenTelemetry. It does not install or configure observability dependencies by itself.

```python
from pydantic_ai.models.instrumented import InstrumentedModel

model = InstrumentedModel('openai:gpt-5.2')
```

## Testing Models

`TestModel` and `FunctionModel` are deterministic development models, not provider integrations. Use them through `agent-core` guidance for agent tests, tool/schema checks, and no-network smoke tests. They do not prove optional cloud SDKs or credentials are installed.
