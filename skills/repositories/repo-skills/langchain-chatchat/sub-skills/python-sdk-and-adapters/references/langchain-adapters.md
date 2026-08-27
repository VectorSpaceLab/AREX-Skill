# LangChain Adapters

## When to read

Read this when integrating Chatchat with LangChain objects or MCP/tool workflows rather than calling Chatchat HTTP APIs directly.

## Public exports

The inspected `langchain_chatchat` package exports:

```python
from langchain_chatchat import ChatPlatformAI, PlatformToolsRunnable
```

## `ChatPlatformAI`

Installed signature excerpt:

```python
ChatPlatformAI(
    *,
    model='glm-4',
    temperature=0.7,
    model_kwargs=None,
    api_key=None,
    api_base=None,
    proxy=None,
    timeout=None,
    max_retries=1,
    streaming=False,
    max_tokens=None,
    http_client=None,
    ...
)
```

Use it when a LangChain workflow needs a Chatchat-compatible chat model wrapper. Configure `api_base`, model name, credentials, streaming, and retry behavior to match the running Chatchat/provider setup. If the request is purely about HTTP payloads, use the API sub-skill instead.

## `PlatformToolsRunnable`

Installed signature excerpt:

```python
PlatformToolsRunnable(
    *,
    agent_executor,
    agent_type,
    callback,
    intermediate_steps=[],
    history=[],
    mcp_connections=None,
    ...
)
```

This is an advanced runnable wrapper around agent/tool execution state. It expects a LangChain `AgentExecutor`, callback handler, intermediate steps, and optional MCP connection mapping. Do not instantiate it casually for simple chat; first decide whether `/tools`, `/chat/chat/completions`, or the SDK tool client is sufficient.

## MCP prompt behavior

Unit-test evidence covers MCP prompt conversion helpers:

- Text prompt messages with role `assistant` map to `AIMessage`.
- Text prompt messages with role `user` map to `HumanMessage`.
- Embedded resource and image content raise `ValueError` in the tested conversion path.
- `load_mcp_prompt` awaits a session's `get_prompt` and returns LangChain messages.

When handling MCP prompts, validate content type before conversion and surface unsupported image/resource content clearly.

## Integration checklist

1. Verify package import with `python -c "from langchain_chatchat import ChatPlatformAI"`.
2. Confirm Chatchat API/provider base URL and model name through setup/API routes.
3. For streaming LangChain flows, coordinate callback handling with the caller's chain/agent framework.
4. For MCP connections, validate connection profiles and server reachability before blaming adapter classes.
5. If adapter signatures differ from this reference, refresh the repo skill.

## Failure boundaries

- `ChatPlatformAI` cannot make a provider model exist; model/provider errors route to setup.
- `PlatformToolsRunnable` cannot fix tool schemas or disabled tools; tool registry errors route to API/tool checks.
- MCP server failures are external service issues unless the adapter import/signature itself fails.
