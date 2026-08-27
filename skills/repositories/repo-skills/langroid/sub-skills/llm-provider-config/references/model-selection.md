# Model selection

Langroid model selection is mostly controlled by `OpenAIGPTConfig.chat_model`, plus `api_base` when the endpoint is generic OpenAI-compatible. Select the model string first, then decide whether the config needs provider-specific params, HTTP-client config, or embedding settings.

## Selection decision tree

1. **OpenAI model through OpenAI API**: use a plain OpenAI model name or `OpenAIChatModel` enum; leave `api_base=None`.
2. **Azure OpenAI deployment**: use `AzureConfig`/`AzureGPT`; set `deployment_name`, `api_base`, and `api_version`.
3. **First-class OpenAI-compatible provider prefix**: use `gemini/`, `deepseek/`, `minimax/`, `openrouter/`, `glhf/`, `ollama/`, `vllm/`, `llamacpp/`, `langdb/`, or `portkey/` when it matches the infrastructure.
4. **Generic OpenAI-compatible server**: set `chat_model` to the served model id and `api_base` to the server `/v1` base.
5. **LiteLLM proxy server**: use `litellm-proxy/<model>` with `LiteLLMProxyConfig` or `LITELLM_` environment variables.
6. **LiteLLM adapter library**: use `litellm/<provider>/<model>` only when the local Python runtime has the LiteLLM optional dependency and provider environment variables.

Do not choose a provider form because of agent/task requirements. Agent orchestration is a separate layer.

## Enum and string choices

Use enums for built-in names when available:

```python
import langroid.language_models as lm

openai_cfg = lm.OpenAIGPTConfig(chat_model=lm.OpenAIChatModel.GPT4o)
gemini_cfg = lm.OpenAIGPTConfig(chat_model="gemini/" + lm.GeminiModel.GEMINI_2_FLASH.value)
minimax_cfg = lm.OpenAIGPTConfig(chat_model="minimax/" + lm.MiniMaxModel.MINIMAX_M2_7.value)
```

Plain strings are accepted for all providers and are required for many gateway, local, preview, or third-party model names:

```python
openrouter_cfg = lm.OpenAIGPTConfig(
    chat_model="openrouter/google/gemini-2.5-flash-lite",
)
local_cfg = lm.OpenAIGPTConfig(
    chat_model="Mistral-7B-Instruct-v0.2",
    api_base="http://model-server:8000/v1",
)
```

## Prefix behavior to remember

- `ollama/<model>` strips the prefix and uses the Ollama OpenAI-compatible endpoint.
- `vllm/<model>` strips the prefix, enables structured-output support, and normalizes a bare host/port `api_base` to `http://.../v1`.
- `llamacpp/<host:port>` takes the endpoint from the model string.
- `gemini/<model>` strips the prefix and uses Gemini's OpenAI-compatible base unless `GEMINI_API_BASE` or explicit `api_base` is set.
- `openrouter/<provider>/<model>` strips the prefix and uses the OpenRouter base.
- `langdb/<provider>/<model>` strips the prefix, composes LangDB base/project path, and adds LangDB headers.
- `portkey/<provider>/<model>` parses provider/model, sets Portkey base, and adds Portkey headers.
- `litellm-proxy/<model>` strips the prefix and uses LiteLLM proxy base/key.
- `litellm/<model>` strips only the `litellm/` prefix, then uses the LiteLLM adapter library.

## Direct `api_base` versus prefixed local strings

These are both valid when the server is OpenAI-compatible:

```python
# Generic explicit form.
cfg = lm.OpenAIGPTConfig(
    chat_model="Mistral-7B-Instruct-v0.2",
    api_base="http://localhost:5000/v1",
)

# Shorthand form where the endpoint is encoded in the model string.
cfg = lm.OpenAIGPTConfig(
    chat_model="local/localhost:5000/v1",
)
```

Use the explicit form when the server expects a real model id in the request body. Use `local/` when the endpoint itself is the main selector or when quick switching through command-line model strings is enough.

## OpenRouter-style bases and third-party gateways

Use the built-in prefix when the gateway is exactly supported:

```python
cfg = lm.OpenAIGPTConfig(chat_model="openrouter/anthropic/claude-haiku-4.5")
```

Use explicit `api_base` for other OpenAI-compatible routers or enterprise proxies:

```python
cfg = lm.OpenAIGPTConfig(
    chat_model="provider/model-name",
    api_base="https://gateway.example.com/api/v1",
    headers={"x-routing-tag": "team-a"},
)
```

If the gateway needs structured metadata, retry, cache, or observability headers and Langroid has first-class params for it, prefer `PortkeyParams` or `LangDBParams` over raw headers.

## Hugging Face chat-template formatting

Some local/completion endpoints need a chat-template formatter. Langroid supports formatter suffixes after `//`:

```python
cfg = lm.OpenAIGPTConfig(
    chat_model="local/localhost:8000/v1//mistral-instruct-v0.2",
)
```

Use `//hf` for auto-detection through Hugging Face formatter lookup when the model name is informative:

```python
cfg = lm.OpenAIGPTConfig(chat_model="litellm/ollama/mistral//hf")
```

A formatter can also be specified directly with `formatter="mistral-instruct-v0.2"`. When a formatter is active, Langroid may use the completion endpoint for chat formatting.

## Environment-prefix pitfalls

`OpenAIGPTConfig` reads `OPENAI_`-prefixed variables for all fields, even when the endpoint is not OpenAI. This is powerful but can surprise provider tests.

Common pitfalls:

- `OPENAI_API_BASE` accidentally forcing a non-OpenAI endpoint for a plain config.
- `OPENAI_CHAT_MODEL` overriding an explicit-looking default in code.
- `OPENAI_MAX_OUTPUT_TOKENS`, `OPENAI_TIMEOUT`, or `OPENAI_TEMPERATURE` changing config values during tests.
- `OPENAI_API_BASE` does not apply to `gemini/`; use `GEMINI_API_BASE` or explicit `api_base`.

For multiple provider groups, create a dynamic config class with a custom prefix:

```python
OllamaConfig = lm.OpenAIGPTConfig.create("ollama")
ollama_cfg = OllamaConfig()
```

Then `OLLAMA_CHAT_MODEL`, `OLLAMA_API_BASE`, and related variables can populate that config group.

## Global model override

Langroid settings can globally override the chat model for quick testing. Treat this as a test convenience, not production configuration, because it changes both chat and completion model selection after the config is created.

If deterministic provider selection matters, clear the global override before constructing `OpenAIGPT` and use explicit config fields.

## Context and output-size selection

- Set `chat_context_length` when the provider's actual context is unknown to Langroid or differs from registry defaults.
- Set `max_output_tokens` to bound cost and latency.
- Set `max_output_tokens=None` when you want Langroid to use the model-info maximum.
- Keep `min_output_tokens` lower than the available context after prompt assembly, especially for local models with small context windows.

## When to use a proxy or gateway

Choose a gateway only for a real gateway need:

- centralized credentials or virtual keys;
- provider fallback/routing;
- observability/tracing;
- budget/cost controls;
- provider-specific headers or cache/retry policies;
- enterprise proxy/network policy.

If the endpoint is simply an OpenAI-compatible model server, `api_base` or a first-class provider prefix is simpler and easier to debug.
