# Server Reference

## Package and Tool Contract

- Install the MCP package into the environment used by the MCP client: `pip install markitdown-mcp`.
- The console script is `markitdown-mcp`, provided by the `markitdown-mcp` distribution.
- The server exposes one MCP tool: `convert_to_markdown(uri: str) -> str`.
- `uri` may use `http:`, `https:`, `file:`, or `data:`. Route conversion behavior, format coverage, and converter exceptions to `../../core-conversion/SKILL.md`.
- The returned value is the Markdown string produced by MarkItDown for the resource described by the URI.

## CLI Transports

### STDIO

STDIO is the default and safest transport for local MCP clients because it does not bind a network socket.

```bash
markitdown-mcp
```

Use STDIO for Claude Desktop, local agent integrations, and automated checks unless the client specifically requires HTTP/SSE.

### Streamable HTTP and SSE

Use `--http` to start the Starlette/Uvicorn server with both Streamable HTTP and SSE endpoints. If omitted, the host defaults to `127.0.0.1` and the port defaults to `3001`.

```bash
markitdown-mcp --http --host 127.0.0.1 --port 3001
```

Endpoints exposed in HTTP mode:

- Streamable HTTP: `http://127.0.0.1:3001/mcp`
- SSE: `http://127.0.0.1:3001/sse`
- SSE message posts: `/messages/`

`--sse` is accepted as a deprecated alias for `--http`; prefer `--http` in new guidance. `--host` and `--port` are valid only with `--http` or `--sse`. Passing either flag with STDIO mode is a parser error.

If the explicit host is anything other than `127.0.0.1` or `localhost`, the CLI prints a security warning because the server has no authentication and runs with the current user's privileges.

## Plugin Switch

The MCP server enables MarkItDown plugins only when `MARKITDOWN_ENABLE_PLUGINS` is set to one of these case-insensitive truthy values:

- `true`
- `1`
- `yes`

Plugin packages must also be installed in the same Python environment or Docker image that runs `markitdown-mcp`. Route plugin discovery, package installation, and custom plugin authoring to `../../plugin-development/SKILL.md`; route OCR-specific plugin behavior to `../../ocr-plugin/SKILL.md`.

## Starlette App Factory

For Python embedding, the package provides `create_starlette_app(mcp_server, *, debug=False) -> Starlette`. The factory wires the MCP server into these routes:

- `/mcp` for Streamable HTTP
- `/sse` for SSE connections
- `/messages/` for SSE message posts

Minimal ASGI-style pattern:

```python
from markitdown_mcp.__main__ import create_starlette_app, mcp

app = create_starlette_app(mcp._mcp_server, debug=False)
```

Keep authentication, reverse proxies, and public gateway design outside this sub-skill. If a user needs anything beyond local trusted use, first apply the security constraints in [security-and-deployment.md](security-and-deployment.md).

## MCP Inspector

The MCP Inspector is useful for interactive debugging, not for unattended verification. Start the Inspector UI with:

```bash
npx @modelcontextprotocol/inspector
```

Connection choices:

- STDIO: choose `STDIO`, command `markitdown-mcp`, then connect.
- Streamable HTTP: start `markitdown-mcp --http --host 127.0.0.1 --port 3001` in a separate terminal, choose `Streamable HTTP`, and use `http://127.0.0.1:3001/mcp`.
- SSE: start `markitdown-mcp --http --host 127.0.0.1 --port 3001` in a separate terminal, choose `SSE`, and use `http://127.0.0.1:3001/sse`.

After connecting, list tools and run `convert_to_markdown` with a valid URI. Stop any HTTP/SSE server when debugging is complete.
