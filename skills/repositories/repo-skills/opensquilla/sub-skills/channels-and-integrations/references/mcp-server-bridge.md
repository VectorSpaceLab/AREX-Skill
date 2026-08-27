# MCP server bridge

OpenSquilla's MCP server bridge lets an MCP-capable local client call into OpenSquilla session workflows through the gateway. It is an integration surface, not a replacement for the gateway, Web UI, CLI, channels, or desktop shell.

OpenSquilla also contains MCP client code for connecting to external MCP servers over `stdio` or `sse` and registering discovered tools with an `mcp_` prefix. That is the opposite direction from `opensquilla mcp-server run`: use the distinction when debugging logs or tool names. External MCP tools still enter OpenSquilla's normal tool registry, timeout, error, permission, and sandbox boundary.

## Requirements

- OpenSquilla must be installed with the `mcp` optional extra.
- An OpenSquilla gateway must be running and reachable over the gateway websocket URL.
- The MCP-capable client must be configured to launch the bridge command as a stdio server process.

For install/gateway preconditions, route to [`../../setup-and-gateway/SKILL.md`](../../setup-and-gateway/SKILL.md). For provider/model credentials used by the sessions the bridge continues, route to [`../../configuration-and-routing/SKILL.md`](../../configuration-and-routing/SKILL.md).

## Run commands

Default local gateway:

```sh
opensquilla gateway start --json
opensquilla gateway status
opensquilla mcp-server run
```

Explicit gateway URL:

```sh
opensquilla mcp-server run --gateway ws://localhost:18792/ws
```

Environment override:

```sh
OPENSQUILLA_GATEWAY_URL='ws://localhost:18792/ws' opensquilla mcp-server run
```

The default URL is `ws://localhost:18791/ws`. The command runs FastMCP over stdio. Do not configure it as an HTTP server and do not invent `--host`, `--port`, `--transport`, `--allow-nonlocal`, mock, or benchmark flags.

## Exposed bridge surface

The server registers product-oriented tools:

| MCP tool | Purpose |
| --- | --- |
| `conversations_list` | List OpenSquilla sessions visible to the connected gateway principal. |
| `session_resolve` | Resolve a session key or identifier to session metadata. |
| `messages_read` | Read persisted messages for a session. |
| `messages_send` | Send a user message to an existing session. |
| `events_wait` | Wait for live or replayed gateway events for a session. |
| `transcript_export` | Export a session transcript as JSONL with standard tool-evidence events. |

It also registers resources:

| MCP resource | Purpose |
| --- | --- |
| `opensquilla://sessions` | Session list. |
| `opensquilla://sessions/{key}` | Session metadata. |
| `opensquilla://sessions/{key}/messages` | Session messages. |
| `opensquilla://sessions/{key}/transcript.jsonl` | JSONL transcript. |

The bridge uses gateway session RPCs, subscribes before sending a message, and preserves stream/replay sequence data where available. For session-management automation beyond the bridge boundary, route to [`../../cli-and-automation/SKILL.md`](../../cli-and-automation/SKILL.md).

## Safety posture

- Keep the gateway on loopback unless there is an explicit, secured exposure requirement.
- Do not put provider keys, channel secrets, gateway tokens, or other credentials in MCP client configuration examples.
- Treat the MCP client as another tool-calling surface. OpenSquilla permissions, sandbox posture, workspace rules, session state, and gateway authentication still matter.
- A bridge-launched `messages_send` can continue an existing session and trigger the same tools/approvals as other surfaces. Use conservative permissions for sessions that an external MCP client can reach.

## External MCP client distinction

When OpenSquilla is the **client** of another MCP server, it uses configured server entries with `transport="stdio"` plus a command/args/env, or `transport="sse"` plus an HTTP(S) SSE URL and optional message endpoint. Discovery registers tool names as `mcp_<tool_name>` and keeps clients alive for the owning runtime. Result-level MCP `isError` responses are propagated as tool errors rather than laundered into successful text.

Keep external MCP server credentials out of generated examples. For tool approval, sandbox, timeout, and execution-policy questions after discovery, route to [`../../cli-and-automation/SKILL.md`](../../cli-and-automation/SKILL.md).

## Troubleshooting

### Command says MCP dependency is missing

Reinstall or upgrade OpenSquilla with the `mcp` extra. The bridge factory raises a clear optional-dependency error when FastMCP is unavailable.

### Bridge cannot connect to gateway

Check the gateway first:

```sh
opensquilla gateway status
opensquilla doctor
```

Then verify that the MCP client command uses the websocket endpoint, not an HTTP base URL. For non-default ports use `--gateway ws://host:port/ws` or `OPENSQUILLA_GATEWAY_URL`.

### Client expects a network server

The OpenSquilla command is a stdio MCP server. The MCP-capable client should launch the command and communicate over stdio. If the client needs an HTTP/SSE server, that is outside this bridge command's current surface.

### Tool calls work but session behavior is surprising

The bridge continues OpenSquilla sessions through the gateway. Investigate the underlying session, permissions, provider config, and tool approvals using the CLI/automation sub-skill rather than changing bridge flags that do not exist.

### Transcript export looks different from raw chat history

`transcript_export` normalizes assistant tool calls and tool results into JSONL message events, preserving tool result execution status. Use it when the consuming MCP client needs standard tool-evidence events instead of OpenSquilla's raw internal message representation.
