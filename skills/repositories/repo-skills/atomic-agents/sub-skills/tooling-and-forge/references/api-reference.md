# Tooling API Reference

## Core import surface

```python
from atomic_agents import BaseIOSchema, BaseTool, BaseToolConfig
from atomic_agents.base import BaseResource, BaseResourceConfig, BasePrompt, BasePromptConfig
from atomic_agents.utils import format_tool_message
```

## BaseTool

`BaseTool[InputSchema, OutputSchema](config=BaseToolConfig())`

- `input_schema` and `output_schema` are inferred from the generic parameters.
- `tool_name` defaults to the input schema title.
- `tool_description` defaults to the input schema description.
- `run(params)` is abstract and must return the typed output schema.

### Tool authoring pattern

1. Define an input schema that inherits from `BaseIOSchema`.
2. Define an output schema that inherits from `BaseIOSchema`.
3. Define a config class that inherits from `BaseToolConfig` if you need tunables.
4. Implement `run()` in the concrete tool class.

## BaseResource / BasePrompt

These follow the same generic pattern as `BaseTool`:

- `BaseResource[InputSchema, OutputSchema]` exposes `read()`.
- `BasePrompt[InputSchema, OutputSchema]` exposes `generate()`.
- Each base class derives names and descriptions from the input schema unless the config overrides them.

## Configuration objects

| Class | Purpose |
| --- | --- |
| `BaseToolConfig` | optional `title` / `description` overrides for tools |
| `BaseResourceConfig` | optional `title` / `description` overrides for resources |
| `BasePromptConfig` | optional `title` / `description` overrides for prompts |

## Tool selection patterns

### 1) Direct call

Use direct calls when the workflow is fixed and you already know which tool should run.

- Best for low latency and deterministic control.
- Tool parameters stay visible in normal Python code.
- Works well when the tool is required for correctness.

### 2) Choice agent

Use a routing agent when the user request determines which tool should run.

- The router output schema uses a `Union` of tool input schemas.
- Instructor validates the selection against the union.
- Dispatch on the returned schema type explicitly with `isinstance(...)`.

## Tool message formatting

`format_tool_message(tool_call, tool_id=None)` converts a Pydantic model instance into the message shape expected for a function/tool call:

- `id`: generated UUID if omitted
- `type`: `function`
- `function.name`: the model class name
- `function.arguments`: compact JSON string of the model data

## Related docs

- Use `forge-catalog.md` for the downloadable tool families.
- Use `cli-reference.md` for the `atomic` command.
