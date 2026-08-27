# Model Provider Workflows

These recipes are distilled from the SDK docs, examples, source, and tests. They avoid depending on the original repository checkout.

## Default OpenAI Responses

Use the default provider and string model names for OpenAI-only workflows.

```python
from agents import Agent, ModelSettings, Runner

agent = Agent(
    name="Assistant",
    instructions="Be concise.",
    model="gpt-5.5",
    model_settings=ModelSettings(max_tokens=300, verbosity="low"),
)

result = await Runner.run(agent, "Summarize this request in one paragraph.")
```

To set the fallback model for all agents that omit `model`, set `OPENAI_DEFAULT_MODEL` before the process starts, or pass `RunConfig(model="...")` for one run.

```python
from agents import Agent, RunConfig, Runner

agent = Agent(name="Assistant", instructions="Be concise.")
result = await Runner.run(
    agent,
    "Hello",
    run_config=RunConfig(model="gpt-5.5"),
)
```

For advanced Responses settings, prefer direct `ModelSettings` fields:

```python
from agents import Agent, ModelSettings

agent = Agent(
    name="Researcher",
    model="gpt-5.5",
    model_settings=ModelSettings(
        parallel_tool_calls=False,
        truncation="auto",
        store=True,
        prompt_cache_retention="24h",
        response_include=["web_search_call.action.sources"],
        top_logprobs=5,
        context_management=[{"type": "compaction", "compact_threshold": 200000}],
    ),
)
```

Use `extra_args`, `extra_query`, `extra_body`, and `extra_headers` only for provider-specific or newly released fields that the SDK does not expose directly yet.

## Responses Websocket Transport

Use websocket transport only with OpenAI Responses-compatible endpoints. This is not the Realtime API.

For a process-wide default:

```python
from agents import set_default_openai_responses_transport

set_default_openai_responses_transport("websocket")
```

For one provider/run:

```python
from agents import Agent, OpenAIProvider, RunConfig, Runner

provider = OpenAIProvider(
    use_responses_websocket=True,
    websocket_base_url="wss://proxy.example.test/v1",
    responses_websocket_options={"ping_interval": 20.0, "ping_timeout": 60.0},
)

agent = Agent(name="Assistant", model="gpt-5.5")
result = await Runner.run(
    agent,
    "Hello",
    run_config=RunConfig(model_provider=provider),
)
```

For multi-turn reuse, prefer `responses_websocket_session()` because it creates a shared websocket-capable `MultiProvider` and injects its `RunConfig` into `run()` / `run_streamed()` calls.

```python
from agents import Agent, responses_websocket_session

agent = Agent(name="Assistant", instructions="Be concise.", model="gpt-5.5")

async with responses_websocket_session(
    responses_websocket_options={"ping_interval": 20.0, "ping_timeout": None},
) as ws:
    first = ws.run_streamed(agent, "Say hello.")
    async for _event in first.stream_events():
        pass

    second = ws.run_streamed(
        agent,
        "What did you just say?",
        previous_response_id=first.last_response_id,
    )
    async for _event in second.stream_events():
        pass
```

Drain streamed results before the context exits. Do not pass `run_config` to `ResponsesWebSocketSession.run()` or `.run_streamed()`; the helper owns it.

## OpenAI-Compatible HTTP Endpoint

When a provider implements an OpenAI-compatible API, pick the API path it actually supports.

Global default client:

```python
from openai import AsyncOpenAI
from agents import set_default_openai_client, set_tracing_disabled

set_tracing_disabled(True)
set_default_openai_client(
    AsyncOpenAI(base_url="https://provider.example/v1", api_key="provider-key"),
    use_for_tracing=False,
)
```

Direct Chat Completions model for providers that lack Responses:

```python
from openai import AsyncOpenAI
from agents import Agent, OpenAIChatCompletionsModel

client = AsyncOpenAI(base_url="https://provider.example/v1", api_key="provider-key")
agent = Agent(
    name="Assistant",
    model=OpenAIChatCompletionsModel(model="provider-model", openai_client=client),
)
```

If tracing is enabled but model traffic uses a non-OpenAI key, configure tracing separately or route tracing to the tracing sub-skill.

## OpenAI-Compatible Websocket Endpoint with Literal Namespaced IDs

Some proxies expect literal model IDs such as `openai/gpt-4.1` or `openrouter/openai/gpt-4.1`. Default `MultiProvider` treats `openai/...` as a routing alias and rejects unknown prefixes, so opt into pass-through.

```python
from agents import Agent, MultiProvider, RunConfig, Runner

provider = MultiProvider(
    openai_base_url="https://openrouter.ai/api/v1",
    openai_websocket_base_url="wss://openrouter.ai/api/v1",
    openai_api_key="provider-key",
    openai_use_responses=True,
    openai_use_responses_websocket=True,
    openai_prefix_mode="model_id",
    unknown_prefix_mode="model_id",
    openai_responses_websocket_options={"ping_interval": 20.0, "max_size": 8 * 1024 * 1024},
)

agent = Agent(name="Assistant", model="openai/gpt-4.1")
result = await Runner.run(
    agent,
    "Hello",
    run_config=RunConfig(model_provider=provider),
)
```

The same prefix modes are available on `responses_websocket_session()`:

```python
from agents import Agent, responses_websocket_session

agent = Agent(name="Assistant", model="openrouter/openai/gpt-4.1")

async with responses_websocket_session(
    base_url="https://openrouter.ai/api/v1",
    websocket_base_url="wss://openrouter.ai/api/v1",
    api_key="provider-key",
    openai_prefix_mode="model_id",
    unknown_prefix_mode="model_id",
) as ws:
    result = await ws.run(agent, "Hello")
```

## MultiProvider Prefix Behavior

Use this table when debugging model names:

| Configuration | Input model | Provider | Sent model id |
| --- | --- | --- | --- |
| Default | `gpt-4.1` | OpenAI | `gpt-4.1` |
| Default | `openai/gpt-4.1` | OpenAI | `gpt-4.1` |
| `openai_prefix_mode="model_id"` | `openai/gpt-4.1` | OpenAI | `openai/gpt-4.1` |
| Default | `litellm/openrouter/openai/gpt-5.4-mini` | LiteLLM | `openrouter/openai/gpt-5.4-mini` |
| Default | `any-llm/openrouter/openai/gpt-5.4-mini` | any-llm | `openrouter/openai/gpt-5.4-mini` |
| Default | `openrouter/openai/gpt-4.1` | Error | N/A |
| `unknown_prefix_mode="model_id"` | `openrouter/openai/gpt-4.1` | OpenAI | `openrouter/openai/gpt-4.1` |

Use a `MultiProviderMap` when a prefix should route to a custom provider. Explicit map entries override built-in fallback behavior.

## LiteLLM Adapter

Install the optional extra and use either prefixed names through `MultiProvider`, a run-level provider, or a direct model object.

```bash
pip install 'openai-agents[litellm]'
```

Prefixed model through default `MultiProvider` routing:

```python
from agents import Agent, Runner

agent = Agent(name="Assistant", model="litellm/openrouter/openai/gpt-5.4-mini")
result = await Runner.run(agent, "Hello")
```

Run-level provider:

```python
from agents import Agent, RunConfig, Runner
from agents.extensions.models.litellm_provider import LitellmProvider

agent = Agent(name="Assistant", model="openrouter/openai/gpt-5.4-mini")
result = await Runner.run(
    agent,
    "Hello",
    run_config=RunConfig(model_provider=LitellmProvider()),
)
```

LiteLLM reads provider credentials and advanced options from LiteLLM-defined environment variables. Use `ModelSettings(include_usage=True)` if streamed usage metrics matter and validate structured outputs/tool calls against the exact upstream provider.

## any-llm Adapter

Install the optional extra and use prefixed names, a run-level provider, or a direct model object.

```bash
pip install 'openai-agents[any-llm]'
```

Prefixed model through `MultiProvider`:

```python
from agents import Agent, Runner

agent = Agent(name="Assistant", model="any-llm/openrouter/openai/gpt-5.4-mini")
result = await Runner.run(agent, "Hello")
```

Pin the API shape when you know the upstream backend supports it:

```python
from agents import Agent, RunConfig, Runner
from agents.extensions.models.any_llm_provider import AnyLLMProvider

agent = Agent(name="Assistant", model="openrouter/openai/gpt-5.4-mini")
result = await Runner.run(
    agent,
    "Hello",
    run_config=RunConfig(model_provider=AnyLLMProvider(api="responses")),
)
```

If the chosen any-llm backend does not support Responses, the adapter can use its Chat Completions path. Validate Responses-specific behavior before relying on it.

## Runner-Managed Retry

Retries are opt-in through `ModelSettings(retry=...)`.

```python
from agents import Agent, ModelRetrySettings, ModelSettings, retry_policies

agent = Agent(
    name="Assistant",
    model="gpt-5.5",
    model_settings=ModelSettings(
        retry=ModelRetrySettings(
            max_retries=4,
            backoff={
                "initial_delay": 0.5,
                "max_delay": 5.0,
                "multiplier": 2.0,
                "jitter": True,
            },
            policy=retry_policies.any(
                retry_policies.provider_suggested(),
                retry_policies.retry_after(),
                retry_policies.network_error(),
                retry_policies.http_status([408, 409, 429, 500, 502, 503, 504]),
            ),
        )
    ),
)
```

Provider-suggested advice is the safest base policy because it can include provider retry headers, retry-after delays, explicit vetoes, and replay-safety information. Stateful requests using `previous_response_id` or `conversation_id` are treated conservatively; non-provider predicates alone may not be enough when replay safety is ambiguous.

## Feature Validation and API Shape Migration

When migrating from Responses to Chat Completions, enable strict feature validation so incompatible features fail early:

```python
from agents import Agent, OpenAIProvider, RunConfig, Runner

provider = OpenAIProvider(use_responses=False, strict_feature_validation=True)
agent = Agent(name="Assistant", model="gpt-4.1")
result = await Runner.run(
    agent,
    "Hello",
    run_config=RunConfig(model_provider=provider),
)
```

Use strict validation when testing provider migrations that might accidentally send Responses-only features such as `ToolSearchTool`, deferred-loading tools, reusable prompts, `previous_response_id`, `conversation_id`, non-text tool outputs, hosted tools, or other Responses payloads to Chat Completions.
