---
name: tools-runtimes-and-services
description: "Attach Python functions, CAMEL toolkits, MCP/OpenAPI tools,
  runtime-backed execution, interpreters, and service routes to CAMEL agents
  safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Tools, Runtimes, and Services

Use this sub-skill when a task needs CAMEL agents to call tools, expose tools through services, or execute code in a controlled runtime. It covers `camel.toolkits`, `FunctionTool`, toolkit `get_tools()` patterns, `MCPToolkit`, `OpenAPIToolkit`, `CodeExecutionToolkit`, `TerminalToolkit`, `camel.runtimes`, `camel.interpreters`, CAMEL agent MCP service patterns, and `camel.services.agent_openapi_server`.

Do not use this sub-skill for provider/model credentials or model backend selection; route that to the model/provider sub-skill. Do not use it for retrieval-specific memory/RAG tools beyond high-level routing; route retrieval work to `../memory-rag-and-data/SKILL.md` when available. Do not use it for multi-agent loop design except to show how the agent receives tools.

## Fast Routing

- For custom Python functions and tool schemas, read [references/api-reference.md](references/api-reference.md) and optionally run [scripts/inspect_tool_schema.py](scripts/inspect_tool_schema.py).
- For selecting a built-in toolkit or optional extra, read [references/toolkit-catalog.md](references/toolkit-catalog.md).
- For MCP, OpenAPI, terminal/code execution, runtimes, interpreters, AgentOpenAPI, or service deployment patterns, read [references/runtime-service-patterns.md](references/runtime-service-patterns.md).
- For failures around schemas, `external_tools`, missing extras, API credentials, MCP startup, Docker/browser/runtime availability, sandbox safety, or OpenAPI auth, read [references/troubleshooting.md](references/troubleshooting.md).

## Minimal Patterns

```python
from camel.agents import ChatAgent
from camel.toolkits import FunctionTool, SearchToolkit

def add(a: int, b: int) -> int:
    """Add two integers."""
    return a + b

agent = ChatAgent(tools=[FunctionTool(add), *SearchToolkit().get_tools()])
```

```python
from camel.toolkits import MCPToolkit

async with MCPToolkit(config_dict={"mcpServers": {"demo": {"command": "python", "args": ["server.py"]}}}) as toolkit:
    agent = ChatAgent(tools=toolkit.get_tools())
```

## Safety Defaults

Prefer pure schema inspection before live calls, treat browser/Docker/terminal/runtime tools as side-effecting, and keep secrets in environment variables or service config outside skill content. For code execution, start with `internal_python` or a sandboxed runtime, explicitly decide `require_confirm`, and never enable `unsafe_mode=True` for untrusted model-generated code without an external sandbox and human approval.
