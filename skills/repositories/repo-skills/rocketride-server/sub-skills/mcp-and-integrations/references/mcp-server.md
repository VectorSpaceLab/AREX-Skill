# RocketRide MCP server

`rocketride-mcp` exposes running RocketRide pipelines as Model Context Protocol
(MCP) tools for assistants such as Claude Desktop, Cursor, and Claude Code. The
server itself is a thin bridge:

```text
assistant MCP client
    ↓ stdio or HTTP/SSE MCP
rocketride-mcp
    ↓ RocketRide client over the engine WebSocket
running RocketRide engine and pipeline tasks
```

This reference is self-contained and intentionally avoids starting a server. For
engine startup, pipeline start/upload/status commands, or SDK token lifecycle,
route to the SDK/runtime sub-skills.

## Package and command surface

| Item | Behavior |
| --- | --- |
| Python package | `rocketride-mcp` |
| Python requirement | Python 3.10+ |
| Runtime dependency | `rocketride` Python client, plus MCP runtime |
| Primary command | `rocketride-mcp` (stdio MCP server) |
| Module command | `python -m rocketride_mcp` |
| Optional SSE command | `rocketride-mcp-sse --host 0.0.0.0 --port 8080` after installing the `sse` extra |
| Safe verification | Import/config checks only; the entry point has no normal `--help` mode and attempts to start a server |

## Environment variables

`rocketride-mcp` uses environment variables only; there is no separate config
file inside the MCP server.

| Variable | Required | Used by | Notes |
| --- | --- | --- | --- |
| `ROCKETRIDE_URI` | Yes | stdio and SSE MCP server | WebSocket URI for the RocketRide engine, typically `ws://localhost:5565` locally or a `wss://…` Cloud/on-prem endpoint. Do not use the HTTP gateway URL here. |
| `ROCKETRIDE_AUTH` | One of auth/APIKEY | stdio and SSE MCP server | Preferred by the config loader when both `ROCKETRIDE_AUTH` and `ROCKETRIDE_APIKEY` are present. |
| `ROCKETRIDE_APIKEY` | One of auth/APIKEY | stdio and SSE MCP server | Fallback accepted by the config loader. Some RocketRide tooling uses this name; MCP accepts it but `ROCKETRIDE_AUTH` wins if both are set. |
| `MCP_API_KEY` | No | SSE mode only | If set, non-`/health` SSE requests must send `Authorization: Bearer <MCP_API_KEY>`. `/health` remains unauthenticated for monitoring. |

Do not confuse MCP engine auth with the public `pk_…` authorization key shown for
a running HTTP/webhook pipeline. The `pk_…` key is for HTTP gateway calls from
n8n or other clients, not for configuring the MCP server's WebSocket client.

## Client configuration examples

### Claude Desktop

Add a server block to the Claude Desktop MCP config file:

```json
{
  "mcpServers": {
    "rocketride": {
      "command": "rocketride-mcp",
      "env": {
        "ROCKETRIDE_URI": "ws://localhost:5565",
        "ROCKETRIDE_AUTH": "your-engine-auth-token"
      }
    }
  }
}
```

### Cursor

Add a workspace MCP config such as `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "rocketride": {
      "command": "rocketride-mcp",
      "env": {
        "ROCKETRIDE_URI": "ws://localhost:5565",
        "ROCKETRIDE_AUTH": "your-engine-auth-token"
      }
    }
  }
}
```

### Claude Code

Register the command and provide env vars through the shell or the client config:

```bash
export ROCKETRIDE_URI=ws://localhost:5565
export ROCKETRIDE_AUTH=your-engine-auth-token
claude mcp add rocketride -- rocketride-mcp
```

### Safe preflight for configs

```bash
python scripts/mcp_config_smoke.py --client-config ./mcp.json --server-name rocketride
python scripts/mcp_config_smoke.py --check-current-env
```

The script checks variable presence and precedence; it does not connect to the
engine or start MCP.

## How pipelines become MCP tools

When the server starts, it connects once to RocketRide using `RocketRideClient`.
For each MCP tool-list request it asks the engine for running tasks
(`rrext_get_tasks`) and formats each task as an MCP tool.

Each dynamic tool has this minimal input schema:

```json
{
  "type": "object",
  "properties": {
    "filepath": { "type": "string", "description": "Path to file to process" }
  },
  "required": ["filepath"]
}
```

Tool execution behavior:

1. The assistant supplies a `filepath`.
2. The server accepts absolute paths, relative paths, `file://` URIs, and `~` home
   expansion, then resolves the path locally.
3. The path must point to a regular file visible to the MCP server process.
4. The file bytes are sent to the matching running RocketRide task token.
5. The response returns a human-readable text message and a structured payload in
   `structuredContent.result`.

Implications:

- The assistant client and `rocketride-mcp` process must agree on local file
  visibility. A path inside a container or remote workspace may not exist in the
  MCP process.
- Stop a RocketRide pipeline and its dynamic MCP tool disappears on the next
  tool-list refresh.
- If a tool name cannot be matched to a running task, the server returns a
  tool-not-found error instead of inventing a pipeline.

## Built-in convenience tool

`rocketride-mcp` also appends one convenience tool to the dynamic task list:

| Tool | Purpose | Pipeline behavior |
| --- | --- | --- |
| `RocketRide_Document_Processor` | Parse a local file without requiring a pre-started task | Starts the bundled `simpleparser` pipeline on demand, sends the file bytes, and returns parsed lanes. |

The bundled parser pipeline is:

```text
webhook_1 → parse_1 → response_1
```

`parse_1` emits `text`, `video`, `table`, `image`, and `audio` lanes into the
response node. It still requires a reachable RocketRide engine and whatever
runtime support the `parse` node needs in that engine. The convenience tool only
removes the need to pre-start a specific task token.

## MCP resources

The server exposes three read-only resources with JSON payloads:

| URI | Name | Payload |
| --- | --- | --- |
| `rocketride://pipelines` | Pipeline List | `{"pipelines": [{"name", "description"}, ...]}` from running tasks. |
| `rocketride://status` | Server Status | Connection status, pipeline count, and pipeline names. |
| `rocketride://nodes` | Node Registry | Node schemas from `rrext_get_nodes`, or an empty list on unsupported/error responses. |

If the internal RocketRide client is not connected, resource reads return JSON
error payloads such as `{"pipelines": [], "error": "Client is not connected"}`.
Unknown resource URIs raise an error.

## MCP prompt templates

Three prompt templates are available to MCP clients:

| Prompt | Required arguments | Use |
| --- | --- | --- |
| `analyze-document` | `pipeline`, `query` | Ask the assistant to analyze a document with a named RocketRide pipeline. |
| `chat-with-data` | `pipeline`, `question` | Start a conversation about data processed by a pipeline. |
| `evaluate-pipeline` | `pipeline`, `test_input`; optional `expected_output` | Ask for an output-quality evaluation against test input. |

These templates produce assistant-facing messages only; they do not start or
validate pipelines.

## SSE mode notes

SSE mode exists for remote or Docker-style MCP clients:

```bash
pip install "rocketride-mcp[sse]"
export ROCKETRIDE_URI=ws://engine:5565
export ROCKETRIDE_AUTH=your-engine-auth-token
export MCP_API_KEY=optional-mcp-bearer-token
rocketride-mcp-sse --host 0.0.0.0 --port 8080
```

Use SSE only when an MCP client needs network transport. Stdio is simpler for
local Claude/Cursor/Claude Code configs. Before production use, validate the
installed `rocketride-mcp` version in the target environment because SSE was not
part of the minimum safe verification scope for this generated skill.

## Minimal MCP exposure checklist

1. A RocketRide engine is reachable at `ROCKETRIDE_URI` over WebSocket.
2. `ROCKETRIDE_AUTH` or `ROCKETRIDE_APIKEY` is set; if both are set, expect
   `ROCKETRIDE_AUTH` to win.
3. The pipeline to expose is already running, unless using
   `RocketRide_Document_Processor`.
4. The assistant passes a file path that the MCP server process can read.
5. Client config uses `rocketride-mcp` as the command and puts secrets in `env`,
   not in prompts or pipeline JSON.
