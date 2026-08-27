# Core SDK API Reference

This reference distills the verified core APIs for local `mcp-agent` applications. It is self-contained for future agents; do not depend on the original repository checkout while following it.

## Package and Imports

- Distribution: `mcp-agent` version `0.2.6`.
- Import module: `mcp_agent`.
- Minimum Python version: `>=3.10`.
- Core imports:

```python
from mcp_agent.app import MCPApp
from mcp_agent.agents.agent import Agent
from mcp_agent.agents.agent_spec import AgentSpec
from mcp_agent.config import Settings, MCPSettings, MCPServerSettings, LoggerSettings
from mcp_agent.workflows.llm.augmented_llm import AugmentedLLM, RequestParams
```

Provider wrapper imports are optional and require matching extras/packages for some providers:

```python
from mcp_agent.workflows.llm.augmented_llm_openai import OpenAIAugmentedLLM
from mcp_agent.workflows.llm.augmented_llm_anthropic import AnthropicAugmentedLLM
from mcp_agent.workflows.llm.augmented_llm_azure import AzureAugmentedLLM
from mcp_agent.workflows.llm.augmented_llm_google import GoogleAugmentedLLM
from mcp_agent.workflows.llm.augmented_llm_bedrock import BedrockAugmentedLLM
```

## MCPApp

Verified constructor shape:

```python
MCPApp(
    name="mcp_application",
    description=None,
    settings=None,
    mcp=None,
    human_input_callback=None,
    elicitation_callback=None,
    signal_notification=None,
    upstream_session=None,
    model_selector=None,
    icons=None,
    session_id=None,
)
```

Key behaviors:

- `settings=None` loads discovered settings via `get_settings()`; `settings="path/to/config.yaml"` loads an explicit file; `settings=Settings(...)` uses the supplied object.
- `app.run()` is the preferred lifecycle wrapper. It calls `initialize()`, yields the app, pushes token tracking when enabled, and calls `cleanup()` on exit.
- `app.initialize()` / `app.cleanup()` exist for tests, CLIs, and advanced embedding, but async context managers are less error-prone.
- `app.context` raises `RuntimeError` before initialization; enter `async with app.run()` before reading it.
- Constructor-level callbacks are stored on the runtime context: `human_input_callback`, `elicitation_callback`, `signal_notification`, `upstream_session`, and `model_selector`.
- The app owns task/decorator/signal registries from construction time, so decorators can be applied at module import time before `app.run()`.

Useful initialized properties:

- `app.context`: shared runtime `Context` for agents, workflows, logging, token stores, and configured servers.
- `app.config`: resolved `Settings`.
- `app.logger`: structured logger bound to app/session context.
- `app.server_registry`: configured MCP servers.
- `app.executor` and `app.engine`: active execution backend.
- `app.workflows`: registered workflow classes.
- `app.tasks`: registered workflow task names.
- `app.session_id`: runtime session id.

Minimal deterministic app:

```python
from mcp_agent.app import MCPApp
from mcp_agent.config import Settings, LoggerSettings, MCPSettings

settings = Settings(
    execution_engine="asyncio",
    logger=LoggerSettings(transports=["console"], level="info"),
    mcp=MCPSettings(servers={}),
)
app = MCPApp(name="local_app", settings=settings)

async def main():
    async with app.run() as running_app:
        running_app.logger.info("ready")
        return running_app.config.execution_engine
```

## Agent

Verified constructor fields:

```python
Agent(
    name,
    instruction="You are a helpful agent.",
    server_names=[],
    functions=[],
    context=None,
    connection_persistence=True,
    human_input_callback=None,
    llm=None,
    initialized=False,
)
```

Key behaviors:

- `Agent` defines policy and tool access: name, instruction, MCP server names, local function tools, and optional human-input callback.
- `server_names` must match keys under `settings.mcp.servers`; unknown names fail later during initialization or tool listing.
- `functions` are local callables converted to FastMCP tools at model initialization. Provide type hints and docstrings for reliable schema generation.
- `context` can be explicit or resolved from the current global context during `initialize()`. Passing `running_app.context` is clearer and safer in tests and scripts.
- If `human_input_callback` is omitted, initialization can inherit `context.human_input_handler` from `MCPApp`.
- Use `async with agent:` or `await agent.initialize()` / `await agent.shutdown()` to manage MCP connections and resources.

Local function-agent pattern with no MCP servers:

```python
from mcp_agent.agents.agent import Agent

def add(a: int, b: int) -> int:
    """Add two integers."""
    return a + b

agent = Agent(
    name="calculator",
    instruction="Use only the provided arithmetic function.",
    functions=[add],
    server_names=[],
    context=running_app.context,
)
```

MCP server-backed agent pattern:

```python
agent = Agent(
    name="finder",
    instruction="Use filesystem and fetch tools to answer exactly.",
    server_names=["filesystem", "fetch"],
    context=running_app.context,
)
```

## Attaching AugmentedLLM

`Agent.attach_llm(llm_factory=None, llm=None)` returns an `AugmentedLLM` instance:

- Pass an LLM class/factory such as `OpenAIAugmentedLLM` when you want the SDK to construct it with `agent=self`.
- Pass an existing `llm` instance when you constructed or wrapped one yourself; the agent is assigned onto the instance.
- Passing neither raises `ValueError`.
- If the LLM has no instruction, it inherits the agent instruction.

```python
async with agent:
    llm = await agent.attach_llm(OpenAIAugmentedLLM)
    text = await llm.generate_str("Summarize the configured tools.")
```

`AugmentedLLM` base constructor shape:

```python
AugmentedLLM(
    agent=None,
    server_names=None,
    instruction=None,
    name=None,
    default_request_params=None,
    type_converter=None,
    context=None,
    **kwargs,
)
```

Base behavior:

- Requires either `name` or an `agent` with a name.
- Creates a backing `Agent` when only `name`/`server_names` are supplied.
- Maintains in-memory conversation history by default.
- Exposes async generation methods: `generate`, `generate_str`, `generate_structured`, `generate_stream`, and `generate_str_stream`.
- Provider implementations use configured provider defaults and credentials; creating a provider instance may not contact the network, but generation will.

## RequestParams

Verified fields include MCP Sampling fields plus mcp-agent additions:

```python
RequestParams(
    modelPreferences=None,
    systemPrompt=None,
    includeContext=None,
    temperature=0.7,
    maxTokens=2048,
    stopSequences=None,
    tools=None,
    toolChoice=None,
    model=None,
    use_history=True,
    max_iterations=10,
    parallel_tool_calls=False,
    user=None,
    strict=False,
    tool_filter=None,
    reasoning_effort=None,
)
```

Usage notes:

- `model` overrides model-preference selection for that request.
- `modelPreferences` can express cost/speed/intelligence priorities when using model selection.
- `maxTokens` is camelCase because it mirrors MCP sampling parameters.
- `use_history=False` is useful for isolated one-shot checks; default `True` keeps conversation memory.
- `max_iterations` limits tool-use loops; keep it small for deterministic local smoke tests.
- `parallel_tool_calls=True` allows multiple tool calls per iteration when a provider supports it.
- `tool_filter` restricts visible tools per request. Use server names as keys and exact tool names as values. Reserved keys: `"*"` for wildcard server filtering and `"non_namespaced_tools"` for local function/human-input tools.
- `reasoning_effort` accepts `"none"`, `"low"`, `"medium"`, or `"high"` and is honored only by supported OpenAI reasoning models.
- `strict=True` asks providers that support strict schema enforcement to apply it; unsupported providers may ignore it.

Restricted local-tool call example:

```python
params = RequestParams(
    model="gpt-5.1",
    maxTokens=512,
    temperature=0.2,
    max_iterations=3,
    tool_filter={"non_namespaced_tools": {"add"}},
    use_history=False,
    reasoning_effort="none",
)
```

## Model and Provider Selection

Core approaches:

- Direct wrapper: `await agent.attach_llm(OpenAIAugmentedLLM)` or another provider class.
- Factory helper: `create_llm(agent=agent_or_spec, provider="openai", model="gpt-4o-mini", context=running_app.context)`.
- Request override: pass `RequestParams(model="...")` to a generation method.
- Provider-prefixed model id in factory helpers: `model="anthropic:claude-sonnet-4-20250514"` infers provider `anthropic`.
- Model preferences: pass MCP `ModelPreferences` to factory helpers or `RequestParams` when you want selection by cost/speed/intelligence priorities.

Provider credential separation:

- Put stable provider defaults such as `default_model`, endpoint/base URL, and temperature in config or `Settings`.
- Put API keys and OAuth secrets in secrets files, environment variables, or preload payloads supplied by a secret manager.
- Missing provider package is an import/install problem; missing API key is a settings/secrets problem; network/provider errors occur only when generating or connecting.

## Human Input and Elicitation Hooks

App-level hooks:

- `human_input_callback`: enables a human-input tool through the app context so agents can ask for decisions during generation.
- `elicitation_callback`: handles MCP elicitation responses when a client supports them.
- `signal_notification`: lets the app surface workflow signal waits to a UI or dashboard.

Agent-level hook:

- `Agent(human_input_callback=...)` overrides or supplements the app context for that agent.
- If omitted and the app context has a human-input handler, agent initialization can inherit it.

Human-input callbacks should be async-compatible and return the response type expected by `mcp_agent.human_input.types`. Do not hard-code interactive console callbacks in libraries; pass callbacks from the application layer.

## Core Do and Do Not

Do:

- Pass explicit `Settings` for tests, notebooks, and examples that must not depend on current working directory discovery.
- Enter `async with app.run()` before creating context-bound agents.
- Use `async with agent:` for real MCP server connections.
- Add precise type hints to local function tools.
- Keep `RequestParams` small and explicit for smoke tests.

Do not:

- Read `app.context` before initialization.
- Assume `server_names` are tool names; they are configured MCP server keys.
- Store secrets in reusable examples or skill files.
- Use provider wrapper imports as proof that credentials are valid.
- Treat workflow routing/orchestration patterns as core SDK work; route that to `workflow-patterns`.
