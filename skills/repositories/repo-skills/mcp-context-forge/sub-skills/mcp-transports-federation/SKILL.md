---
name: mcp-transports-federation
description: "Operate ContextForge transport, federation, and runtime surfaces:
  streamable HTTP /mcp and /servers/{server_id}/mcp, SSE/WebSocket/stdio
  bridges, virtual-server and gateway federation, A2A/UAID routing, gRPC
  reflection, and Rust mode diagnostics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# MCP Transports and Federation

Use this sub-skill for transport-layer and federation work across the gateway: public MCP ingress, virtual servers, bridge workflows, A2A federation, gRPC reflection, and Rust runtime mode checks.

## Route Here For

- Registering MCP servers and gateways, creating virtual servers, and exposing tools, prompts, and resources over MCP.
- Operating streamable HTTP at `/mcp` and `/servers/{server_id}/mcp`, including session bootstrap, GET stream behavior, and teardown.
- Bridging stdio ↔ SSE ↔ streamable HTTP with `mcpgateway.translate` or the stdio wrapper.
- Using WebSocket reverse-proxy flows when a client needs a socket tunnel instead of direct HTTP.
- Managing A2A agents, task state, push notification configs, UAID cross-gateway routing, and agent federation.
- Discovering gRPC services via reflection and turning reflected methods into MCP tool schemas.
- Checking Rust/Python public MCP ownership, session/event-store/affinity health, and runtime mode drift.

## Reroute

- Registry CRUD schemas, object payload validation, and admin-form field details: `registry-admin-api`.
- Token scoping, RBAC, session auth, and access-control decisions: `auth-rbac-security`.
- Plugin hook side effects, header mutation, and tool/post-fetch observability: `plugins-observability`.
- Choosing the overall repo validation gate or broadening from a transport-only check: `development-validation`.

## Fast Path

1. Inspect `/health` first. Confirm `x-contextforge-mcp-runtime-mode` and `x-contextforge-mcp-transport-mounted` before deciding which runtime is active.
2. Distinguish the two public MCP paths:
   - `/mcp` for the global transport.
   - `/servers/{server_id}/mcp` for a scoped virtual server.
3. Remember that `GET /mcp` is a passive session stream. It needs an initialized session id and an SSE-capable client; it is not the bootstrap request.
4. Use `scripts/contextforge_mcp_smoke.py` for a read-only health + transport smoke check. It stays off create/update/delete flows.
5. If the question is about translation or local client bridging, open `references/transport-surfaces.md` first.
6. If the question is about Rust ownership, shadow/edge/full behavior, or `GET /mcp` changing hands, read `references/runtime-modes.md` next.
7. If the question is about A2A/UAID or gRPC reflection, use `references/federation-and-schema.md` before debugging the service layer.
8. If the symptom is a failure, start with `references/troubleshooting.md`; only then move to the validation matrix.

## What This Skill Must Preserve

- `MCP_REQUIRE_AUTH=false` only opens public-only access on non-OAuth servers. A server with `oauth_enabled=True` still rejects unauthenticated callers.
- Health headers are the source of truth for runtime ownership. A `rust-managed` runtime can still have the public transport mounted on Python in shadow mode.
- `GET /mcp` should fail closed on a missing session id, a wrong endpoint, a disabled stream, or a missing listener claim.
- UAID cross-gateway routing must be allowlist-driven and fail closed when the target domain is not approved.
- gRPC reflection must reject invalid targets, bad TLS paths, and oversized descriptor sets before tool generation.
- Live gateway transport tests are optional final candidates and require running services.

## Reference Map

- `references/transport-surfaces.md`
- `references/runtime-modes.md`
- `references/federation-and-schema.md`
- `references/troubleshooting.md`
- `references/validation.md`
- `references/source-script-inventory.md`
- `scripts/contextforge_mcp_smoke.py`

## Operating Notes

- Prefer read-only probes first: `/health`, `initialize`, `list_tools`, `list_resources`, `list_prompts`, A2A card/task reads, and gRPC reflection discovery.
- Keep any live checks safe by default. Do not add create/update/delete steps unless the task explicitly asks for them.
- If the issue turns out to be token scope, RBAC, plugin hook behavior, or a broad validation decision, hand off to the matching sibling skill instead of stretching this one.
