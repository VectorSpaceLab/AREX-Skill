# Federation and Schema Surfaces

This reference groups the federation-oriented surfaces that create or expose remote capability catalogs.

## Gateway and virtual-server federation

- Register upstream MCP gateways first, then bind their tools, prompts, and resources into a virtual server.
- Virtual servers are the client-facing federation unit for MCP access.
- Server-scoped MCP access should be used when the caller needs the catalog of one virtual server only.
- Connectivity tests for gateway registration are read-only probes, not catalog mutations.

## A2A agent federation

A2A agents can be registered, updated, enabled/disabled, invoked, and exposed through MCP discovery.

Common surfaces:

- `/a2a`
- `/a2a/{agent_id}`
- `/a2a/{agent_id}/state`
- `/a2a/{agent_name}/invoke`
- `/a2a/{agent_name}/jsonrpc`
- `/a2a/tasks/get`
- `/a2a/tasks/list`
- `/a2a/tasks/cancel`
- `/a2a/push/create`
- `/a2a/push/get`
- `/a2a/push/list`
- `/a2a/push/delete`
- `/a2a/events/flush`
- `/a2a/events/replay`
- `/a2a/agents/{agent_name}/resolve`
- `/a2a/agents/{agent_name}/card`

A2A federation notes:

- Tasks and push configs are persisted server-side so later reads can reconstruct state.
- A2A agents can be surfaced as MCP tools on virtual servers.
- UAID routing must stay allowlist-driven.
- Cross-gateway calls should forward bearer tokens only when the deployment explicitly allows it and both gateways trust the same issuer.
- `UAID_ALLOW_ALL_DOMAINS=true` is a development-only escape hatch and is unsafe for production.

## gRPC reflection and schemas

gRPC services are discovered by reflection and translated into MCP tools.

Key points:

- Service targets are validated as host:port addresses.
- TLS and mTLS use validated certificate and key paths.
- Reflection extracts service and method descriptors, then stores tool schemas.
- Reflected tools carry `x-grpc-input-type`, `x-grpc-output-type`, `x-grpc-client-streaming`, and `x-grpc-server-streaming` metadata.
- Descriptor count and size are bounded before the reflected schema is accepted.
- If reflection is unavailable, the service can still invoke methods when a descriptor pool is already cached.

## Safe focus

This reference is about federation surfaces and schema derivation. It does not own the detailed CRUD payload shapes for registry admin pages.
