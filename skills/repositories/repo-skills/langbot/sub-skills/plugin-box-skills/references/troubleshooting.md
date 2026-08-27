# Plugin, Box, and Skills Troubleshooting

## Local Plugin Runtime Disconnects

Local stdio Plugin Runtime disconnects do not always auto-reconnect. Restart
LangBot when that path breaks. For standalone/container runtime, inspect
`plugin.runtime_ws_url`, control token configuration, and runtime logs.

## Plugin Install Fails

- Distinguish marketplace network failure from manifest/config validation.
- Check plugin id parsing and author/name paths.
- Do not expose secrets in logs or service responses.
- For SDK API failures, verify whether the change belongs in the sibling SDK.

## Box Reports No Backend

Likely causes:

- `box.enabled` false or env override disabled it.
- Docker installed but inaccessible to the current user/socket.
- `box.backend` selects a backend unavailable on the host.
- Standalone Box endpoint or control token mismatch.
- Host/container workspace root mismatch.

Use unit tests for service logic and real integration tests only after container
runtime prerequisites are confirmed.

## Skill Files Missing or Read-Only

- Box disabled can leave skill listing visible but editing/execution disabled.
- Check `box.local.skills_root` and storage fallback behavior.
- Validate path traversal and hidden-file rules before writing files.
- Run `cd skills && bin/lbs validate` after changing in-repo QA assets.

## External MCP vs LangBot MCP Confusion

External MCP servers are resources LangBot connects to and exposes to agents as
tools. LangBot's own `/mcp` server is managed by `api-mcp-web`. Keep these
separate when debugging auth, transport, or tool visibility.
