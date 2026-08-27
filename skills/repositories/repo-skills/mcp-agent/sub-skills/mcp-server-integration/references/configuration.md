# MCP Server Configuration

This reference distills the server-facing parts of `mcp-agent` configuration. Use it to define upstream MCP servers, validate transport fields, wire roots, restrict tools, and prepare client-side installation safely.

## Configuration Shape

A typical `mcp_agent.config.yaml` contains a top-level `mcp.servers` map. Each key is the registry name future agents must use in `server_names`, `gen_client(...)`, or `MCPAggregator(...)`.

```yaml
execution_engine: asyncio

mcp:
  servers:
    fetch:
      transport: stdio
      command: uvx
      args: ["mcp-server-fetch"]
      description: "Fetch URL content"

    docs_api:
      transport: streamable_http
      url: "https://api.example.com/mcp"
      headers:
        Authorization: "Bearer ${DOCS_API_TOKEN}"
      http_timeout_seconds: 30
      read_timeout_seconds: 120
      terminate_on_close: true

    project_tools:
      transport: stdio
      command: python
      args: ["-m", "project_mcp_server"]
      env:
        LOG_LEVEL: info
      roots:
        - uri: "file:///project/data"
          name: "project-data"
          server_uri_alias: "file:///mnt/data"
      allowed_tools: ["search_docs", "read_doc"]
```

The underlying settings model accepts these core fields on each server:

| Field | Use |
| --- | --- |
| `name` | Optional display name. Defaults to the map key when absent. |
| `description` | Human-readable server purpose. |
| `transport` | `stdio`, `sse`, `streamable_http`, or `websocket`; defaults to `stdio`. |
| `command`, `args`, `cwd`, `env` | Subprocess launch details for `stdio` servers. |
| `url`, `headers` | Remote endpoint and request headers for remote transports. |
| `http_timeout_seconds` | HTTP request timeout for SSE/streamable HTTP. |
| `read_timeout_seconds` | Wait time for new events/messages before a read timeout. |
| `terminate_on_close` | Streamable HTTP session-close behavior; defaults to `true`. |
| `auth.oauth` | Delegated OAuth client configuration for protected downstream servers. |
| `roots` | Declared filesystem roots; each URI must start with `file://`. |
| `allowed_tools` | Exact allowlist of tools exposed from this server. |

## Transport Rules

### `stdio`

Use for local subprocess servers. `command` is required and `args` should be a list. `env` values are passed to the subprocess along with the default environment.

```yaml
mcp:
  servers:
    filesystem:
      transport: stdio
      command: npx
      args: ["-y", "@modelcontextprotocol/server-filesystem", "."]
```

Validation checklist:

- Confirm `command` exists on `PATH` before relying on it.
- Keep credentials in environment placeholders or secrets files, not literal config values.
- Avoid mutating `args` at runtime unless the app intentionally adds session-specific roots.
- Use `allowed_tools` when the subprocess exposes tools broader than the agent needs.

### `sse`

Use for Server-Sent Events endpoints, usually ending in `/sse`.

```yaml
mcp:
  servers:
    events:
      transport: sse
      url: "https://events.example.com/sse"
      headers:
        Authorization: "Bearer ${EVENTS_TOKEN}"
      http_timeout_seconds: 30
      read_timeout_seconds: 60
```

Validation checklist:

- `url` must be HTTP(S).
- Put bearer/API tokens in `headers` unless using OAuth through `auth.oauth`.
- Set `read_timeout_seconds` high enough for idle streams.

### `streamable_http`

Use for modern HTTP MCP servers with streaming support. The connection manager can preserve MCP session IDs via the `Mcp-Session-Id` header when available.

```yaml
mcp:
  servers:
    remote_api:
      transport: streamable_http
      url: "https://api.example.com/mcp"
      headers:
        X-Client: "mcp-agent"
      terminate_on_close: false
```

Validation checklist:

- `url` must be HTTP(S).
- Use `terminate_on_close: false` only when the remote server expects sessions to persist across client disconnects.
- If OAuth is enabled, ensure the app context has a token manager; otherwise OAuth auth is skipped with a warning.

### `websocket`

Use for bidirectional WebSocket servers.

```yaml
mcp:
  servers:
    realtime:
      transport: websocket
      url: "wss://realtime.example.com/mcp/ws"
```

Validation checklist:

- `url` must be WS(S).
- Some hosted WebSocket servers encode server-specific JSON config in the URL; keep secrets out of committed URLs.

## Roots

Roots declare filesystem-like access that a server can browse or present back to an MCP client.

```yaml
roots:
  - uri: "file:///project/data"
    name: "data"
    server_uri_alias: "file:///mnt/data"
```

Rules:

- `uri` and `server_uri_alias` must start with `file://`.
- `name` is optional but improves logs and user-facing root lists.
- Use `server_uri_alias` when a containerized or remote server sees a different mount path than the client.
- Keep roots narrow; avoid granting an entire workspace if one data directory is enough.

## Registry and Connection Lifecycle

`ServerRegistry` loads `mcp.servers`, fills missing server display names from map keys, and exposes `get_server_config(...)`. It owns an `MCPConnectionManager` for persistent sessions.

Operational facts:

- `ServerRegistry.start_server(server_name, ...)` opens the configured transport and yields a `ClientSession`.
- `ServerRegistry.initialize_server(...)` additionally calls `session.initialize()` and optional init hooks.
- `MCPConnectionManager` manages long-lived connections, tracks health, and shuts down subprocess/remote transports on close.
- For streamable HTTP, connection code can propagate a session ID callback to `MCPAgentClientSession`.
- Unknown registry names raise `ValueError("Server '<name>' not found in registry.")`.

## Direct Client Usage

Use `gen_client` when a workflow or tool needs direct MCP access without building an `Agent`:

```python
from mcp_agent.mcp.gen_client import gen_client

async with gen_client("docs_api", app.context.server_registry, context=app.context) as session:
    tools = await session.list_tools()
    result = await session.call_tool("search_docs", {"query": "release notes"})
```

Use `MCPAggregator` when a workflow needs a single namespaced surface across multiple servers:

```python
from mcp_agent.mcp.mcp_aggregator import MCPAggregator

aggregator = MCPAggregator(
    server_names=["fetch", "docs_api"],
    connection_persistence=True,
    context=app.context,
    name="research_tools",
)

async with aggregator:
    tools = await aggregator.list_tools()
```

Aggregator notes:

- Tool, prompt, and resource names are namespaced by server to prevent accidental ambiguity.
- Persistent aggregators share a connection manager through the app context and reference-count cleanup.
- If tool-name collisions are still confusing to callers, reduce each server with `allowed_tools`.

## Client Installation Dry-run Guidance

Before giving a user install or client configuration commands:

1. Validate config statically with `scripts/validate_server_config.py`.
2. Check local executables with `--check-executables` when using `stdio` transports.
3. Prefer placeholders like `${TOKEN_NAME}` for secrets.
4. Confirm the target client transport matches the server runner (`stdio`, SSE URL, streamable HTTP URL, or WebSocket URL).
5. For cloud or hosted install/deploy commands, switch to `../cli-cloud-operations/SKILL.md` after this configuration passes.

Safe dry-run examples:

```bash
python sub-skills/mcp-server-integration/scripts/validate_server_config.py mcp_agent.config.yaml
python sub-skills/mcp-server-integration/scripts/validate_server_config.py mcp_agent.config.yaml --check-executables --expect-server fetch
```
