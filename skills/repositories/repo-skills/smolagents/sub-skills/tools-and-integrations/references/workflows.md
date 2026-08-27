# Tool Workflows

## Choose a Tool Pattern

| Need | Recommended pattern |
| --- | --- |
| One pure function, no setup, easy type hints | `@tool` decorator |
| Lazy setup, clients, helper methods, custom serialization behavior | `Tool` subclass |
| Existing Gradio Space endpoint | `Tool.from_space(...)` |
| Existing LangChain tool | `Tool.from_langchain(...)` |
| Shared Hub Space tool | `load_tool(...)` or `Tool.from_hub(...)` |
| Hub collection of Space tools | `ToolCollection.from_hub(...)` |
| MCP server tools | `ToolCollection.from_mcp(...)` or `MCPClient` |

## Build a Simple `@tool`

```python
from smolagents import CodeAgent, InferenceClientModel, tool

@tool
def count_words(text: str) -> int:
    """Count whitespace-separated words in text.

    Args:
        text: Text to inspect.
    """
    return len(text.split())

agent = CodeAgent(tools=[count_words], model=InferenceClientModel())
```

Checklist:

- Function name becomes the tool name; use a valid, descriptive Python identifier.
- Every argument has a type hint and docstring entry.
- The function has a return type hint.
- Defaulted parameters become optional/nullable from the agent's perspective; be explicit in descriptions.

## Build a `Tool` Subclass

Use a subclass when the tool owns resources, caches, or helper methods:

```python
from smolagents import Tool

class KeywordSearchTool(Tool):
    name = "keyword_search"
    description = "Searches a local list of documents by keyword and returns matching snippets."
    inputs = {"query": {"type": "string", "description": "Keyword or phrase to match."}}
    output_type = "string"

    def __init__(self, documents: list[str] | None = None):
        super().__init__()
        self.documents = documents or []

    def forward(self, query: str) -> str:
        matches = [doc for doc in self.documents if query.lower() in doc.lower()]
        return "\n".join(matches[:5]) or "No matches found."
```

For Hub-serializable tools, avoid required `__init__` parameters and put external imports inside methods. For local-only tools inside an application, constructor parameters are fine if you do not plan to call `save()`, `to_dict()`, or `push_to_hub()`.

## Add Structured Output Guidance

`output_schema` tells the agent how to consume structured returns. It is especially useful for `CodeAgent`, because the generated tool prompt includes a schema note.

```python
from smolagents import Tool

class ParseReceiptTool(Tool):
    name = "parse_receipt"
    description = "Extracts receipt totals from plain text."
    inputs = {"text": {"type": "string", "description": "Receipt text."}}
    output_type = "object"
    output_schema = {
        "type": "object",
        "properties": {
            "merchant": {"type": "string"},
            "total": {"type": "number"},
            "currency": {"type": "string"},
        },
        "required": ["merchant", "total"],
    }

    def forward(self, text: str) -> dict:
        return {"merchant": "Example", "total": 12.5, "currency": "USD"}
```

`output_schema` is not a runtime validator. Add your own assertions or tests if malformed returns would be dangerous.

## Validate Before Agent Wiring

Use the bundled helper for local tool modules:

```bash
python scripts/validate_tool_schema.py my_tools.py --object ParseReceiptTool --call-json '{"text":"Total: $12.50"}'
```

Use `validate_tool_arguments` inside tests when checking an already-created tool:

```python
from smolagents import validate_tool_arguments

validate_tool_arguments(parse_receipt_tool, {"text": "Total: $12.50"})
```

## Manage an Agent Toolbox

An agent stores tools in a dictionary keyed by name. Adding a tool with an existing name replaces the previous one.

```python
agent.tools[new_tool.name] = new_tool
```

Before adding dynamic tools, check for collisions:

```python
if new_tool.name in agent.tools:
    raise ValueError(f"Tool name already exists: {new_tool.name}")
agent.tools[new_tool.name] = new_tool
```

Keep the toolbox small and focused. Too many similar tools can degrade model choice quality.

## Use Hub and Space Tools

Load a Space tool only after code review:

```python
from smolagents import CodeAgent, InferenceClientModel, load_tool

image_tool = load_tool("username/image-tool-space", trust_remote_code=True)
agent = CodeAgent(tools=[image_tool], model=InferenceClientModel())
```

Wrap a Gradio Space directly when the API endpoint is the tool:

```python
from smolagents import Tool

captioner = Tool.from_space(
    "username/caption-space",
    name="caption_image",
    description="Generates a caption for an input image.",
)
```

Load a Hub collection of Spaces:

```python
from smolagents import ToolCollection

collection = ToolCollection.from_hub("owner/collection-slug", trust_remote_code=True)
tools = [*collection.tools]
```

Hub and Space workflows can fail because of missing auth, private repos, network errors, incompatible Space inputs, or untrusted code. Handle these outside the agent run when possible.

## Convert a LangChain Tool

```python
from langchain.agents import load_tools
from smolagents import Tool

serp_tool = Tool.from_langchain(load_tools(["serpapi"])[0])
```

Notes:

- Install LangChain and the provider package separately.
- The wrapped name is lowercased.
- The wrapper removes LangChain schema `title` fields and fills empty descriptions; improve descriptions manually if model tool selection is poor.
- The wrapper calls `langchain_tool.run(...)` with mapped positional/keyword inputs.

## Load MCP Tools with `ToolCollection.from_mcp`

Use `ToolCollection.from_mcp` when you want a context-managed list of smolagents tools from one MCP server:

```python
from mcp import StdioServerParameters
from smolagents import CodeAgent, InferenceClientModel, ToolCollection

server_parameters = StdioServerParameters(
    command="python",
    args=["-c", "from mcp.server.fastmcp import FastMCP; mcp = FastMCP('empty'); mcp.run()"],
)

with ToolCollection.from_mcp(
    server_parameters,
    trust_remote_code=True,
    structured_output=True,
) as collection:
    agent = CodeAgent(tools=[*collection.tools], model=InferenceClientModel())
```

Supported server parameter forms:

- `mcp.StdioServerParameters(...)` for subprocess stdio servers.
- `{"url": "http://host:port/mcp", "transport": "streamable-http"}` for streamable HTTP.
- `{"url": "http://host:port/sse", "transport": "sse"}` for legacy SSE.

Rules:

- Install the MCP extra before using this path.
- Pass `trust_remote_code=True`; otherwise loading fails by design.
- Use the context manager so the server/client lifetime closes cleanly.
- Pass `structured_output=True` when MCP tools expose output schemas or structured content. If unset, smolagents currently warns and uses legacy text-oriented behavior.

## Use `MCPClient` Directly

Use `MCPClient` instead of `ToolCollection.from_mcp` when you need lower-level lifecycle control, multiple servers, or explicit `disconnect()`:

```python
from smolagents import MCPClient

client = MCPClient(server_parameters, structured_output=True)
try:
    tools = client.get_tools()
finally:
    client.disconnect()
```

A list of server parameter objects/dicts can connect to multiple MCP servers. Watch for duplicate tool names when merging tools from multiple servers.

## Adapt Source Examples Safely

Repository examples demonstrate useful patterns but often require live models, provider credentials, network datasets, or services:

- RAG tools show a `Tool` subclass wrapping a retriever; adapt the pattern with local documents when avoiding network/model dependencies.
- Text-to-SQL tools show a `@tool` function that closes over a database engine; this is useful for local apps, but not Hub-serializable unless connection creation is inside the tool or class.
- Structured-output MCP examples show inline FastMCP servers and `structured_output=True`; use them as design references, not as default smoke tests, because they require the MCP extra and a model to exercise the full agent loop.
