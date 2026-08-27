# Provider configuration

This reference covers direct LLM/provider access in Langroid. It deliberately stops before agent orchestration, task delegation, tools, retrieval, or MCP integration.

## Core objects

Use `langroid.language_models` as the normal import surface:

```python
import langroid.language_models as lm

llm_config = lm.OpenAIGPTConfig(
    chat_model="gpt-4o",
    temperature=0.2,
    timeout=20,
)
llm = lm.OpenAIGPT(llm_config)
```

`OpenAIGPTConfig` is the central config for OpenAI and OpenAI-compatible chat/completion providers. Its installed defaults include:

- `chat_model="gpt-4o"`
- `timeout=20`
- `temperature=0.2`
- `use_cached_client=True`
- `stream=True` from the base LLM config
- `max_output_tokens=8192` unless set to `None` to use the model-info maximum

Important: `OpenAIGPTConfig` is a settings class with `OPENAI_` environment-variable prefix. For example, `OPENAI_API_BASE`, `OPENAI_CHAT_MODEL`, or `OPENAI_MAX_OUTPUT_TOKENS` can override fields in a config instance. Clear or isolate these variables when doing deterministic provider tests.

Create an LLM object only after verifying the config. Avoid calling `chat()`, `achat()`, `generate()`, `agenerate()`, or embedding functions during no-network validation.

## Direct OpenAI

Use either enum values or exact string model names:

```python
llm_config = lm.OpenAIGPTConfig(
    chat_model=lm.OpenAIChatModel.GPT4o,
    max_output_tokens=1000,
)
```

For plain OpenAI models, keep `api_base=None` unless a proxy explicitly replaces the OpenAI endpoint. Set the key in `OPENAI_API_KEY` or pass `api_key` only for short-lived local tests. Prefer environment variables or secret managers over hardcoded keys.

`OpenAICallParams` carries per-request/provider parameters that should be sent to the chat-completion call:

```python
llm_config = lm.OpenAIGPTConfig(
    chat_model="gpt-4o-mini",
    params=lm.OpenAICallParams(
        temperature=0.0,
        max_tokens=500,
        extra_body={"custom": "provider-specific"},
    ),
)
```

Call-time parameters override `OpenAIGPTConfig.params`, which override base config values such as `temperature`.

## Generic OpenAI-compatible endpoints

For any server that exposes the OpenAI chat-completions API, set both the served model name and base URL:

```python
llm_config = lm.OpenAIGPTConfig(
    chat_model="Mistral-7B-Instruct-v0.2",
    api_base="http://model-server:8000/v1",
    api_key="placeholder-if-server-requires-one",
)
```

Use `local/host:port/v1` for the shorthand path:

```python
llm_config = lm.OpenAIGPTConfig(chat_model="local/localhost:8000/v1")
```

When `local/` lacks a scheme, Langroid adds `http://`. The server still must expose OpenAI-compatible `/v1` chat endpoints.

## Local and hosted provider prefixes

The `chat_model` prefix selects provider-specific key and base handling.

| Prefix | Example | Key source | Base handling | Notes |
|---|---|---|---|---|
| none/OpenAI | `gpt-4o` | `OPENAI_API_KEY` | OpenAI default | First-class OpenAI path. |
| `local/` | `local/localhost:8000/v1` | usually placeholder | taken from model string | Generic local OpenAI-compatible server. |
| `ollama/` | `ollama/qwen2.5` | `OLLAMA_API_KEY`, usually `ollama` | `OLLAMA_HOST` or local default | Strips `ollama/` before request. |
| `vllm/` | `vllm/Qwen/Qwen2.5-Coder-7B` | `VLLM_API_KEY` or placeholder | `api_base` or local default, normalized to `/v1` | Structured output is enabled. |
| `llamacpp/` | `llamacpp/localhost:8080` | `LLAMA_API_KEY` or placeholder | host from model string | For llama.cpp server chat access. |
| `groq/` | `groq/llama3-8b-8192` | `GROQ_API_KEY` | Groq SDK client | `api_key_provider` is not supported. |
| `cerebras/` | `cerebras/llama-3.3-70b` | `CEREBRAS_API_KEY` | Cerebras SDK client | `api_key_provider` is not supported. |
| `gemini/` | `gemini/gemini-2.0-flash` | `GEMINI_API_KEY` | Gemini OpenAI-compatible base | Uses `GEMINI_API_BASE` or explicit `api_base`, not `OPENAI_API_BASE`. |
| `deepseek/` | `deepseek/deepseek-reasoner` | `DEEPSEEK_API_KEY` | DeepSeek base | Reasoning models can populate reasoning fields. |
| `minimax/` | `minimax/MiniMax-M2.7` | `MINIMAX_API_KEY` | MiniMax base, unless explicit base is supplied | Direct OpenAI-compatible path. |
| `openrouter/` | `openrouter/google/gemini-2.5-flash-lite` | `OPENROUTER_API_KEY` | OpenRouter base | Use provider/model names expected by OpenRouter. |
| `glhf/` | `glhf/hf:Qwen/Qwen2.5-Coder-32B-Instruct` | `GLHF_API_KEY` | GLHF base | Hosted open-weight models. |
| `langdb/` | `langdb/openai/gpt-4o-mini` | `LANGDB_API_KEY` through `LangDBParams` | LangDB base plus optional project path | Adds tracking headers when configured. |
| `portkey/` | `portkey/openai/gpt-4o-mini` | `PORTKEY_API_KEY` through `PortkeyParams`; provider keys may also be needed | Portkey base plus headers | Supports gateway metadata, cache, retry, virtual keys. |
| `litellm-proxy/` | `litellm-proxy/anthropic/claude-3-haiku` | `LITELLM_API_KEY` or `LiteLLMProxyConfig` | deployed LiteLLM proxy base | Does not use the LiteLLM adapter library in-process. |
| `litellm/` | `litellm/anthropic/claude-3-haiku` | provider-specific environment variables | LiteLLM adapter library | Requires the LiteLLM optional dependency. |

## Azure OpenAI

Use `AzureConfig` and `AzureGPT` for Azure deployments:

```python
azure_config = lm.AzureConfig(
    api_version="2024-08-01-preview",
    deployment_name="my-chat-deployment",
    chat_model="gpt-4o",
)
llm = lm.AzureGPT(azure_config)
```

Relevant environment variables use the `AZURE_OPENAI_` prefix:

- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_API_BASE`
- `AZURE_OPENAI_API_VERSION`
- `AZURE_OPENAI_DEPLOYMENT_NAME`
- `AZURE_OPENAI_CHAT_MODEL`

Azure `deployment_name` is the custom deployment name in the Azure resource. It is not necessarily the underlying model name. The older `model_name` field is mapped to `chat_model` when `chat_model` is omitted, but prefer `chat_model` in new configs.

For Azure Entra ID, provide SDK clients through `azure_openai_client_provider` and `azure_openai_async_client_provider`. Do not use `api_key_provider` for `AzureGPT`; that field is for OpenAI-compatible providers on the `OpenAIGPT` path.

## Gemini and Vertex-style bases

For Google AI Studio Gemini:

```python
llm_config = lm.OpenAIGPTConfig(chat_model="gemini/gemini-2.0-flash")
```

Set `GEMINI_API_KEY`. If neither `GEMINI_API_BASE` nor explicit `api_base` is set, Langroid uses the Gemini OpenAI-compatible endpoint.

For Vertex-style OpenAI-compatible endpoints, set `GEMINI_API_BASE` or pass explicit `api_base`. `OPENAI_API_BASE` is intentionally ignored for `gemini/` models to avoid accidental leakage from local/proxy OpenAI settings.

## LangDB gateway

Use `chat_model="langdb/<provider>/<model>"` with optional tracking fields:

```python
from langroid.language_models.provider_params import LangDBParams

llm_config = lm.OpenAIGPTConfig(
    chat_model="langdb/openai/gpt-4o-mini",
    langdb_params=LangDBParams(
        label="support-bot",
        run_id="run-123",
        thread_id="thread-456",
    ),
)
```

`LangDBParams` uses `LANGDB_` environment variables. API key and project ID can come from `LANGDB_API_KEY` and `LANGDB_PROJECT_ID`. When `project_id`, `label`, `run_id`, or `thread_id` are set, Langroid adds the corresponding tracking headers.

LangDB embeddings use `OpenAIEmbeddingsConfig(model_name="langdb/openai/text-embedding-3-small")`; see [embedding configuration](embedding-config.md).

## Portkey gateway

Use `chat_model="portkey/<provider>/<model>"` with `PortkeyParams` when you need gateway features:

```python
from langroid.language_models.provider_params import PortkeyParams

llm_config = lm.OpenAIGPTConfig(
    chat_model="portkey/openai/gpt-4o-mini",
    portkey_params=PortkeyParams(
        virtual_key="vk-example",
        trace_id="trace-123",
        metadata={"component": "summarizer"},
        retry={"max_retries": 3},
        cache={"enabled": True, "ttl": 3600},
    ),
)
```

`PortkeyParams` uses `PORTKEY_` environment variables and builds headers such as API key, provider, virtual key, trace ID, metadata, retry, cache, user, organization, and custom headers. Provider API keys may still be required by Portkey unless a virtual key handles provider credentials.

## LiteLLM proxy versus LiteLLM adapter

Use `litellm-proxy/` when a LiteLLM proxy server is already deployed:

```python
from langroid.language_models.openai_gpt import LiteLLMProxyConfig

llm_config = lm.OpenAIGPTConfig(
    chat_model="litellm-proxy/anthropic/claude-3-haiku",
    litellm_proxy=LiteLLMProxyConfig(
        api_key="proxy-key",
        api_base="http://litellm-proxy:4000/v1",
    ),
)
```

Use `litellm/` when the current Python process should load the LiteLLM adapter library:

```python
llm_config = lm.OpenAIGPTConfig(
    chat_model="litellm/anthropic/claude-3-haiku",
)
```

Do not mix these forms. The proxy form needs proxy URL/key; the adapter form needs the `litellm` optional dependency and provider-specific environment variables.

## Client caching

`OpenAIGPTConfig(use_cached_client=True)` is the default. Cached clients share HTTP connection pools for identical client configurations and reduce resource exhaustion from many agents or LLM instances. Disable caching only when isolation is required, such as multiprocessing, debugging, or code that depends on distinct client objects:

```python
llm_config = lm.OpenAIGPTConfig(
    chat_model="gpt-4o",
    use_cached_client=False,
)
```

The cache key includes provider/client type, API key or key-provider identity, base URL, organization, timeout, default headers, and HTTP-client config. A factory-supplied HTTP client is not cacheable.

## Rotating API keys and short-lived tokens

Use `api_key_provider` for OpenAI-compatible endpoints that need a fresh bearer token per request:

```python
def token_provider() -> str:
    return current_valid_token()

llm_config = lm.OpenAIGPTConfig(
    chat_model="local/secure-endpoint.example/v1",
    api_key_provider=token_provider,
)
```

The callable takes precedence over `api_key` and environment keys. It is resolved per request by the OpenAI SDK, and the client cache keys on the callable identity instead of token value. The provider must be thread-safe.

Supported with the OpenAI-client path, including plain OpenAI-compatible endpoints and prefixes such as `gemini/`, `litellm-proxy/`, `openrouter/`, `deepseek/`, `vllm/`, and `local/`. It is not supported with `groq/`, `cerebras/`, or the in-process LiteLLM adapter (`litellm/` or `litellm=True`).

For transport-level custom authentication, use `http_client_factory` and return an `httpx.Client` or `(httpx.Client, httpx.AsyncClient)`.

## HTTP client configuration

Use one of three OpenAI-client HTTP options:

1. `http_verify_ssl=False`: quick local/trusted workaround for certificate errors.
2. `http_client_config={...}`: cacheable `httpx` config for proxies, custom CA bundles, timeouts, and headers.
3. `http_client_factory`: custom sync or sync+async clients; most flexible but not cacheable.

Priority order is `http_client_factory`, then `http_client_config`, then `http_verify_ssl`.

Prefer `http_client_config` for stable corporate proxy/CA settings because it keeps client caching active:

```python
llm_config = lm.OpenAIGPTConfig(
    chat_model="gpt-4o",
    http_client_config={
        "verify": "/path/to/ca-bundle.pem",
        "proxy": "http://proxy.example:8080",
        "timeout": 30.0,
    },
)
```

Avoid disabling SSL verification outside trusted development or test environments.

## Reasoning content and streaming

`OpenAICallParams` includes `reasoning_effort` and `extra_body`. Use them only for models/providers that support them:

```python
llm_config = lm.OpenAIGPTConfig(
    chat_model="deepseek/deepseek-reasoner",
    params=lm.OpenAICallParams(
        reasoning_effort="low",
        extra_body={"include_reasoning": True},
    ),
)
```

`LLMResponse.reasoning` carries reasoning text when the provider returns it. Streaming can emit reasoning events separately from text events through `StreamEventType.REASONING`. Some models accept reasoning parameters but do not expose the internal reasoning trace in API responses.
