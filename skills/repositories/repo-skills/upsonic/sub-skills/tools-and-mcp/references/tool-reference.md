# Tool Reference

## Verified API shapes

| Surface | Verified behavior |
| --- | --- |
| `tool(...)` | Decorator / decorator factory that attaches `ToolConfig` metadata to a function. |
| `ToolConfig` | Controls confirmation, user input, external execution, result visibility, caching, retries, timeout, docstring parsing, and instruction injection. The HITL flags `requires_confirmation`, `requires_user_input`, and `external_execution` are mutually exclusive. |
| `FunctionTool.from_callable(c, name=None, description=None, config=None)` | Wraps a Python callable as a tool with schema generation. |
| `prepare_command(command)` | Sanitizes MCP commands and rejects shell metacharacters. |
| `MCPHandler` / `MultiMCPHandler` | Handle MCP transports such as stdio, SSE, and streamable HTTP when the optional MCP extra is installed. |
| `Agent.as_mcp(name=None)` | Exposes an Agent as a FastMCP server. |

## Typical tool workflow

```python
from upsonic.tools import tool

@tool(requires_confirmation=True)
def sum_tool(a: float, b: float) -> float:
    return a + b
```

```python
from upsonic.tools import FunctionTool

def greet(name: str) -> str:
    return f'Hello {name}'

wrapped = FunctionTool.from_callable(greet)
```

## What to remember

- Use `ToolConfig` when the tool needs confirmation or user input.
- Use `FunctionTool.from_callable` for ordinary Python functions.
- Use MCP only when the workflow truly needs an external protocol connection.
- Keep command strings simple and trust only MCP servers you control.
