# Provider Patterns

## Provider Setup Patterns

Use `ModelFactory.create()` for provider selection. Keep three concepts separate:

| Concept | CAMEL argument | Typical source | Notes |
| --- | --- | --- | --- |
| Provider/backend | `model_platform` | `ModelPlatformType` enum | Chooses backend class. |
| Model name | `model_type` | `ModelType` enum or string | Strings are valid for provider catalog/local names. |
| Request parameters | `model_config_dict` | `ConfigClass(...).as_dict()` | Temperature, max tokens, stream, response format, tool choice, provider extras. |
| Credential | `api_key` or env var | Secret manager/env | Do not commit keys. |
| Endpoint | `url` or provider env var | Provider/local base URL | Usually base URL, not a completions path. |
| Reliability | `timeout`, `max_retries` | Code defaults/user needs | Increase for slow local models; reduce retries in tests. |

Common provider examples:

```python
from camel.configs import ChatGPTConfig, AnthropicConfig, GeminiConfig
from camel.models import ModelFactory
from camel.types import ModelPlatformType, ModelType

openai_model = ModelFactory.create(
    ModelPlatformType.OPENAI,
    ModelType.GPT_4O_MINI,
    model_config_dict=ChatGPTConfig(temperature=0.2).as_dict(),
)

anthropic_model = ModelFactory.create(
    ModelPlatformType.ANTHROPIC,
    ModelType.CLAUDE_HAIKU_4_5,
    model_config_dict=AnthropicConfig(temperature=0.2).as_dict(),
)

gemini_model = ModelFactory.create(
    ModelPlatformType.GEMINI,
    ModelType.GEMINI_2_5_PRO,
    model_config_dict=GeminiConfig(temperature=0.2).as_dict(),
)
```

The exact key environment variable is provider-specific. If `ModelFactory.create()` or the backend constructor raises an API-key error, inspect that backend/config docstring and avoid guessing. Many OpenAI-compatible providers accept direct `api_key=...` and `url=...` overrides.

## OpenAI-Compatible and Local Endpoints

Use `ModelPlatformType.OPENAI_COMPATIBLE_MODEL` when a service exposes OpenAI chat-completions or responses APIs but is not one of CAMEL's dedicated backends.

```python
from camel.configs import ChatGPTConfig
from camel.models import ModelFactory
from camel.types import ModelPlatformType

model = ModelFactory.create(
    model_platform=ModelPlatformType.OPENAI_COMPATIBLE_MODEL,
    model_type="local-model-name",
    url="http://localhost:8000/v1",
    api_key="not-needed-or-runtime-secret",
    model_config_dict=ChatGPTConfig(temperature=0.0).as_dict(),
    timeout=180,
    max_retries=1,
)
```

Migration case: to move existing `ChatAgent` code from OpenAI to a local vLLM endpoint, change only the model construction and keep the `ChatAgent(model=model, ...)` call unchanged.

```python
model = ModelFactory.create(
    ModelPlatformType.OPENAI_COMPATIBLE_MODEL,
    "meta-llama/Llama-3.1-8B-Instruct",
    url="http://localhost:8000/v1",
    api_key="EMPTY",
    model_config_dict={"temperature": 0.1, "max_tokens": 1024},
)
agent = ChatAgent(system_message="You are helpful.", model=model)
```

URL rules:

- Pass the service base URL, commonly ending in `/v1`; do not append `/chat/completions`.
- vLLM's OpenAI-compatible server commonly listens on `http://localhost:8000/v1`.
- Ollama's OpenAI-compatible API commonly uses `http://localhost:11434/v1`, but the dedicated `ModelPlatformType.OLLAMA` backend can infer its own defaults.
- LMStudio's local server commonly exposes an OpenAI-compatible base URL; use `ModelPlatformType.LMSTUDIO` when you want CAMEL's dedicated backend/config class.
- If the service returns 404, the base URL or API mode is usually wrong; if it returns connection refused, the local server is not running.

`OpenAICompatibleModel` also supports `api_mode="chat_completions"` or `api_mode="responses"`, plus custom sync/async clients via `client=` and `async_client=`. Custom clients must implement OpenAI-like `.chat.completions.create()` and, for structured output, `.beta.chat.completions.parse()` as needed.

## Dedicated Local Backends

| Backend | Platform enum | Config class | Typical use | Notes |
| --- | --- | --- | --- | --- |
| Ollama | `ModelPlatformType.OLLAMA` | `OllamaConfig` | Local Ollama model by string name | Structured output requires recent Ollama support. |
| vLLM | `ModelPlatformType.VLLM` | `VLLMConfig` | OpenAI-compatible vLLM server | `extra_body`, `logprobs`, and `top_logprobs` are config fields. |
| LMStudio | `ModelPlatformType.LMSTUDIO` | `LMStudioConfig` | LM Studio local server | Tool/structured support depends on model/server. |
| SGLang | `ModelPlatformType.SGLANG` | `SGLangConfig` | SGLang serving | Provider-specific response-format behavior. |
| LiteLLM | `ModelPlatformType.LITELLM` | `LiteLLMConfig` | Routing through LiteLLM | Stream support is limited in the backend source. |

For local endpoints, validate outside CAMEL first with the provider's health/model-list endpoint, then instantiate CAMEL. Do not use this skill to start background servers; ask the user how they want local services managed.

## ModelManager Provider Mixes

A `ChatAgent` can receive a list of model objects and a scheduling strategy:

```python
agent = ChatAgent(
    system_message="Use model scheduling.",
    model=[fast_local_model, fallback_cloud_model],
    scheduling_strategy="round_robin",
)
```

Use this when comparing providers, doing coarse failover, or balancing cost/latency. Use `always_first` carefully: if the first model raises, `ModelManager` switches to `round_robin` and re-raises the original exception, so callers still need exception handling.

## Credentialed Examples Are Reference-Only

Provider examples under the original repository often call real APIs or require keys. Treat them as design references, not safe verification scripts. The bundled registry script in this sub-skill intentionally does not instantiate providers or call services.

Native examples worth adapting during verification, if credentials/services are intentionally supplied, include OpenAI chat/structured output, Ollama local model, schema converter, and model manager examples.
