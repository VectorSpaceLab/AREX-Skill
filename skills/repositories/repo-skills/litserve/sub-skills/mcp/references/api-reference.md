# LitServe MCP API reference

This reference captures the operational MCP behavior needed to expose a `LitAPI` as an MCP tool without reading the source checkout.

## Dependency boundary

- Import MCP support with `from litserve.mcp import MCP`.
- `fastmcp` must be installed before constructing `MCP`. When it is missing, `MCP()` raises:

```text
mcp package is required for MCP support. To install, run `pip install fastmcp` in the terminal.
```

- The LitServe server-side mount is gated by MCP package availability. In practice, install `fastmcp` in the same environment that runs the LitServe app so both `fastmcp` and the underlying `mcp` package are available.

## `MCP` constructor

```python
from litserve.mcp import MCP

mcp = MCP(
    description="Human-readable tool description.",
    input_schema=None,      # optional dict[str, Any]
    name=None,              # optional tool name
)
```

Parameters:

- `description: Optional[str]` — description shown to MCP clients. If omitted, `as_tool()` falls back to the connected `LitAPI` class docstring.
- `input_schema: Optional[dict[str, Any]]` — JSON-schema-like dictionary to use as the MCP `inputSchema`. If omitted, `as_tool()` extracts a schema from `lit_api.decode_request`.
- `name: Optional[str]` — MCP tool name. If omitted, `as_tool()` falls back to the connected `LitAPI.api_path`.

Name handling:

- A leading slash is stripped.
- Remaining slashes are converted to underscores.
- Examples: `/predict` becomes `predict`; `/v1/classify` becomes `v1_classify`.
- Choose a unique `name` when serving multiple MCP-enabled `LitAPI` instances; duplicate tool names can collide in the MCP connector mapping.

Validation timing:

- `MCP.__init__` stores `description`, `input_schema`, and `name`; it does not prove that the schema matches the endpoint call signature.
- `MCP.as_tool()` validates that the MCP object is connected to a `LitAPI`, and that resolved `name` and `description` are non-empty.
- MCP clients may reject malformed `inputSchema` values even if LitServe accepted the dictionary.

## Connection to `LitAPI`

Pass the `MCP` object into the `LitAPI` constructor:

```python
import litserve as ls
from litserve.mcp import MCP

class MyAPI(ls.LitAPI):
    """Short fallback description if MCP(description=...) is omitted."""

    def __init__(self):
        super().__init__(api_path="/predict", mcp=MCP(description="Run prediction."))
```

`LitAPI.__init__(..., mcp=mcp)` connects the MCP object to the API. Calling `mcp.as_tool()` before that connection raises:

```text
MCP is not connected to a LitAPI.
```

Do not call private connection methods in user applications; pass `mcp=` to the API constructor instead.

## `MCP.as_tool()`

`MCP.as_tool()` returns a `ToolEndpointType` with these operational fields:

- `name` — sanitized MCP tool name.
- `description` — constructor description or connected `LitAPI` docstring.
- `inputSchema` — manual `input_schema` if provided; otherwise auto-extracted from `decode_request`.
- `endpoint` — connected `LitAPI.api_path`, such as `/predict`.

Required conditions:

- The `MCP` object must already be connected to a `LitAPI`.
- The resolved tool name must be non-empty.
- The resolved description must be non-empty.

If `input_schema` is omitted, LitServe logs a warning and calls `extract_input_schema(self.lit_api.decode_request)`.

## Schema extraction helpers

Import helpers:

```python
from litserve.mcp import extract_input_schema, _python_type_to_json_schema, _param_name_to_title
```

### `extract_input_schema(func) -> dict[str, Any]`

The helper returns a dictionary with MCP `inputSchema`-compatible shape for function parameters or Pydantic models.

For a Pydantic `BaseModel` class:

```python
from pydantic import BaseModel
from litserve.mcp import extract_input_schema

class PowerRequest(BaseModel):
    input: float

schema = extract_input_schema(PowerRequest)
```

The schema contains:

- `type: "object"`
- `title: "PowerRequestArguments"`
- `properties: {"powerrequest": {"$ref": "#/$defs/PowerRequest"}}`
- `required: ["powerrequest"]`
- `$defs.PowerRequest` copied from the Pydantic model schema

For a bound `decode_request(self, request: PowerRequest)` method, the schema instead wraps the parameter name:

```json
{
  "type": "object",
  "title": "decode_requestArguments",
  "properties": {
    "request": {"$ref": "#/$defs/PowerRequest"}
  },
  "required": ["request"],
  "$defs": {
    "PowerRequest": {
      "type": "object",
      "title": "PowerRequest",
      "properties": {
        "input": {"title": "Input", "type": "number"}
      },
      "required": ["input"]
    }
  }
}
```

For a normal function:

```python
def classify(text: str, top_k: int = 3):
    ...
```

The schema has `properties.text.type == "string"`, `properties.top_k.type == "integer"`, `required == ["text"]`, and `title == "classifyArguments"`.

Extraction rules:

- `*args` and `**kwargs` are skipped.
- Unannotated parameters default to JSON Schema type `"string"`.
- Parameters without defaults are marked required.
- Parameters with defaults are optional.
- A parameter annotated as a Pydantic `BaseModel` becomes a `$ref` property and the model schema is added under `$defs`.
- Nested Pydantic models are represented through Pydantic’s `$defs` output.
- Pydantic `Field` metadata inside models is preserved by Pydantic’s own schema output.
- For `Field` defaults on plain function parameters, LitServe attempts to copy description/default/constraint metadata into the property schema.
- Extraction uses the runtime annotations visible through `inspect.signature`. If annotations are postponed into strings, Pydantic model parameters may be treated as unknown types and fall back to `"string"`; use real runtime annotations or provide a verified manual schema for MCP-exposed methods.

### `_python_type_to_json_schema(python_type)`

Verified mappings:

| Python annotation | Returned schema fragment |
| --- | --- |
| no annotation / `inspect.Parameter.empty` | `"string"` |
| `int` | `"integer"` |
| `float` | `"number"` |
| `str` | `"string"` |
| `bool` | `"boolean"` |
| `list` | `"array"` |
| `dict` | `"object"` |
| `Optional[int]` | `{"type": "integer", "nullable": True}` |
| `Optional[str]` | `{"type": "string", "nullable": True}` |
| `Optional[bool]` | `{"type": "boolean", "nullable": True}` |
| `Optional[list]` | `{"type": "array", "nullable": True}` |
| `Optional[dict]` | `{"type": "object", "nullable": True}` |
| `list[str]` | `"array"` |
| `dict[str, int]` | `"object"` |
| unknown type | `"string"` |

The helper does not expand generic item schemas for `list[str]` or `dict[str, int]`; use a Pydantic model or a manual `input_schema` when precise nested schema matters.

### `_param_name_to_title(param_name)`

Converts underscores into a readable title:

- `name` -> `Name`
- `age` -> `Age`
- `is_active` -> `Is Active`

## Manual `input_schema` shape

When you supply `input_schema`, LitServe passes it through to the returned MCP tool as `inputSchema`.

Recommended full shape:

```python
MCP(
    name="power",
    description="Return the square of a number.",
    input_schema={
        "type": "object",
        "properties": {
            "request": {
                "type": "object",
                "properties": {"input": {"type": "number", "title": "Input"}},
                "required": ["input"],
            }
        },
        "required": ["request"],
    },
)
```

For a default `LitAPI` endpoint, MCP tool-call arguments are bound against the generated endpoint handler, whose parameter is usually named `request`. A flat manual schema such as `{"properties": {"input": ...}}` may list successfully but fail at call time because the endpoint expects a `request` argument. Prefer auto-extraction from `decode_request` unless you have verified the call arguments against the endpoint handler.

## Streamable HTTP connector

LitServe collects MCP tools from each `LitAPI` with an attached `mcp` object and calls `as_tool()` for each one.

Internal connector behavior:

- `_LitMCPServerConnector()` creates a low-level MCP server named `mcp-streamable-http-stateless`.
- `add_tool(tool)` stores `tool_endpoint_connections[tool.name] = tool.endpoint` and appends the tool to the list returned by `list_tools()`.
- `connect_mcp_server(mcp_tools, app)` returns immediately if the tool list is empty.
- With tools present, it registers MCP `list_tools` and `call_tool` handlers, emits a beta-support warning, and mounts a Starlette streamable HTTP app into the LitServe FastAPI app.
- The Starlette MCP app has an internal `Mount("/mcp/", ...)` route and is mounted at FastAPI root with name `"mcp"`.
- The client-facing URL is therefore `<litserve-base-url>/mcp/`, for example `http://localhost:8000/mcp/`.
- The streamable HTTP session manager is stateless and uses JSON responses.

Tool calls:

1. MCP client calls a tool by name with arguments.
2. The connector maps the tool name to the original LitServe endpoint path.
3. It finds the FastAPI route whose `route.path` equals that endpoint path.
4. It binds MCP arguments to that endpoint handler signature.
5. If a bound argument annotation is a Pydantic `BaseModel`, it constructs the model from the supplied dictionary.
6. It calls the endpoint handler and converts the response to MCP content.

Implications:

- Tool names must be unique enough to map to the intended endpoint.
- The endpoint path recorded in the tool must exist in the FastAPI app at call time.
- Manual schemas must produce argument names compatible with the endpoint handler.
- If multiple `LitAPI` instances use the same `api_path`, LitServe detects the path collision before serving.
