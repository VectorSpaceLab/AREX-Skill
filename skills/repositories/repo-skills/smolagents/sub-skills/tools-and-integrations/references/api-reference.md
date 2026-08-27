# Tool API Reference

## Core Classes and Functions

| API | Use | Key details |
| --- | --- | --- |
| `Tool` | Base class for agent-callable capabilities. | Requires `name`, `description`, `inputs`, `output_type`, and `forward`; can optionally define `output_schema` and `setup`. |
| `@tool` | Converts a typed Python function into a `Tool`. | Requires input type hints, a return type hint, and docstring argument descriptions. |
| `validate_tool_arguments(tool, arguments)` | Checks runtime arguments against `tool.inputs`. | Accepts a dict or a single value for one-input tools; checks missing required keys, unknown keys, JSON-schema type compatibility, `nullable`, and integer-to-number coercion. |
| `load_tool(...)` | Loads a Hub Space tool. | Delegates to `Tool.from_hub`; requires `trust_remote_code=True` for remote code. |
| `ToolCollection.from_hub(...)` | Loads every Space in a Hub collection as tools. | Returns a `ToolCollection` with a `.tools` list. |
| `ToolCollection.from_mcp(...)` | Adapts MCP server tools into smolagents tools. | Context manager; supports stdio, `streamable-http`, and legacy `sse`; requires `trust_remote_code=True`. |
| `Tool.from_space(...)` | Wraps a Gradio Space as a tool. | Calls a remote Space through `gradio-client`; caller supplies tool `name` and `description`. |
| `Tool.from_langchain(...)` | Wraps a LangChain tool. | Lowercases the LangChain tool name and maps its args to smolagents inputs. |
| `launch_gradio_demo(tool)` | Builds a local Gradio demo for a tool. | Requires Gradio and only supports standard smolagents input/output types mapped to Gradio components. |

## Tool Subclass Contract

A subclass must be instantiable without missing required attributes:

```python
from smolagents import Tool

class SlugifyTool(Tool):
    name = "slugify"
    description = "Converts a short title into a URL slug."
    inputs = {
        "title": {"type": "string", "description": "Title to convert."},
        "separator": {"type": "string", "description": "Separator to use.", "nullable": True},
    }
    output_type = "string"

    def forward(self, title: str, separator: str | None = "-") -> str:
        return (separator or "-").join(title.lower().split())
```

Required class attributes:

- `name`: string, valid Python identifier, not a reserved keyword; avoid spaces and hyphens.
- `description`: string that tells the model when to call the tool and what it returns.
- `inputs`: dict keyed by argument name; each value needs `type` and `description`; optional keys include `nullable`, `enum`, and schema metadata produced from type hints.
- `output_type`: one of `string`, `boolean`, `integer`, `number`, `image`, `audio`, `array`, `object`, `any`, or `null`.
- `forward`: method whose parameters match `inputs` and whose return value matches `output_type`.

Optional attributes and methods:

- `output_schema`: JSON schema for structured object-like returns; surfaced in prompts and preserved by serialization helpers, but not a runtime validator.
- `setup()`: lazy initialization hook for expensive clients/models; called on first `__call__` when `is_initialized` is false.
- `skip_forward_signature_validation = True`: advanced escape hatch for wrappers whose dynamic signatures cannot be represented normally.

## `@tool` Decorator Contract

Use `@tool` for small, stateless tools:

```python
from typing import Literal
from smolagents import tool

@tool
def convert_temperature(value: float, unit: Literal["c", "f"] = "c") -> float:
    """Convert a temperature to the opposite unit.

    Args:
        value: Numeric temperature value.
        unit: Unit of the provided value, either c or f.
    """
    return value * 9 / 5 + 32 if unit == "c" else (value - 32) * 5 / 9
```

Decorator-derived schema behavior:

- Missing return type hints fail unless the function has no parameters, in which case a `null` return can be inferred.
- Missing `Args:` descriptions fail for arguments.
- Defaults and `Optional`/`| None` parameters are represented with `nullable` in `inputs`.
- `Literal[...]` values become `enum` constraints in `inputs`.
- `list[...]` and `tuple[...]` become `array`; `dict[...]` becomes `object`; `Any` becomes `any`; `None` returns become `null`.
- Extra decorators can work, but the serializer warns because remote executors may not reconstruct them reliably.
- Multiple `@tool` decorators on the same function are invalid.

## Input Schema Rules

Valid `type` values are:

```python
[
    "string", "boolean", "integer", "number", "image", "audio",
    "array", "object", "any", "null",
]
```

A hand-written schema should look like this:

```python
inputs = {
    "query": {"type": "string", "description": "Search query."},
    "limit": {"type": "integer", "description": "Maximum results.", "nullable": True},
    "mode": {"type": "string", "description": "Search mode.", "enum": ["fast", "deep"]},
}
```

Validation checks performed by `Tool` initialization and helpers include:

- Each input spec has a valid type string or list of valid type strings.
- Each input has a string `description`.
- `forward` parameters are present in `inputs` and nullable flags agree with default/optional type hints.
- `validate_tool_arguments` rejects unknown keys, missing non-nullable inputs, wrong primitive JSON-schema types, and `None` for non-nullable fields.

## Serialization and Sharing

`Tool.save(output_dir)`, `Tool.to_dict()`, and `Tool.push_to_hub()` rely on source reconstruction. Design shareable tools so they can be rebuilt:

- Put third-party imports inside methods that use them.
- Avoid required `__init__` parameters; all `__init__` parameters must have literal defaults.
- Avoid non-literal or computed class attributes; use simple strings, dicts, lists, and sets.
- Avoid module-global variables that methods reference unless they are built-ins or class attributes.
- Do not expect wrappers from `from_space`, `from_langchain`, or `from_gradio` to be saved as plain source; those wrappers are intentionally not serializable through `save()`.

Typical Hub flow:

```python
tool.save("dist/my_tool")
# inspect generated files, then publish when ready
tool.push_to_hub("username/my-tool-space", private=True)
```

When loading remote tools, inspect the Space code first and pass `trust_remote_code=True` only for sources you trust.

## Prompt Rendering

Agents render tools differently by agent type:

- `CodeAgent` uses a Python-like signature from `to_code_prompt()`, including argument descriptions and structured output schema notes.
- `ToolCallingAgent` uses a compact tool-calling description from `to_tool_calling_prompt()`, including `inputs` and `output_type`.

Good tool names, concise descriptions, and precise input descriptions are therefore part of model performance, not just API documentation.
