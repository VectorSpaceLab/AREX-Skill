# MCP Server CLI Reference

The server is distributed as `strands-agents-mcp-server` and exposes a FastMCP stdio server. It has no application-specific command-line flags beyond the MCP framework's entry-point behavior; operational behavior is mostly controlled by environment variables and MCP client configuration.

## Launch choices

| Purpose | Command |
| --- | --- |
| Installed console script | `strands-agents-mcp-server` |
| Published package without a persistent install | `uvx strands-agents-mcp-server` |
| Local package module entry point | `python -m strands_mcp_server` |
| MCP Inspector against published package | `npx @modelcontextprotocol/inspector uvx strands-agents-mcp-server` |
| MCP Inspector against active package environment | `npx @modelcontextprotocol/inspector python -m strands_mcp_server` |

Use the console script or `uvx` form inside MCP client configuration. Use the module entry point when working from a checkout whose active environment already imports `strands_mcp_server`.

## Minimal MCP client shape

Most MCP clients need a stdio server definition equivalent to:

```json
{
  "command": "uvx",
  "args": ["strands-agents-mcp-server"]
}
```

Some clients add `env`, `disabled`, or `autoApprove` fields. Auto-approval is typically limited to `search_docs` and `fetch_doc`.

## Environment variables

| Variable | Values | Effect |
| --- | --- | --- |
| `STRANDS_MCP_PREFETCH_ALL` | `1`, `true`, or `yes` enable; other values disable | Starts a best-effort background hydration thread after the `llms.txt` catalog loads. Body-term search may still be title-only until hydration finishes. |
| `SKIP_INTEG_TESTS` | any set value | Causes the live integration pytest metadata to skip networked documentation tests. This is a test-control variable, not a server runtime feature. |

Client-specific logging variables such as `FASTMCP_LOG_LEVEL` may be useful when diagnosing a client/server connection, but they do not change the documented search/fetch tool contracts.

## Local checks

From an environment where the package imports:

```bash
scripts/mcp-smoke.sh
```

From a checkout with test dependencies installed:

```bash
scripts/mcp-unit-check.sh
```

To run live documentation checks intentionally, use the package's integration suite with network access available. To avoid live network checks in CI or offline work, set `SKIP_INTEG_TESTS=1` before invoking the integration suite.

## Dependency guardrail

The package declares `mcp>=1.1.3,<2.0.0` because the server imports `mcp.server.fastmcp` at module scope. If fresh installs fail at import time, check the resolved `mcp` major version before debugging server code.
