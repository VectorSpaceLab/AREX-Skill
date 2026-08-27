# Tool Troubleshooting

## `@tool` Fails During Decoration

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Tool return type not found` | Function has parameters but no return type hint. | Add `-> str`, `-> int`, `-> dict[...]`, `-> None`, etc. |
| Error about missing argument description | Docstring lacks an `Args:` entry for one or more parameters. | Add a docstring `Args:` section with every argument. |
| Multiple decorator error | Function is decorated with `@tool` more than once. | Keep exactly one `@tool`. |
| Warning about decorators other than `@tool` | Extra decorators may not serialize correctly. | Prefer wrapping logic inside the function body or subclass `Tool`. |
| Unexpected schema for optional values | Defaults and `Optional`/`| None` become `nullable`. | Check generated `tool.inputs` and update descriptions/tests. |

Good decorator skeleton:

```python
from smolagents import tool

@tool
def summarize(text: str, max_words: int = 50) -> str:
    """Summarize text.

    Args:
        text: Text to summarize.
        max_words: Maximum words to return.
    """
    return " ".join(text.split()[:max_words])
```

## `Tool` Subclass Fails on Instantiation

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `You must set an attribute output_type` | Missing required class attribute. | Define `name`, `description`, `inputs`, and `output_type`. |
| Invalid tool name | `name` is not a valid Python identifier or is a reserved keyword. | Use `snake_case`, no spaces or hyphens. |
| Input type validation error | `inputs` uses unsupported type strings. | Use only `string`, `boolean`, `integer`, `number`, `image`, `audio`, `array`, `object`, `any`, `null`, or a list of those strings. |
| Nullable mismatch | `inputs` and `forward` signature disagree. | Align `nullable: True` with defaults or `| None`; remove `nullable` when required. |
| Type mismatch in runtime arguments | Tool was called with wrong argument JSON type. | Use `validate_tool_arguments(tool, args)` in tests before agent runs. |

## Serialization, Hub, and Remote Executor Failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Undefined name such as `np` during `save()` or `to_dict()` | Import or global variable lives outside tool methods. | Move imports into `forward`, `setup`, or helper methods. |
| Required `__init__` parameter error | Serializable tool constructors must have defaults. | Give every constructor parameter a literal default, or avoid serialization. |
| Non-literal default/complex class attribute error | Source reconstruction only supports simple class-level literals. | Move computed values into `__init__` or `setup`. |
| Cannot save wrappers from Space/LangChain/Gradio | These wrapper tools are dynamic integration adapters. | Recreate integration code in application setup; do not serialize wrapper instances. |
| Hub load asks for trust | Remote tool code executes locally. | Inspect remote Space code, then pass `trust_remote_code=True` only when trusted. |
| Hub auth or network failure | Private repo, missing token, offline runtime, or revision mismatch. | Pass a valid token, check repo visibility/revision, and add retry/user-facing fallback outside the agent. |

## Optional Dependency Failures

| Integration | Error pattern | Install/check |
| --- | --- | --- |
| DuckDuckGo search | Missing `ddgs` | Install `ddgs`; consider rate limiting and no-results handling. |
| Webpage visit | Missing `markdownify` or `requests` | Install both packages; validate URL and handle timeouts. |
| Wikipedia search | Missing `wikipedia-api` | Install it and set a meaningful user agent. |
| MCP tools | Message says install MCP extra | Install the MCP integration extras and ensure `mcpadapt` is importable. |
| LangChain tool | Missing LangChain/provider package or provider credentials | Install LangChain plus provider SDK and configure provider credentials. |
| Gradio Space | Missing Gradio client or remote endpoint incompatibility | Install Space client dependencies and inspect Space API names/input types. |
| Pipeline tools | Missing Transformers/Torch/Accelerate | Install model extras and check local hardware/model availability. |

## MCP Server Lifetime Errors

Use context managers whenever possible:

```python
with ToolCollection.from_mcp(server_parameters, trust_remote_code=True) as collection:
    tools = [*collection.tools]
```

If you need manual lifecycle control:

```python
client = MCPClient(server_parameters, structured_output=True)
try:
    tools = client.get_tools()
finally:
    client.disconnect()
```

Common MCP fixes:

- Pass `trust_remote_code=True` to `ToolCollection.from_mcp`; it fails intentionally without this acknowledgement.
- Use `structured_output=True` explicitly when relying on `outputSchema` or structured content.
- For dict server parameters, set `transport` to `streamable-http` or `sse`; omitted transport defaults to `streamable-http`.
- Ensure stdio server commands are available in the runtime and do not wait for interactive prompts.
- If connecting to multiple servers, check for duplicate names before adding tools to an agent.

## Tool Name Collisions

`agent.tools` is a dictionary keyed by `tool.name`. Built-ins such as `DuckDuckGoSearchTool`, `GoogleSearchTool`, and other web search variants may all use `web_search`.

Detect collisions before merging:

```python
names = [tool.name for tool in tools]
duplicates = sorted({name for name in names if names.count(name) > 1})
if duplicates:
    raise ValueError(f"Duplicate tool names: {duplicates}")
```

Fix collisions by subclassing with a new `name`, wrapping one provider behind a routing tool, or only adding the provider selected for the current workflow.

## Output Type Mismatch

If the model or caller expects one type but the tool returns another:

- Check `output_type` against the actual return type.
- Use `output_type = "object"` for dict-like structured returns and optionally add `output_schema`.
- Use `output_type = "array"` for lists, not `object`.
- Use `output_type = "any"` sparingly for final answers or polymorphic tools.
- Test `tool(..., sanitize_inputs_outputs=True)` when the application depends on smolagents agent type wrappers.

## Poor Tool Selection by the Model

Schema validity is not enough for good agent behavior. Improve:

- Tool `name`: action-oriented and specific, such as `lookup_receipt` rather than `helper`.
- `description`: include when to use the tool, important constraints, and return shape.
- Input descriptions: specify units, allowed values, expected formats, and whether a value should be affirmative rather than a question.
- Toolbox size: remove redundant tools or rename them to make differences obvious.
