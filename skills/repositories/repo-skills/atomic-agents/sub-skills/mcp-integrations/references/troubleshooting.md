# MCP Troubleshooting

## Connector import fails after dependency resolution

**Symptom:** importing `atomic_agents.connectors.mcp` raises an import error around `streamablehttp_client`.

**Cause:** the repository source currently matches the lockfile-aligned `mcp 1.22.x` series. A newer `mcp 2.x` line renamed the streamable HTTP client symbol.

**Fix:** pin the environment to the lockfile-compatible `mcp 1.22.x` line and rerun the import smoke check.

## Endpoint formatting issues

**Symptom:** server discovery or connection fails even though the base URL looks correct.

**Cause:** the transport-specific suffix is wrong.

**Fix:**
- `HTTP_STREAM` → `.../mcp/`
- `SSE` → `.../sse`
- `STDIO` → a non-empty command string

## Persistent session errors

**Symptom:** a client session works once but fails on reuse.

**Cause:** a persistent session was created without an explicit event loop.

**Fix:** pass both `client_session` and `event_loop` into `MCPFactory`.

## Generated tool shape looks wrong

**Symptom:** the generated tool class has missing fields or an unhelpful output schema.

**Cause:** the server's JSON schema is incomplete or the fallback generic output schema was used.

**Fix:** inspect the server's schema payload, then confirm whether the server actually exposes a typed `outputSchema`.

## No server / invalid command

**Symptom:** `fetch_mcp_*` raises because there is no endpoint or the STDIO command is empty.

**Cause:** the connector surface requires an explicit endpoint or command.

**Fix:** pass a real endpoint or command string and keep the working directory explicit for STDIO runs.
