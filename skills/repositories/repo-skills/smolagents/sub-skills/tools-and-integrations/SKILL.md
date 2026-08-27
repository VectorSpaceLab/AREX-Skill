---
name: tools-and-integrations
description: "Use this sub-skill when defining, validating, sharing, loading, or
  troubleshooting smolagents tools, built-in/default tools, Hub/Space/LangChain
  integrations, or MCP tool collections."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Tools and Integrations

## Use This For

- Creating a smolagents tool with a `Tool` subclass or the `@tool` decorator.
- Designing `inputs`, `output_type`, optional `output_schema`, and runtime argument validation.
- Adding built-in tools such as `DuckDuckGoSearchTool`, `VisitWebpageTool`, `UserInputTool`, or `FinalAnswerTool` to an agent.
- Loading tools from Hub Spaces/collections, Gradio apps, LangChain tools, or MCP servers.
- Diagnosing schema, serialization, optional dependency, trust, network, and name-collision failures.

## Route Elsewhere

- Agent selection, managed agents, planning, callbacks, `max_steps`, or toolbox composition strategy across agents: use `../agent-workflows/SKILL.md`.
- Model classes, provider credentials, model routing, structured model output behavior, or LiteLLM setup: use `../model-providers/SKILL.md`.
- `smolagent`, `webagent`, Gradio UI, CLI commands, and app launching: use `../cli-and-ui/SKILL.md`.
- Code execution sandboxes, executor backends, authorized imports, and secure execution policy: use `../execution-and-safety/SKILL.md`.

## Fast Path

1. Choose `@tool` for a simple stateless function; choose a `Tool` subclass when you need class attributes, `setup()`, helper methods, lazy model/client initialization, or serialization control.
2. Keep tool names valid Python identifiers and unique inside an agent toolbox; `agent.tools` is a dict keyed by `tool.name`.
3. Validate schema shape before wiring a tool into an agent: `python scripts/validate_tool_schema.py path/to/tool_file.py --object tool_or_class_name`.
4. For remote or third-party integrations, require explicit trust (`trust_remote_code=True`) only after code/server review, and document optional extras.
5. Use bundled references for details:
   - [API reference](references/api-reference.md) for `Tool`, `@tool`, schemas, validation, serialization, and helper APIs.
   - [Workflows](references/workflows.md) for common recipes: decorator, subclass, structured output, MCP, Hub, Space, LangChain, and toolbox updates.
   - [Built-in tools](references/built-in-tools.md) for default tool capabilities and dependencies.
   - [Troubleshooting](references/troubleshooting.md) for common failures and fixes.

## Minimal Examples

Decorator tools must have type hints, a return type, and an `Args:` docstring section for every argument:

```python
from smolagents import tool

@tool
def normalize_label(label: str, lowercase: bool = True) -> str:
    """Normalize a user-facing label.

    Args:
        label: Label text to normalize.
        lowercase: Whether to lowercase before replacing spaces.
    """
    cleaned = label.strip().replace(" ", "_")
    return cleaned.lower() if lowercase else cleaned
```

Subclass tools must define `name`, `description`, `inputs`, `output_type`, and `forward`:

```python
from smolagents import Tool

class ReceiptLookupTool(Tool):
    name = "receipt_lookup"
    description = "Looks up a receipt summary by integer receipt id."
    inputs = {"receipt_id": {"type": "integer", "description": "Receipt id to retrieve."}}
    output_type = "string"

    def forward(self, receipt_id: int) -> str:
        return f"Receipt {receipt_id}: not connected to a database in this example."
```

## Guardrails

- Do not put secrets, local checkout paths, or private environment paths into tool code, descriptions, or serialized Hub artifacts.
- Put imports used by a serializable tool inside methods/functions, not only at module scope, so `save()`, `to_dict()`, and `push_to_hub()` can reconstruct self-contained code.
- Mark nullable/defaultable inputs consistently between `forward` type hints and `inputs`; mismatches raise validation errors.
- Treat `output_schema` as prompt/schema guidance for structured outputs; it does not replace testing the actual return value.
- Install optional extras only for the integration being used, such as MCP, web search, webpage parsing, LangChain, Gradio, or Transformers pipeline tools.
