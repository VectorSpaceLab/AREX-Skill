# API Reference: Tools and Tool Attachment

This reference summarizes the CAMEL APIs most often needed to attach callable tools to agents and services. It is based on CAMEL-AI package version `0.2.91a4` plus package modules, documentation, examples, and tests inspected during skill generation.

## Core Concepts

| Need | CAMEL surface | Notes |
| --- | --- | --- |
| Wrap one Python callable | `camel.toolkits.FunctionTool(func, openai_tool_schema=None, synthesize_schema=False, synthesize_output=False, ...)` | Parses signature and docstring into OpenAI-compatible tool schema unless an explicit schema is supplied. |
| Decorate a function as a tool | `from camel.toolkits import tool` then `@tool()` | Used in toolkit examples; produces a callable accepted by `ChatAgent(tools=[...])`. |
| Group related tools | subclass `camel.toolkits.base.BaseToolkit` and implement `get_tools()` | `BaseToolkit(timeout=...)` validates positive timeout and auto-wraps most callable subclass methods with timeout handling. |
| Attach tools to an agent | `ChatAgent(..., tools=[FunctionTool(...), *toolkit.get_tools()])` | `tools` expects `FunctionTool`-compatible objects or decorated tools. |
| Pass provider-native tool schemas | `ChatAgent(..., external_tools=[...])` | Shape must match the model/provider tool schema, usually OpenAI tool objects. CAMEL service support is limited; prefer `tools` when calling Python functions. |
| Register an agent in a toolkit | `RegisteredAgentToolkit` | Toolkits needing the current `ChatAgent` implement `register_agent`; pass them through the agent registration path rather than calling detached methods. |

The verified installed `ChatAgent` constructor includes `tools=None`, `external_tools=None`, `tool_execution_timeout=None`, `mask_tool_output=False`, `retry_attempts=3`, `retry_delay=1.0`, and `step_timeout=None`. Keep provider setup separate from this sub-skill.

## FunctionTool Schema Workflow

1. Define a small Python function with precise type hints for every argument and a docstring with `Args:` descriptions.
2. Wrap it with `FunctionTool(func)` or decorate it with `@tool()`.
3. Inspect `get_function_name()`, `get_function_description()`, `get_openai_function_schema()`, and `get_openai_tool_schema()` before connecting it to an agent.
4. If auto-parsing produces the wrong schema, pass `openai_tool_schema={...}` or mutate fields with `set_function_description()`, `set_parameter_description()`, or `set_parameter()`.
5. Call `FunctionTool.validate_openai_tool_schema(schema)` during tests to catch malformed JSON Schema before a model request.

`FunctionTool` coerces dictionaries into Pydantic model arguments when the wrapped function expects a Pydantic type. This is useful for nested arguments, but the generated schema still depends on clean type annotations and parameter descriptions.

## FunctionTool Example

```python
from pydantic import BaseModel, Field
from camel.toolkits import FunctionTool

class Address(BaseModel):
    city: str = Field(description="Destination city")
    country: str = Field(description="ISO country or common country name")

def plan_trip(address: Address, nights: int = 2) -> dict:
    """Plan a short trip.

    Args:
        address: Destination address.
        nights: Number of nights to stay.
    """
    return {"destination": address.model_dump(), "nights": nights}

tool = FunctionTool(plan_trip)
schema = tool.get_openai_tool_schema()
```

For a local, side-effect-free inspection helper, use `scripts/inspect_tool_schema.py`.

## Toolkit Subclass Pattern

```python
from typing import List
from camel.toolkits import FunctionTool
from camel.toolkits.base import BaseToolkit

class FinanceToolkit(BaseToolkit):
    def lookup_ticker(self, symbol: str) -> str:
        """Look up a stock ticker.

        Args:
            symbol: Ticker symbol such as AAPL.
        """
        return symbol.upper()

    def get_tools(self) -> List[FunctionTool]:
        return [FunctionTool(self.lookup_ticker)]
```

Use `@manual_timeout` from `camel.toolkits.base` when a method handles timeout internally and should not receive the automatic timeout wrapper. If a toolkit method already has a `timeout` parameter, `BaseToolkit` skips automatic wrapping.

## Attaching Tools to ChatAgent

```python
from camel.agents import ChatAgent
from camel.toolkits import FunctionTool, MathToolkit

agent = ChatAgent(
    system_message="Use tools when arithmetic is requested.",
    tools=[FunctionTool(my_function), *MathToolkit().get_tools()],
    tool_execution_timeout=30,
    max_iteration=3,
)
response = agent.step("Use the available tool to solve 17 * 23.")
```

Use `max_iteration` to bound repeated tool-calling loops. Use `tool_execution_timeout` for per-tool safety. Use `mask_tool_output=True` when raw tool results contain sensitive text that should not be echoed directly.

## External Tools Shape

`external_tools` is for provider-native tool declarations rather than local Python execution. A typical OpenAI-style object is:

```python
external_tools = [
    {
        "type": "function",
        "function": {
            "name": "lookup_order",
            "description": "Look up an order by id.",
            "parameters": {
                "type": "object",
                "properties": {"order_id": {"type": "string", "description": "Order id"}},
                "required": ["order_id"],
            },
        },
    }
]
```

Prefer `tools=[FunctionTool(...)]` for local Python callables because CAMEL can execute them and report tool results. Use `external_tools` only when the selected model backend expects to handle tool calls externally or a service endpoint accepts native tool schemas.

## AgentOpenAPI Service Inputs

`camel.services.agent_openapi_server.ChatAgentOpenAPIServer` exposes REST endpoints for managing agents. Its `InitRequest` accepts:

- `agent_id` as a required stable identifier.
- `model_type` and `model_platform` for model creation.
- `tools_names` to load tools from the server's `tool_registry` mapping.
- `external_tools` as optional provider-native tool dictionaries; source comments state this is not fully supported in the service path.
- `system_message`, `message_window_size`, `token_limit`, `output_language`, and `max_iteration`.

When building a service, register Python tools on the server side with `tool_registry={"math": MathToolkit().get_tools()}` and initialize agents with `tools_names=["math"]` instead of shipping arbitrary Python over the API.

## Evidence Basis

This reference distills the package documentation, source implementation, function-tool examples, and native tests for tool schema behavior. The generated guidance is self-contained and does not require the original repository checkout at runtime.
