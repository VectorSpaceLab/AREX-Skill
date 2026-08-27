# Transport Surfaces

This reference summarizes the public transport and bridging surfaces this sub-skill owns.

## Public MCP ingress

- `GET /mcp` — passive session stream for the global transport.
- `POST /mcp` — MCP JSON-RPC request entrypoint.
- `DELETE /mcp` — close a session.
- `GET /servers/{server_id}/mcp` — passive stream for a virtual server.
- `POST /servers/{server_id}/mcp` — scoped JSON-RPC entrypoint.
- `DELETE /servers/{server_id}/mcp` — scoped session close.
- `/.well-known/oauth-protected-resource/servers/{server_id}/mcp` — RFC 9728 discovery for OAuth-enabled servers.

## Runtime-owned transport choices

- Python transport: standard gateway ownership.
- Rust shadow: Rust is present, but public `/mcp` still behaves like Python.
- Rust edge: the public transport can move to Rust while other runtime pieces are still mixed.
- Rust full: Rust owns the public path plus session/event-store/resume/affinity cores.

## Bridge and client workflows

- `mcpgateway.translate` bridges stdio, SSE, and streamable HTTP in both directions.
- `mcpgateway.wrapper` exposes gateway tools/prompts/resources over stdio for clients that need a local process.
- WebSocket reverse-proxy flows tunnel a local MCP server through `/reverse-proxy/ws`.
- `mcpgateway.translate` can also expose both SSE and streamable HTTP from the same stdio source.

## Federation surfaces

- Register gateways first, then bind them to virtual servers.
- Virtual servers aggregate tools, prompts, resources, and A2A agents into the client-facing catalog.
- Federation decisions should be visible in `/health` and in the scoped transport response headers.

## Safe smoke behavior

The bundled smoke script in this sub-skill only checks health and read-only transport behavior. It does not create or delete remote resources.
