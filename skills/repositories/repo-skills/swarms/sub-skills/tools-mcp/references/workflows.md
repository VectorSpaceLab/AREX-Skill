# Tools and MCP workflows

## 1. Convert a callable into a tool schema

```python
from swarms.tools.base_tool import BaseTool


def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

schema = BaseTool().func_to_dict(add)
```

Use this when you need an OpenAI-style function definition for a plain Python callable.

## 2. Convert a Pydantic model into a tool schema

```python
from pydantic import BaseModel
from swarms.tools.pydantic_to_json import base_model_to_openai_function

class WeatherQuery(BaseModel):
    city: str
    units: str = "celsius"

schema = base_model_to_openai_function(WeatherQuery)
```

Use this when the tool input shape is better expressed as a model than as a free-form function signature.

## 3. Execute a tool by name

`BaseTool` can execute a function after validating the payload shape.

- Register the callable in the function map.
- Pass a JSON payload with the tool name and parameters.
- Inspect the returned value before handing it back to the agent.

## 4. Connect an agent to one MCP server

```python
from swarms import Agent

agent = Agent(
    agent_name="MCP-Agent",
    model_name="gpt-5.4",
    mcp_url="https://example.com/mcp",
    max_loops=1,
)
```

Use this when one remote server already exposes the tools the agent needs.

## 5. Connect an agent to several MCP servers

Use `mcp_urls` or `mcp_configs` when different servers own different tools.

- The manager deduplicates tool names.
- Each tool call is routed back to the server that advertised it.
- This is the right pattern when the agent needs to mix capability domains.

## 6. Local MCP server smoke test

The bundled local server helper lets you prove the client path without any external service.

Suggested sequence:

1. Start the local server helper on a free port.
2. Load its tools with `MCPManager.get_tools()`.
3. Execute the `add` tool once.
4. Repeat with API-key and bearer-token modes if you want to verify auth handling.

## 7. Agent + tool path

The usual end-to-end shape is:

1. Build or convert the tool schema.
2. Attach it to an `Agent` or MCP manager.
3. Load or list tools.
4. Execute a minimal tool call.
5. Verify the returned payload or error object.
