# Provider Reference

This reference distills CrewAI 1.14.8a2 LLM behavior into self-contained guidance for future agents. It is based on CrewAI's current LLM docs, installed signatures, native provider implementations, and focused LLM tests.

## Current `LLM` Shape

The installed `LLM` constructor accepts these important fields:

```python
from crewai import LLM

llm = LLM(
    model="openai/gpt-4o-mini",
    provider="openai",          # optional; usually inferred from model prefix
    api_key=None,               # prefer env vars over literals
    base_url=None,              # OpenAI-compatible/custom endpoint
    api_base=None,              # legacy alias used by some configs
    api_version=None,           # especially Azure
    temperature=0.2,
    top_p=None,
    max_tokens=None,
    max_completion_tokens=None,
    timeout=60,
    stream=False,
    stop=[],
    response_format=None,       # dict or Pydantic model class depending provider
    reasoning_effort=None,
    context_window_size=0,
)
```

Other provider-specific keyword arguments are accepted through provider subclasses or collected as `additional_params`. For agent/crew attachment points such as `Agent(llm=...)`, `Crew(manager_llm=...)`, `Crew(planning_llm=...)`, and `function_calling_llm`, use the core runtime sub-skill because this reference focuses on provider configuration.

## Provider Dispatch Rules

CrewAI's public `LLM` class is a factory:

1. If `provider="..."` is supplied, CrewAI treats that provider as explicit and attempts the matching native provider.
2. If `model` contains `/`, the prefix is inspected. Recognized native prefixes include `openai`, `anthropic`, `claude`, `azure`, `azure_openai`, `google`, `gemini`, `bedrock`, `aws`, `snowflake`, and OpenAI-compatible provider prefixes such as `openrouter`, `deepseek`, `ollama`, `ollama_chat`, `hosted_vllm`, `cerebras`, and `dashscope`.
3. If `model` has no prefix, CrewAI infers from known model lists and naming patterns. Unknown unprefixed models default toward OpenAI.
4. If a prefixed provider is not handled as native/OpenAI-compatible, CrewAI falls back to LiteLLM. If LiteLLM is not installed, initialization raises an import error with guidance to install `crewai[litellm]` or choose a native provider.

Practical rule: use `provider/model` prefixes for clarity, especially in YAML/JSONC projects and migrations.

## Native and OpenAI-Compatible Providers

| Provider intent | Model form | Required credentials | Endpoint/base URL notes | Install/runtime notes |
| --- | --- | --- | --- | --- |
| OpenAI native | `openai/gpt-4o`, `openai/gpt-4o-mini`, `gpt-4o-mini` | `OPENAI_API_KEY` or `api_key` | `base_url`, `api_base`, or `OPENAI_BASE_URL`; explicit `base_url` wins | Native OpenAI SDK. Supports Chat Completions and `api="responses"` for OpenAI Responses API options. |
| Anthropic native | `anthropic/claude-sonnet-4-20250514`, `claude-...` | `ANTHROPIC_API_KEY` or `api_key` | Usually no custom base URL needed | Native Anthropic SDK. Supports tool use and streaming. Structured output support depends on Claude model family. |
| Google Gemini native | `gemini/gemini-2.0-flash`, `google/gemini-...` | `GOOGLE_API_KEY` or `GEMINI_API_KEY`; Vertex can use project/ADC | `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION`, `GOOGLE_GENAI_USE_VERTEXAI=true` for Vertex paths | Native Google Gen AI SDK. Gemini 1.5+ patterns support tools; 2.5+ may auto-enable thinking config. |
| Azure native | `azure/<deployment-or-model>` | `AZURE_API_KEY` or Azure identity | `AZURE_ENDPOINT`, `AZURE_OPENAI_ENDPOINT`, `AZURE_API_BASE`; `AZURE_API_VERSION` defaults to `2024-06-01` | Native Azure AI Inference provider. Azure OpenAI Responses API delegates to OpenAI-compatible Responses handling. |
| AWS Bedrock native | `bedrock/anthropic.claude-...`, `aws/...` | Standard AWS credential chain, commonly `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, optional `AWS_SESSION_TOKEN` | Region from `aws_region_name`, `AWS_DEFAULT_REGION`, or `AWS_REGION_NAME` | Native Bedrock Converse API. Provider-specific `additionalModelRequestFields` may be needed for model-specific options. |
| Snowflake Cortex native | `snowflake/<model>` | `SNOWFLAKE_PAT`, `SNOWFLAKE_TOKEN`, `SNOWFLAKE_JWT`, or `api_key` | `SNOWFLAKE_ACCOUNT_URL`, `SNOWFLAKE_ACCOUNT`, `SNOWFLAKE_ACCOUNT_ID`, `SNOWFLAKE_ACCOUNT_IDENTIFIER`; CrewAI appends `/api/v2/cortex/v1` | Reuses OpenAI transport against Snowflake Cortex REST; supports Chat Completions only. |
| OpenRouter | `openrouter/<vendor>/<model>` | `OPENROUTER_API_KEY` | `OPENROUTER_BASE_URL` optional; default `https://openrouter.ai/api/v1` | OpenAI-compatible native path. Adds default referer header. |
| DeepSeek | `deepseek/deepseek-chat` | `DEEPSEEK_API_KEY` | `DEEPSEEK_BASE_URL` optional; default `https://api.deepseek.com/v1` | OpenAI-compatible native path. |
| Ollama local | `ollama/llama3`, `ollama_chat/llama3` | No real hosted key required; default key is `ollama` | `OLLAMA_HOST` optional; normalized to include `/v1`; default `http://localhost:11434/v1` | OpenAI-compatible native path for local servers. Requires local service if actually called. |
| Hosted vLLM | `hosted_vllm/<model>` | No real hosted key required by default; default key is `dummy` | `VLLM_BASE_URL` optional; default `http://localhost:8000/v1` | OpenAI-compatible native path for self-hosted vLLM. |
| Cerebras | `cerebras/<model>` | `CEREBRAS_API_KEY` | `CEREBRAS_BASE_URL` optional; default `https://api.cerebras.ai/v1` | OpenAI-compatible native path. |
| Dashscope/Qwen | `dashscope/qwen-turbo` | `DASHSCOPE_API_KEY` | `DASHSCOPE_BASE_URL` optional; default compatible-mode endpoint | OpenAI-compatible native path; model names should normally start with `qwen`. |

## Environment and Fallback Defaults

When a caller supplies `llm=None`, CrewAI attempts environment-driven LLM creation. Model selection checks `MODEL`, then `MODEL_NAME`, then `OPENAI_MODEL_NAME`, then CrewAI's default model. Base URL selection checks `BASE_URL`, then `OPENAI_API_BASE`, then `OPENAI_BASE_URL`; `API_BASE` and `AZURE_API_BASE` can also populate API-base behavior.

Use explicit `LLM(...)` objects when you need reliable reviewable behavior. Environment defaults are convenient but can hide unintended provider changes, especially when `MODEL` is set globally.

## Provider Examples

### OpenAI Native

```python
from crewai import LLM

llm = LLM(
    model="openai/gpt-4o-mini",
    temperature=0.2,
    max_tokens=1200,
    timeout=60,
)
```

Set `OPENAI_API_KEY` in the runtime environment. For a custom OpenAI-compatible endpoint that should still route through OpenAI native transport, include a custom `base_url`:

```python
llm = LLM(
    model="openai/local-model-name",
    base_url="http://localhost:8000/v1",
    api_key="dummy",  # placeholder required by many OpenAI-compatible servers
)
```

### Azure

```python
llm = LLM(
    model="azure/my-deployment-name",
    api_key="${AZURE_API_KEY}",
    base_url="https://my-resource.openai.azure.com",
    api_version="2024-06-01",
)
```

In real code, prefer `AZURE_API_KEY`, `AZURE_ENDPOINT`/`AZURE_OPENAI_ENDPOINT`, and `AZURE_API_VERSION` environment variables instead of literal values. Use deployment names exactly as configured in Azure.

### Anthropic

```python
llm = LLM(
    model="anthropic/claude-sonnet-4-20250514",
    temperature=0.1,
    max_tokens=2048,
)
```

Set `ANTHROPIC_API_KEY`. Anthropic-specific features such as thinking, tool search, and native structured output have model-family requirements; keep fallbacks ready when using older Claude models.

### Gemini / Vertex

```python
llm = LLM(
    model="gemini/gemini-2.0-flash",
    temperature=0.2,
)
```

Use `GOOGLE_API_KEY` or `GEMINI_API_KEY` for Gemini API. For Vertex-style routing, configure `GOOGLE_CLOUD_PROJECT`, optional `GOOGLE_CLOUD_LOCATION`, and `GOOGLE_GENAI_USE_VERTEXAI=true`; do not mix API-key assumptions with ADC-only deployment assumptions without checking provider docs.

### Bedrock

```python
llm = LLM(
    model="bedrock/anthropic.claude-3-5-sonnet-20241022-v2:0",
    aws_region_name="us-east-1",
    max_tokens=2048,
)
```

Use standard AWS credentials and region. Bedrock supports multiple model families behind one Converse API, so feature support varies by model.

### Snowflake Cortex

```python
llm = LLM(
    model="snowflake/claude-3-5-sonnet",
    account_identifier="org-account",
    api_key="${SNOWFLAKE_PAT}",
)
```

CrewAI normalizes account identifiers or account URLs to the Cortex API root. Do not pass a URL already ending in `/chat/completions`; pass the account URL or Cortex root.

### Local Ollama Without LiteLLM

```python
llm = LLM(
    model="ollama/llama3.2",
    base_url="http://localhost:11434/v1",
)
```

CrewAI's OpenAI-compatible Ollama provider supplies a placeholder key if none is set. If using the OpenAI prefix against Ollama instead, use `model="openai/llama3.2"`, `base_url="http://localhost:11434/v1"`, and a placeholder `api_key`.

## LiteLLM Migration Notes

CrewAI supports native provider integrations for the main hosted providers and several OpenAI-compatible providers. LiteLLM is still a fallback for additional providers, but it is lazy-loaded and only required when a model string does not route to a native implementation.

Common migrations:

| Before | Preferred migration |
| --- | --- |
| `ollama/llama3` through LiteLLM assumptions | Use CrewAI's native `ollama/llama3` OpenAI-compatible provider, or `openai/llama3` with `base_url="http://localhost:11434/v1"`. |
| `groq/...`, `together_ai/...`, `mistral/...` without LiteLLM installed | Either install `crewai[litellm]` intentionally or switch to a native provider/model supported by CrewAI. |
| Generic custom server with `OPENAI_API_BASE` only | Prefer explicit `LLM(model="openai/<served-model>", base_url=".../v1", api_key="dummy")`. |
| Azure deployment treated like OpenAI base URL | Use `model="azure/<deployment>"`, Azure endpoint env vars, and `api_version`. |

## Context Windows, Rate Limits, and Token Caps

- CrewAI tracks known context windows for many OpenAI, Gemini, Bedrock, and open-source model names. Unknown custom models fall back to a conservative default unless the provider overrides `get_context_window_size()`.
- `context_window_size` can be passed when you know a local/custom model's limit, but it does not make the provider support a larger context than its server actually accepts.
- `max_tokens` limits generated output for most providers. Newer OpenAI/Azure reasoning models may use `max_completion_tokens` instead.
- Agent- and crew-level `max_rpm` are core runtime throttling knobs that help avoid provider rate-limit failures; route detailed placement to the core runtime sub-skill.
- Set `timeout` and provider retry options deliberately for long-running or slow local models.

## Reference Notes

Source docs and tests were used as evidence only. Future agents should not need the original repository checkout to use this runtime skill. Provider details above are bundled here because original docs, tests, and source paths are not runtime dependencies.
