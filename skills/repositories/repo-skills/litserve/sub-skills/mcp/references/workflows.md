# LitServe MCP workflows

Use these workflows to add MCP to a LitServe app, expose a `decode_request` schema, verify the generated tool metadata, and connect streamable HTTP MCP clients.

## Add MCP to a new `LitAPI`

```python
from pydantic import BaseModel, Field
import litserve as ls
from litserve.mcp import MCP

class PowerRequest(BaseModel):
    input: float = Field(description="Number whose square should be returned.")

class PowerAPI(ls.LitAPI):
    """Return the square of a number."""

    def __init__(self):
        super().__init__(
            api_path="/predict",
            mcp=MCP(
                name="power",
                description="Return the square of a number.",
            ),
        )

    def setup(self, device):
        self.device = device

    def decode_request(self, request: PowerRequest) -> float:
        return request.input

    def predict(self, x: float) -> float:
        return x * x

    def encode_response(self, output: float) -> dict:
        return {"output": output}

if __name__ == "__main__":
    server = ls.LitServer(PowerAPI())
    server.run(port=8000)
```

Why this works:

- `MCP(...)` is passed into `LitAPI.__init__`, so `as_tool()` is connected.
- `name="power"` is unique and stable for clients.
- `description` is non-empty and explains when to use the tool.
- `input_schema` is omitted, so LitServe auto-extracts a schema from the bound `decode_request(request: PowerRequest)` method.
- LitServe automatically mounts the MCP streamable HTTP route at `http://localhost:8000/mcp/` when the server starts and MCP packages are installed.

## Add MCP to an existing `LitAPI`

Find the class constructor and add `mcp=` to the `super().__init__` call:

```python
class ExistingAPI(ls.LitAPI):
    def __init__(self, model_name: str):
        super().__init__(
            api_path="/classify",
            mcp=MCP(
                name="classify_text",
                description=f"Classify text with {model_name}.",
            ),
        )
        self.model_name = model_name
```

If the class currently does not define `__init__`, add one and preserve any existing defaults needed by the app:

```python
class ExistingAPI(ls.LitAPI):
    def __init__(self):
        super().__init__(api_path="/predict", mcp=MCP(description="Run prediction."))
```

If the app passes `api_path`, batching, streaming, or spec options from outside the class, keep those options and add `mcp` alongside them rather than replacing the server design.

## Make a tool from `decode_request`

Use a Pydantic request model whenever possible:

```python
from typing import Optional
from pydantic import BaseModel, Field

class SummarizeRequest(BaseModel):
    text: str = Field(min_length=1, description="Text to summarize.")
    max_tokens: int = Field(default=128, ge=1, le=1024)
    style: Optional[str] = Field(default=None, description="Optional summary style.")

class SummarizeAPI(ls.LitAPI):
    def __init__(self):
        super().__init__(
            api_path="/summarize",
            mcp=MCP(name="summarize", description="Summarize text."),
        )

    def decode_request(self, request: SummarizeRequest):
        return request
```

The generated tool schema will be wrapped under the `request` parameter because the endpoint handler accepts `request: SummarizeRequest`. MCP tool-call arguments should therefore look like:

```json
{
  "request": {
    "text": "Long text...",
    "max_tokens": 128,
    "style": "bullet points"
  }
}
```

Avoid assuming the MCP call should be a flat object unless you have supplied and verified a manual schema that matches the endpoint handler signature.

## Preview the generated schema or tool object

After the API is constructed, the MCP object is connected and can be inspected:

```python
import json

api = SummarizeAPI()
tool = api.mcp.as_tool()
print(tool.name)
print(tool.endpoint)
print(json.dumps(tool.inputSchema, indent=2))
```

This is a fast way to catch missing descriptions, unexpected tool names, and schema shape issues before starting a long-running server.

## Build a schema directly from Pydantic or type hints

For model classes:

```python
schema = extract_input_schema(SummarizeRequest)
```

For a connected API method:

```python
api = SummarizeAPI()
schema = extract_input_schema(api.decode_request)
```

For a regular function:

```python
def search(query: str, top_k: int = 5):
    ...

schema = extract_input_schema(search)
```

Guidance:

- Use Pydantic models for nested objects, constraints, descriptions, and defaults.
- Use regular type hints for simple primitive arguments.
- Use a manual `input_schema` for schemas that need precise list item types, unions beyond optional, or MCP-client-specific descriptions.
- If you supply a manual schema for a default `LitAPI` endpoint, keep the top-level argument name compatible with the endpoint handler, usually `request`.

## Run the bundled MCP example

From the installed LitServe environment, run:

```bash
python scripts/mcp_server.py --print-tool
python scripts/mcp_server.py --port 8000
```

The running server exposes:

- LitServe prediction endpoint: `POST http://localhost:8000/predict`
- MCP streamable HTTP endpoint: `http://localhost:8000/mcp/`

Expected MCP tool-call argument shape for the bundled example:

```json
{"request": {"input": 3.0}}
```

## Check the streamable HTTP route with an MCP client

Use this only as a reference snippet in a debug environment that has MCP client packages installed:

```python
import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async def main():
    async with (
        streamablehttp_client("http://localhost:8000/mcp/") as (read_stream, write_stream, _),
        ClientSession(read_stream, write_stream) as session,
    ):
        await session.initialize()
        result = await session.list_tools()
        print(result.tools)

asyncio.run(main())
```

If `list_tools()` returns the expected tool, the MCP mount is reachable. If `call_tool()` fails after listing succeeds, move to schema and endpoint-path troubleshooting.

## Claude Desktop integration notes

LitServe logs a reference configuration when MCP support is enabled. Use it as a template, not as a literal URL:

```json
{
  "mcpServers": {
    "litserve": {
      "command": "npx",
      "args": ["mcp-remote", "https://YOUR_PUBLIC_LITSERVE_HOST/mcp/"]
    }
  }
}
```

Checklist:

1. Install the bridge where Claude Desktop can run it:

   ```bash
   npm install -g mcp-remote
   ```

2. Replace the URL with the public, reachable LitServe base URL plus `/mcp/`.
3. Keep the trailing slash: `/mcp/`.
4. Restart Claude Desktop after editing its settings.
5. If using localhost, remember that Claude Desktop must run on the same machine/network context as the LitServe server.
6. MCP support is beta; verify with a simple `list_tools()` client if Claude Desktop reports a vague connection error.

## Multiple MCP tools in one server

Use multiple `LitAPI` instances with distinct `api_path` values and distinct MCP names:

```python
apis = [
    TextAPI(api_path="/classify", mcp=MCP(name="classify_text", description="Classify text.")),
    VisionAPI(api_path="/caption", mcp=MCP(name="caption_image", description="Caption an image.")),
]
server = ls.LitServer(apis)
server.run(port=8000)
```

Rules:

- `api_path` values must be unique; LitServe rejects path collisions.
- MCP `name` values should also be unique; duplicate names can overwrite the name-to-endpoint mapping in the connector even if the tool list still contains both tools.
- Name sanitization converts slashes to underscores, so `/v1/predict` and `v1_predict` resolve to the same tool name unless you override `name`.
