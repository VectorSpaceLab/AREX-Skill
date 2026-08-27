# Troubleshooting Transport and Federation

Use this when transport behavior fails at the health, handshake, session, federation, or reflection layer.

## `GET /mcp` returns 405

Likely causes:

- The request has no `mcp-session-id` yet.
- Stateful sessions are disabled.
- The GET stream feature is disabled.
- The caller is hitting the wrong endpoint and never initialized a session.

Fix:

- Call `POST /mcp` or `POST /servers/{server_id}/mcp` to initialize first.
- Reuse the returned session id for `GET /mcp`.
- Check `/health` for the active runtime and mount.

## `GET /mcp` returns 401 on an anonymous request

Likely causes:

- Global auth is required.
- The target server has OAuth enabled, which still forces auth even when global auth is permissive.

Fix:

- Provide a bearer token.
- Confirm the server-level OAuth metadata is configured.

## `GET /mcp` looks like Python, but the runtime says Rust-managed

Likely causes:

- The runtime is in shadow mode.
- A reverse proxy is still routing the public path to the Python ingress.

Fix:

- Compare `x-contextforge-mcp-runtime-mode` and `x-contextforge-mcp-transport-mounted`.
- Do not assume Rust owns the public path just because the runtime is managed by Rust.

## Session, event-store, or affinity failures

Likely symptoms:

- 503 while claiming the listener.
- 409 because another listener already owns the session.
- Reconnect loops after Redis or event-store disruption.

Fix:

- Verify the session id is valid and consistent across requests.
- Check that the backend services needed for session ownership are reachable.
- Re-run the transport smoke after the stack recovers.

## UAID cross-gateway routing is denied

Likely causes:

- `UAID_ALLOWED_DOMAINS` is empty.
- The destination is not on the allowlist.
- The deployment is using the unsafe allow-all escape hatch incorrectly.
- The remote gateway does not trust the same issuer or cannot accept the forwarded bearer token.

Fix:

- Add only the required destination domains to the allowlist.
- Leave `UAID_ALLOW_ALL_DOMAINS` off in production.
- Confirm the remote gateway can validate the forwarded token.

## gRPC reflection fails

Likely causes:

- The target is not a valid host:port.
- TLS certificate or key paths are wrong.
- Reflection is disabled on the upstream service.
- The reflected descriptor set is too large.

Fix:

- Verify host, port, certificate, and key inputs.
- Check the upstream gRPC health endpoint or reflection capability.
- Reduce the reflection target to a smaller service if needed.

## `mcpgateway.translate` or the wrapper hangs

Likely causes:

- The transport URL is wrong.
- The endpoint needs a trailing `/mcp/` style path.
- The token or gateway URL was omitted.

Fix:

- Start from `/health`.
- Use the bundled smoke script before trying a full client bridge.
- Keep the bridge read-only until the path and auth are confirmed.
