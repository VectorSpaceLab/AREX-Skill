# LitServe MCP troubleshooting

Use this guide when MCP tools do not construct, do not list, do not connect, or do not call correctly.

## `fastmcp` missing or import failure

Symptom:

```text
mcp package is required for MCP support. To install, run `pip install fastmcp` in the terminal.
```

Cause:

- The runtime where the LitServe app is constructing `MCP()` does not have `fastmcp` installed.
- The server process may be using a different Python environment from the one where dependencies were installed.

Fix:

```bash
python -m pip install fastmcp
python - <<'PY'
import fastmcp
import mcp
from litserve.mcp import MCP
print("MCP imports ok")
PY
```

Then restart the LitServe process. Installing the package after the server has already started does not retrofit the running process.

## `MCP is not connected to a LitAPI`

Symptom:

```text
RuntimeError: MCP is not connected to a LitAPI.
```

Cause:

- `mcp.as_tool()` was called before the `MCP` object was passed into a `LitAPI` constructor.
- The application created `mcp = MCP(...)` but did not pass it as `mcp=mcp` to `super().__init__`.
- A test or debug snippet inspects the tool object before constructing the API.

Fix:

```python
mcp = MCP(name="predict", description="Run prediction.")
api = MyAPI(mcp=mcp)          # or super().__init__(mcp=mcp) inside MyAPI.__init__
tool = api.mcp.as_tool()      # now connected
```

For custom subclasses, connect in the class constructor:

```python
class MyAPI(ls.LitAPI):
    def __init__(self):
        super().__init__(api_path="/predict", mcp=MCP(description="Run prediction."))
```

Do not call private `_connect` methods in normal app code.

## Missing tool name

Symptom:

```text
ValueError: Name is required for MCP tool
```

Cause:

- `MCP(name=...)` was not set and the connected `LitAPI.api_path` resolved to an empty value.
- A custom object bypassed normal `LitAPI` initialization.

Fix:

- Prefer an explicit stable tool name:

```python
MCP(name="classify_text", description="Classify text.")
```

- Remember name sanitization: `/predict` becomes `predict`; `/v1/predict` becomes `v1_predict`.

## Missing tool description

Symptom:

```text
ValueError: Description is required for MCP tool
```

Cause:

- `MCP(description=...)` was omitted and the connected `LitAPI` class has no docstring.
- The docstring is empty or not useful enough for MCP clients.

Fix:

```python
MCP(description="Summarize text and return a short summary.")
```

A class docstring can be a fallback, but an explicit MCP description is clearer and more stable for tool selection.

## Malformed or missing input schema

Symptoms:

- Client lists the tool but rejects the schema.
- Client sends arguments that do not match the LitServe endpoint.
- Tool call fails with a missing `request` argument or Pydantic validation error.
- LitServe logs a warning that no input schema was provided and it is extracting one from `decode_request`.

Causes:

- Manual `input_schema` is not a complete object schema.
- Manual schema uses flat argument names while the default LitServe endpoint handler expects top-level `request`.
- `decode_request` has weak annotations, so extraction falls back to broad `string`, `array`, or `object` types.
- Generic list/dict item types were expected in the schema, but LitServe’s helper maps `list[str]` to `"array"` and `dict[str, int]` to `"object"` without nested item details.
- Python annotations were postponed into strings, so `extract_input_schema` could not see the actual Pydantic model class and fell back to broad types such as `"string"`.

Fix:

1. Prefer a Pydantic request model:

   ```python
   class Request(BaseModel):
       text: str
       top_k: int = 3

   def decode_request(self, request: Request):
       return request
   ```

2. Inspect the actual generated schema:

   ```python
   api = MyAPI()
   print(api.mcp.as_tool().inputSchema)
   ```

3. Shape MCP call arguments according to the top-level schema. For a `decode_request(self, request: Request)` endpoint, send:

   ```json
   {"request": {"text": "hello", "top_k": 3}}
   ```

4. If using a manual schema, make it a full object schema and verify a real `call_tool` round trip, not only `list_tools`.
5. For MCP-exposed methods, make sure the annotations visible at runtime are actual classes, or provide a verified manual schema.

## Tool endpoint collision or wrong endpoint

Symptoms:

- LitServe raises an `api_path` collision error during startup.
- MCP lists tools but a tool calls the wrong LitServe endpoint.
- MCP tool call fails with an endpoint lookup error.

Causes:

- Multiple `LitAPI` instances share the same `api_path`.
- Multiple MCP tools resolve to the same sanitized `name`.
- A custom connector was given a stale tool object whose `endpoint` is not mounted in the FastAPI app.
- Name sanitization made two distinct-looking names identical.

Fix:

- Give each `LitAPI` a unique `api_path`:

  ```python
  TextAPI(api_path="/classify")
  ImageAPI(api_path="/caption")
  ```

- Give each MCP tool a unique explicit `name`:

  ```python
  MCP(name="classify_text", description="Classify text.")
  MCP(name="caption_image", description="Caption an image.")
  ```

- Inspect generated tool metadata:

  ```python
  for api in apis:
      if api.mcp:
          tool = api.mcp.as_tool()
          print(tool.name, tool.endpoint)
  ```

- Avoid manually constructing or reusing tool objects across app instances unless you also verify that the endpoint path exists in that app.

## MCP endpoint not found or not connected by client

Symptoms:

- `http://localhost:8000/mcp/` returns 404 or fails to connect.
- MCP client says it is not connected.
- `list_tools()` never returns.

Causes:

- Server was started without any MCP-enabled `LitAPI` tools.
- MCP packages were not available in the server process.
- The URL is missing the `/mcp/` suffix or trailing slash.
- Client is pointed at the prediction endpoint (`/predict`) instead of the MCP endpoint (`/mcp/`).
- Server is not reachable from the client environment.
- The app has not finished startup yet.

Fix checklist:

1. Confirm the API was constructed with `mcp=MCP(...)`.
2. Confirm the server logs the MCP beta warning/enabled message at startup.
3. Use the exact streamable HTTP URL:

   ```text
   http://localhost:8000/mcp/
   ```

4. Check the LitServe app is reachable on the same host/port before testing MCP.
5. Verify a simple MCP client can initialize and `list_tools()`.
6. If using a remote or hosted environment, replace `localhost` with a public URL that the client can reach.

## Streamable HTTP mounting confusion

Normal LitServe apps do not need manual mounting. When tools exist, LitServe creates a connector and mounts the MCP Starlette app automatically. The resulting client-facing path is `/mcp/`.

Only use manual connector APIs for tests or advanced integration checks:

```python
from fastapi import FastAPI
from litserve.mcp import _LitMCPServerConnector

connector = _LitMCPServerConnector()
connector.connect_mcp_server([tool], app)
```

After connection, the FastAPI routes include a mount named `mcp`, and that mounted app handles `/mcp/`. If no tools are provided, `connect_mcp_server([], app)` returns without mounting anything.

## Claude Desktop setup confusion

Symptoms:

- Claude Desktop says the MCP server is disconnected.
- Tool never appears in Claude.
- The logged example URL does not work as copied.

Causes:

- `mcp-remote` is not installed where Claude Desktop can execute `npx`.
- The logged URL is a placeholder and was not replaced.
- The URL lacks `/mcp/` or is not publicly reachable.
- Localhost refers to a different machine or sandbox than the LitServe process.
- Claude Desktop settings were edited but the app was not restarted.

Fix:

```bash
npm install -g mcp-remote
```

Use this shape in Claude Desktop settings:

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

Then restart Claude Desktop. If the problem remains, test the same URL with a minimal MCP `list_tools()` client outside Claude Desktop.

## Beta support warning

LitServe emits a warning that MCP support is beta and APIs are subject to change. Treat the warning as informational unless behavior changed after a version upgrade.

Upgrade-safe habits:

- Pin LitServe and MCP package versions for production deployments.
- Inspect `api.mcp.as_tool()` after upgrades.
- Re-run a simple streamable HTTP `list_tools()` check.
- Re-test at least one real `call_tool()` request for each schema pattern you expose.
