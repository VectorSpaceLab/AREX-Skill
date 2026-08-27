# Provider Reference

This reference summarizes the model/provider surface for `openai-agents` 0.17.6. It is self-contained and intentionally avoids requiring the source checkout.

## Default OpenAI Model Path

| Surface | Use | Key facts |
| --- | --- | --- |
| `Agent(model="...")` | Per-agent model selection | A string model name is resolved by the active `ModelProvider`. With the default provider this uses OpenAI Responses unless the global/default provider is switched to Chat Completions. |
| `RunConfig(model="...")` | Per-run fallback model | Applies when an agent does not set a model. |
| `OPENAI_DEFAULT_MODEL` | Process-wide default model | Used when neither the agent nor run config supplies a model. The current code default is `gpt-5.4-mini`. |
| `ModelSettings` | Per-agent or run-level request settings | Agent settings are resolved with run-level settings; non-`None` values override, and retry/backoff dictionaries are merged. |
| `OpenAIProvider` | Explicit OpenAI provider | Lazily creates an `AsyncOpenAI` client and reads `OPENAI_BASE_URL` / `OPENAI_WEBSOCKET_BASE_URL` when matching constructor fields are omitted. |

For GPT-5-family default model names, the SDK applies model-specific default settings such as low verbosity and an appropriate reasoning effort unless custom settings override them. Non-GPT-5 model names use generic `ModelSettings()` defaults.

## Model Classes

| Class | API shape | Typical use | Notes |
| --- | --- | --- | --- |
| `OpenAIResponsesModel` | OpenAI Responses over HTTP/SSE | Recommended OpenAI path | Supports Responses-only tools and server-managed continuation features such as `previous_response_id` and `conversation_id`. |
| `OpenAIResponsesWSModel` | OpenAI Responses over websocket | Lower-latency OpenAI Responses transport and shared websocket sessions | Requires websocket-compatible endpoint support and the `websockets` package. It is not the Realtime API. |
| `OpenAIChatCompletionsModel` | Chat Completions | OpenAI-compatible providers that lack Responses support | Does not support Responses-only surfaces; with `strict_feature_validation=True` it raises on several unsupported inputs instead of warning or dropping fields. |
| `LitellmModel` | LiteLLM chat-completions adapter | Adapter-managed provider routing | Requires `openai-agents[litellm]`; upstream provider support controls tools, structured output, usage, and reasoning behavior. |
| `AnyLLMModel` | any-llm Responses or Chat Completions | Any-LLM provider routing and optional native Responses path | Requires `openai-agents[any-llm]`; `any-llm-sdk` currently requires Python 3.11+. |
| Custom `Model` | SDK model interface | Full control over request transport/conversion | Implement `get_response`, `stream_response`, and optional `get_retry_advice` / `close` behavior. |

## Provider Classes

| Provider | Purpose | Important constructor fields |
| --- | --- | --- |
| `OpenAIProvider` | Resolve model names to OpenAI Responses, OpenAI Responses websocket, or Chat Completions model objects. | `api_key`, `base_url`, `websocket_base_url`, `openai_client`, `organization`, `project`, `use_responses`, `use_responses_websocket`, `strict_feature_validation`, `agent_registration`, `responses_websocket_options`, `buffer_streamed_tool_calls`. |
| `MultiProvider` | Prefix-based routing across OpenAI, LiteLLM, any-llm, and explicit provider map entries. | `provider_map`, `openai_*` provider fields, `openai_prefix_mode`, `unknown_prefix_mode`, `openai_agent_registration`, `openai_responses_websocket_options`, `openai_buffer_streamed_tool_calls`. |
| `LitellmProvider` | Route through LiteLLM using model strings. | Uses LiteLLM environment variables; returns `LitellmModel(model_name or get_default_model())`. |
| `AnyLLMProvider` | Route through any-llm using model strings. | `api_key`, `base_url`, `api="responses" | "chat_completions" | None`. |
| Custom `ModelProvider` | Map model names to custom `Model` implementations. | Implement `get_model(model_name)` and close any cached resources in `aclose()` when needed. |

`MultiProvider` default routing is:

| Model name | Default route | Sent model id |
| --- | --- | --- |
| `gpt-4.1` | OpenAI provider | `gpt-4.1` |
| `openai/gpt-4.1` | OpenAI provider alias | `gpt-4.1` |
| `litellm/openrouter/openai/gpt-5.4-mini` | LiteLLM fallback provider | `openrouter/openai/gpt-5.4-mini` |
| `any-llm/openrouter/openai/gpt-5.4-mini` | any-llm fallback provider | `openrouter/openai/gpt-5.4-mini` |
| `openrouter/openai/gpt-4.1` | Error unless opted in | N/A by default; pass-through with `unknown_prefix_mode="model_id"`. |

`provider_map` entries win over built-in prefix behavior, including the `openai` alias.

## ModelSettings Fields

| Field group | Fields | Notes |
| --- | --- | --- |
| Sampling and limits | `temperature`, `top_p`, `frequency_penalty`, `presence_penalty`, `max_tokens` | Provider support varies. |
| Tool control | `tool_choice`, `parallel_tool_calls` | `parallel_tool_calls` is model-side; SDK local function-tool concurrency is configured separately in core runtime. |
| Responses controls | `truncation`, `reasoning`, `verbosity`, `metadata`, `store`, `prompt_cache_retention`, `response_include`, `top_logprobs`, `context_management` | Prefer direct fields instead of duplicating the same key in `extra_args`. |
| Chat Completions controls | `include_usage`, `top_logprobs` | `include_usage` is Chat Completions stream-usage control; official OpenAI Chat Completions defaults stream usage on. |
| Provider passthrough | `extra_query`, `extra_body`, `extra_headers`, `extra_args` | Use for provider-specific or newly released request fields. `extra_headers` merges with the SDK user-agent header and should not contain secrets in logs. |
| Retry | `retry` | `ModelRetrySettings(max_retries, backoff, policy)` is opt-in runner-managed retry logic. |

`ModelSettings.resolve()` overlays non-`None` fields from an override. `extra_args` dictionaries merge. `retry` settings deep-merge so a run-level policy can be paired with an agent-level retry count or backoff override.

## Environment Variables

| Variable | Used by | Notes |
| --- | --- | --- |
| `OPENAI_API_KEY` | Default OpenAI client/model calls and tracing unless separately configured | Set before the first model call; `set_default_openai_key()` is the code alternative. |
| `OPENAI_DEFAULT_MODEL` | Default model resolver | Lowercased by the resolver. |
| `OPENAI_BASE_URL` | Default `OpenAIProvider` HTTP base URL | Useful for OpenAI-compatible endpoints. |
| `OPENAI_WEBSOCKET_BASE_URL` | Default `OpenAIProvider` websocket base URL | Used only for Responses websocket transport. |
| `OPENAI_ORG_ID`, `OPENAI_PROJECT_ID` | OpenAI client/tracing attribution | Constructor `organization` / `project` can also be used for explicit providers. |
| `OPENAI_AGENTS_ENABLE_LITELLM_SERIALIZER_PATCH` | LiteLLM adapter | Set to `true` / `1` to opt into an SDK patch that suppresses a known LiteLLM Pydantic serializer-warning issue. |
| Provider-specific adapter keys | LiteLLM / any-llm | Examples include `OPENROUTER_API_KEY`; exact names are owned by the adapter/upstream provider. |

## Transport Choices

| Choice | How to configure | Best fit | Avoid when |
| --- | --- | --- | --- |
| Responses HTTP/SSE | Default; or `OpenAIProvider(use_responses=True)` | OpenAI models, Responses-only tools, server-managed continuation | Endpoint only supports Chat Completions. |
| Responses websocket | `set_default_openai_responses_transport("websocket")`, `OpenAIProvider(use_responses_websocket=True)`, `MultiProvider(openai_use_responses_websocket=True)`, or `responses_websocket_session()` | Lower-latency Responses runs and multi-turn connection reuse | Endpoint lacks a websocket `/responses` endpoint, reliability is more important than websocket latency, or you are using Chat Completions. |
| Chat Completions | `set_default_openai_api("chat_completions")`, `OpenAIProvider(use_responses=False)`, or direct `OpenAIChatCompletionsModel` | OpenAI-compatible providers without Responses support | Responses-only tools, prompt templates, server-managed continuation, hosted tool search, or deferred-loading tool surfaces are required. |
| Third-party adapter | `litellm/...`, `any-llm/...`, direct adapter model, or adapter provider | Mixed provider coverage and adapter-managed routing | You only need OpenAI models or cannot validate adapter-specific capability gaps. |

`OpenAIResponsesWebSocketOptions` supports `ping_interval`, `ping_timeout`, and `max_size`. The SDK defaults `max_size` to `None` for no incoming websocket message-size limit.

## Optional Extras

| Capability | Install extra | Import surface |
| --- | --- | --- |
| LiteLLM adapter | `pip install 'openai-agents[litellm]'` | `agents.extensions.models.litellm_model.LitellmModel`, `agents.extensions.models.litellm_provider.LitellmProvider` |
| any-llm adapter | `pip install 'openai-agents[any-llm]'` | `agents.extensions.models.any_llm_model.AnyLLMModel`, `agents.extensions.models.any_llm_provider.AnyLLMProvider` |
| Voice | `pip install 'openai-agents[voice]'` | Route to the realtime/voice sub-skill. |
| Websocket transport dependency | Install `websockets` if absent | Needed by Responses websocket runtime. |
| Sandbox Docker/hosted backends | Optional sandbox extras | Route sandbox-specific setup outside this model-provider sub-skill. |

Base install imports `agents`, model/provider classes, `responses_websocket_session`, realtime classes, and sandbox base classes; adapter packages may still be missing until their optional extras are installed.
