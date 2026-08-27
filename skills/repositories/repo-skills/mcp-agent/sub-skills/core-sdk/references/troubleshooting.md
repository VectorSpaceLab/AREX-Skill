# Core SDK Troubleshooting

Use this when a local `mcp-agent` app fails before, during, or immediately after core SDK setup. Keep diagnosis focused: separate import/package problems, settings/secrets problems, MCP server-name problems, async lifecycle mistakes, decorator schema failures, and request-parameter misuse.

## Quick Triage

1. Run `scripts/check_core_sdk.py` with no provider. If this fails, fix the installed package or local SDK usage before checking credentials.
2. Run `scripts/check_core_sdk.py --provider <name>` only to verify provider wrapper import and settings shape. It does not call the network.
3. If provider wrapper import succeeds but generation fails, inspect provider settings and secrets.
4. If app/agent construction succeeds but tools are missing, inspect `settings.mcp.servers`, `Agent.server_names`, local function annotations, and `RequestParams.tool_filter`.
5. If code hangs or raises context errors, inspect async lifecycle: `async with app.run()` and `async with agent:`.

## Install and Import Failures

Symptoms:

- `ModuleNotFoundError: No module named 'mcp_agent'`
- `ImportError` for `openai`, `anthropic`, `google`, `boto3`, `azure`, or `redis`
- Provider wrapper import fails before any generation call

Likely causes and fixes:

- The distribution is not installed in the active Python environment. Install or activate the environment that contains `mcp-agent`.
- Optional provider dependency is missing. Install the matching extra/package for the provider wrapper you import.
- Redis token store is configured but the `redis` optional dependency is missing. Either install the dependency or switch `oauth.token_store.backend` to `memory` for local tests.
- You are running a different Python than expected. Print `python -c "import mcp_agent; print(mcp_agent.__file__)"` in the same shell that runs the app.

Do not treat a missing API key as an import failure. Provider wrappers may import successfully even when credentials are absent.

## Missing Provider Package vs Missing API Key

Package problem:

- Fails while importing a provider wrapper or constructing provider-specific client classes.
- Error names a Python package or module.
- Fix by installing the relevant optional dependency.

Key/settings problem:

- Provider wrapper imports successfully.
- `Settings` object has no `api_key`, endpoint, region, or provider-specific credential.
- Error appears during generation, client construction, or authentication.
- Fix by adding secrets/env values, not by changing app code.

Config/secrets separation pattern:

```yaml
# mcp_agent.config.yaml
openai:
  default_model: gpt-4o-mini
```

```yaml
# mcp_agent.secrets.yaml
openai:
  api_key: ${OPENAI_API_KEY}
```

Environment aliases to check:

- `OPENAI_API_KEY` or `OPENAI__API_KEY`.
- `ANTHROPIC_API_KEY` or `ANTHROPIC__API_KEY`.
- `AZURE_OPENAI_API_KEY`, `AZURE_AI_API_KEY`, `AZURE__API_KEY`, and endpoint variants.
- `GOOGLE_API_KEY`, `GEMINI_API_KEY`, or `GOOGLE__API_KEY`.
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`, `AWS_REGION`, and `AWS_PROFILE` for Bedrock-style auth.

## Config and Secrets Merge Problems

Symptoms:

- App uses an unexpected model/provider.
- A value exists in YAML but not in `app.config`.
- A secrets file seems ignored.
- Preload works locally but not in CI.

Checks:

- Confirm file names: `mcp_agent.config.yaml` or `mcp-agent.config.yaml`; `mcp_agent.secrets.yaml` or `mcp-agent.secrets.yaml`.
- If using an explicit config path, secrets are first searched beside that config file.
- Secrets are deep-merged over config, so a secrets value can override a config default.
- `MCP_APP_SETTINGS_PRELOAD` is authoritative and bypasses files/environment when valid.
- If preload is malformed and `MCP_APP_SETTINGS_PRELOAD_STRICT=true`, loading raises. If strict is false, loading falls back and prints a warning.
- Environment variables can override file settings through Pydantic aliases when preload is not active.
- `.env` and `.env.mcp-cloud` are loaded by app environment binding; `.env` wins when both define the same key.

YAML pitfalls:

- Use strings for provider model names that contain punctuation.
- Keep server `args` as a list, not a shell string, for stdio servers.
- `roots.uri` must start with `file://`.
- Empty environment variable names in `Settings.env` are invalid.
- Single-key mappings in `Settings.env` must contain exactly one key-value pair.

## Unknown MCP Server Names

Symptoms:

- Agent initializes but no expected tools are listed.
- Tool calls fail because a server name is unknown.
- `RequestParams.tool_filter` appears to hide all tools.

Checks:

- `Agent(server_names=[...])` entries must match keys under `settings.mcp.servers`, not display descriptions or tool names.
- `allowed_tools` is a server-level allowlist; if it is empty, no tools from that server are exposed.
- `RequestParams.tool_filter` is request-level and can further restrict tools. Exact tool names are required.
- Local functions are not under MCP server names; filter them with the reserved `non_namespaced_tools` key.
- The wildcard `"*"` key only applies to servers without explicit filters.

Example restricted request:

```python
RequestParams(
    tool_filter={
        "filesystem": {"read_file", "list_directory"},
        "non_namespaced_tools": {"add_numbers"},
    }
)
```

## Async Context Misuse

Symptoms:

- `RuntimeError: MCPApp not initialized, please call initialize() first, or use async with app.run().`
- Agent has no context or executor.
- Connections are not cleaned up.
- Token counters or loggers behave inconsistently.

Fix patterns:

```python
app = MCPApp(name="demo", settings=settings)

async def main():
    async with app.run() as running_app:
        agent = Agent(name="assistant", context=running_app.context)
        async with agent:
            ...
```

Avoid:

- Reading `app.context` at import time.
- Creating context-bound agents before app initialization unless you pass context later.
- Calling `asyncio.run()` inside an already-running event loop.
- Forgetting `await` on `agent.initialize()`, `agent.attach_llm(...)`, or LLM generation methods.
- Reusing one initialized app across unrelated event loops.

## Decorator and Local Function Schema Failures

Symptoms:

- Import-time validation errors from `@app.tool` or `@app.async_tool`.
- Local function tools are missing from agent tools.
- Schema generation fails for a callable.

Fixes:

- Add complete type hints to every exposed function parameter and return value.
- Prefer JSON-schema-friendly types: `str`, `int`, `float`, `bool`, `list[...]`, `dict[...]`, Pydantic models, and optional fields.
- Add docstrings or explicit `description` for useful tool descriptions.
- Avoid complex defaults that cannot be serialized.
- Keep sync tools quick; use `@app.async_tool` or offload blocking work for slow operations.
- If a decorated function needs app context, use an `app_ctx` parameter or annotate a parameter with `mcp_agent.core.context.Context`.
- For workflow tasks, the target must be async; wrap sync blocking work with `asyncio.to_thread`.

Bad local function:

```python
def lookup(query):
    return {"query": query}
```

Better local function:

```python
def lookup(query: str) -> dict[str, str]:
    """Return a local lookup result."""
    return {"query": query}
```

## RequestParams Misconfiguration

Symptoms:

- Wrong model is used.
- Tool calls loop too long or stop too early.
- Conversation history unexpectedly affects output.
- Tools are invisible to the model.
- OpenAI reasoning settings are ignored.

Checks:

- `model` overrides model-preference selection for that request.
- `modelPreferences` affects selection only when a model selector/factory path uses it.
- `maxTokens` is camelCase, not `max_tokens`, in `RequestParams`.
- `max_iterations` controls tool-use loop depth; lower it for deterministic tests.
- `use_history=False` isolates the request from prior conversation memory.
- `tool_filter={}` means no tools allowed; `tool_filter=None` means no filtering.
- `reasoning_effort` is OpenAI-specific and ignored by other providers.
- `strict=True` only helps providers that support strict schema enforcement.

Safe smoke-test parameters:

```python
RequestParams(
    model="gpt-4o-mini",
    maxTokens=128,
    temperature=0.0,
    max_iterations=1,
    use_history=False,
    tool_filter={},
)
```

## Human Input and Elicitation Failures

Symptoms:

- Model attempts to ask a human but no tool/callback is available.
- Callback returns an unexpected type.
- App-level callback is ignored for a particular agent.

Checks:

- Pass `human_input_callback` to `MCPApp(...)` when all agents should inherit it.
- Pass `human_input_callback` to `Agent(...)` when one agent needs a custom handler.
- Ensure the callback follows the expected request/response protocol from `mcp_agent.human_input.types`.
- Initialize the agent with app context so it can inherit `context.human_input_handler`.
- Keep UI-specific callbacks at application boundaries rather than inside reusable libraries.

## Programmatic Settings Without Disk Config

For local tests that must not read disk config or credentials:

```python
settings = Settings(
    execution_engine="asyncio",
    mcp=MCPSettings(servers={}),
    logger=LoggerSettings(transports=["console"], level="warning"),
)
app = MCPApp(name="no_disk_config", settings=settings)
```

Add a local function agent with restricted tools and no provider call:

```python
def echo(text: str) -> str:
    """Echo text locally."""
    return text

agent = Agent(name="local", functions=[echo], server_names=[], context=running_app.context)
params = RequestParams(tool_filter={"non_namespaced_tools": {"echo"}}, use_history=False)
```

This is the safest pattern for smoke checks, examples, and tests that should not require provider keys or network access.

## When to Route Elsewhere

- Workflow composition, router/orchestrator/parallel/evaluator pattern selection: `workflow-patterns`.
- App-as-MCP-server exposure, server auth internals, FastMCP transport setup: `mcp-server-integration`.
- CLI/cloud deploy/config builder/hosted operations: `cli-cloud-operations`.
- Temporal worker lifecycle, task queues, durable retries, run/resume operations: `durable-execution`.
- Observability exporters, provider-wrapper instrumentation, token-accounting internals: `observability-integrations`.
