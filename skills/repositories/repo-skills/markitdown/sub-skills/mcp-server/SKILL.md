---
name: mcp-server
description: "Run and integrate the local MarkItDown MCP server with safe STDIO,
  HTTP, SSE, Docker, and Claude Desktop patterns."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# MarkItDown MCP Server

Use this sub-skill when a user wants an MCP client to call MarkItDown through `markitdown-mcp` and its `convert_to_markdown(uri)` tool. The server is intended for local trusted agents; keep it on STDIO or loopback unless the user explicitly accepts the unauthenticated file and network access risk.

## Start Here

- For CLI flags, transports, MCP Inspector, the tool contract, and Starlette embedding, read [references/server-reference.md](references/server-reference.md).
- For localhost-only deployment, Docker and Claude Desktop patterns, file mounts, and plugin environment boundaries, read [references/security-and-deployment.md](references/security-and-deployment.md).
- For command failures, invalid flag combinations, plugin setup, file access, and Inspector connection issues, read [references/troubleshooting.md](references/troubleshooting.md).
- To perform a safe local preflight without starting a server, run `python scripts/check_mcp_cli.py --transport stdio --report-plugin-env` from this sub-skill directory.

## Routing Boundaries

- Use this sub-skill for `markitdown-mcp`, MCP transports, `convert_to_markdown(uri)`, Docker or Claude Desktop MCP configuration, MCP Inspector, `create_starlette_app`, and server security posture.
- Route conversion API details, URI semantics, supported file formats, and converter exceptions to `../core-conversion/SKILL.md`.
- Route plugin discovery, installation, and custom plugin authoring to `../plugin-development/SKILL.md`.
- Route OCR-specific plugin usage to `../ocr-plugin/SKILL.md`.
- Do not design public unauthenticated deployments or authentication gateways here.

## Safe Defaults

1. Prefer STDIO: `markitdown-mcp` starts local MCP over standard input/output and does not open a listening socket.
2. For HTTP/SSE, use loopback: `markitdown-mcp --http --host 127.0.0.1 --port 3001` exposes Streamable HTTP at `/mcp` and SSE at `/sse`.
3. Treat `--host 0.0.0.0` or any non-loopback bind as a security exception because the server has no authentication and runs with user privileges.
4. Enable plugins only when the plugin packages are installed and `MARKITDOWN_ENABLE_PLUGINS` is `true`, `1`, or `yes`.
5. For Docker or Claude Desktop file conversion, mount only the directory the user intends to expose and prefer read-only mounts when conversion does not need writes.
