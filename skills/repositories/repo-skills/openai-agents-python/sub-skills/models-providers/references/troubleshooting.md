# Model Provider Troubleshooting

## Missing API Keys

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| OpenAI client raises before the first model call or reports missing credentials | No `OPENAI_API_KEY` and no explicit default key/client/provider key | Set `OPENAI_API_KEY`, call `set_default_openai_key(...)`, pass `OpenAIProvider(api_key=...)`, or use an `AsyncOpenAI(api_key=...)` client. |
| Model calls use a non-OpenAI provider key but tracing fails with 401 | Tracing still exports to OpenAI using the model key or no OpenAI tracing key | Disable tracing for the run/process or configure a separate tracing export key in the tracing sub-skill. |
| LiteLLM or any-llm reports provider authentication failure | Adapter-specific credential environment variables are missing | Set the upstream adapter/provider variables, such as an OpenRouter key when using OpenRouter routes. |

Do not print raw API keys while debugging. Use the bundled `scripts/inspect_model_provider.py` helper to report whether variables are set without exposing their values.

## Wrong API Path: Responses vs Chat Completions

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| 404/unsupported endpoint from an OpenAI-compatible provider | The SDK defaulted to Responses but the provider only supports Chat Completions | Use `set_default_openai_api("chat_completions")`, `OpenAIProvider(use_responses=False)`, or a direct `OpenAIChatCompletionsModel`. |
| Responses-only tools fail on Chat Completions | Chat Completions cannot represent hosted tool search/deferred-loading Responses surfaces | Stay on `OpenAIResponsesModel` / `OpenAIResponsesWSModel`, or remove/replace the Responses-only tools. |
| `previous_response_id`, `conversation_id`, or reusable `prompt` is ignored or rejected | Chat Completions model path does not support server-managed Responses continuation or reusable prompts | Use Responses, or pass full local history yourself when using Chat Completions. Enable strict feature validation to catch this early. |

## ToolSearchTool and Deferred-Loading Tools Fail

`ToolSearchTool`, `tool_namespace()`, and `@function_tool(defer_loading=True)` are Responses-only surfaces. They require OpenAI Responses conversion, and deferred-loading surfaces must be paired with exactly one reachable `ToolSearchTool()` so the model can discover/load tools.

Use this decision path:

1. If the workflow uses hosted tool search, namespaces, or deferred-loading tools, route to Responses HTTP/SSE or Responses websocket.
2. If the provider only supports Chat Completions, remove those surfaces or replace them with eager top-level function tools.
3. If the error names `ToolSearchTool()` specifically, check that exactly one `ToolSearchTool()` is present and that at least one searchable surface exists.
4. Avoid forcing `tool_choice` to bare deferred-only function names; let the model use `auto` / `required` and the hosted tool-search surface.

## Websocket Keepalive, Timeout, and Message Size

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Disconnects during long reasoning turns | Keepalive pong timeout is too aggressive for the network/model latency | Pass `responses_websocket_options={"ping_timeout": None}` or increase `ping_timeout`. |
| Memory concerns for long-lived websocket processes | Default incoming message size limit is disabled (`max_size=None`) | Set `responses_websocket_options={"max_size": 8 * 1024 * 1024}` or another explicit byte limit. |
| Websocket URL points at HTTP endpoint or loses query params | Wrong `websocket_base_url` or proxy URL shape | Set `websocket_base_url` / `OPENAI_WEBSOCKET_BASE_URL` explicitly; the SDK normalizes HTTP(S) schemes to WS(S) and appends `/responses`. |
| Runtime says `websockets` dependency is missing | Optional runtime dependency is absent | Install `websockets` in the application environment. |
| A streamed websocket run is force-closed at context exit | The stream was not fully drained or closed before leaving `responses_websocket_session()` | Finish consuming `stream_events()` or close the result before exiting the context. |

Prefer HTTP/SSE transport when operational reliability is more important than websocket latency.

## Chat Completions Unsupported Features

Chat Completions has narrower SDK feature coverage than Responses. Watch for:

- Server-managed continuation: `previous_response_id`, `conversation_id`, and `auto_previous_response_id` are Responses features.
- Reusable prompt templates: `prompt` is Responses-only.
- Hosted tools and Responses-specific built-ins: use Responses or remove those tools.
- Non-text-only tool outputs and rich Responses output items: strict validation can raise instead of silently converting/dropping unsupported parts.
- Tool-search/deferred-loading tool surfaces: use Responses with `ToolSearchTool()`.

For migrations, create `OpenAIProvider(use_responses=False, strict_feature_validation=True)` or `OpenAIChatCompletionsModel(..., strict_feature_validation=True)` during testing.

## Namespaced Model IDs Route Incorrectly

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `openai/gpt-4.1` reaches the provider as `gpt-4.1` | Default `MultiProvider` treats `openai/` as a routing alias | Set `openai_prefix_mode="model_id"` when the endpoint expects the literal string. |
| `openrouter/openai/gpt-4.1` raises `Unknown prefix: openrouter` | Unknown prefixes fail fast by default | Set `unknown_prefix_mode="model_id"` to pass literal unknown-prefixed IDs to the OpenAI provider. |
| A custom provider is not selected | Missing or overridden `provider_map` prefix | Add the prefix to `MultiProviderMap`; explicit map entries override built-in fallback behavior. |
| Websocket setup works for bare IDs but not namespaced IDs | The shared websocket session uses default prefix modes | Pass the same `openai_prefix_mode` / `unknown_prefix_mode` to `responses_websocket_session()`. |

## Optional Extras Missing

| Symptom | Missing package | Fix |
| --- | --- | --- |
| Importing LiteLLM model/provider raises `ImportError` | `litellm` extra | Install `pip install 'openai-agents[litellm]'`. |
| Importing any-llm model/provider raises `ImportError` | `any-llm-sdk` extra | Install `pip install 'openai-agents[any-llm]'` and use Python 3.11+ if required by the adapter. |
| Voice import under `agents.voice` fails | `voice` extra | Install `pip install 'openai-agents[voice]'` and route usage to realtime/voice guidance. |
| Websocket runtime import fails | `websockets` package | Install `websockets` or disable Responses websocket transport. |

The no-call inspection helper reports optional adapter availability without importing unavailable adapter modules in a way that performs network calls.

## Reasoning Content Replay and Provider-Specific Thinking

Some Chat Completions-compatible providers emit `reasoning_content`, thinking blocks, or provider-specific reasoning metadata. The SDK converts this into reasoning items and can replay reasoning content for follow-up tool-call messages when the provider requires it.

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Follow-up tool-call request fails because prior reasoning content is missing | Provider requires reasoning content to accompany assistant tool-call messages | Use the provider adapter path that preserves reasoning content, or construct a model with a `should_replay_reasoning_content` hook when supported. |
| Reasoning from one provider is sent to a different provider | Mixed-provider history was replayed without filtering | Keep provider-specific histories separate or use SDK defaults/hooks that avoid replaying incompatible reasoning content. |
| Reasoning IDs cause Responses follow-up 400 errors | A reasoning item ID is replayed without its required paired item | In core runtime, set `RunConfig(reasoning_item_id_policy="omit")` for SDK-generated follow-up input. |
| LiteLLM ignores `Reasoning.summary` | LiteLLM chat-completions path forwards scalar reasoning effort rather than Responses reasoning summaries | Use provider-specific `extra_body` / `extra_args` only when the upstream backend supports it, or switch to a Responses-capable path. |

## Retry Does Not Happen

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Transient model failure is not retried | `ModelSettings.retry` was not configured | Add `ModelRetrySettings` with a policy and `max_retries`. |
| Stateful websocket or `previous_response_id` request is not retried after an ambiguous failure | Replay safety is unknown or provider advice vetoes retry | Include `retry_policies.provider_suggested()` and avoid forcing retries after output has started. |
| Retry-after delay exceeds `backoff.max_delay` | Retry-after is an explicit policy/provider delay | Treat retry-after as authoritative or write a custom policy if your app must cap it. |
| Provider SDK also retries | Underlying provider-managed retry may be active | The SDK disables some provider-managed retries during runner-managed attempts, but validate behavior for custom adapters/providers. |
