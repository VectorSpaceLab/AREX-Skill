# gRPC Architecture

| Endpoint | Default | Owner | Purpose |
|---|---:|---|---|
| HTTP/A2A | `3773` | Bindu core | External A2A JSON-RPC and agent card/skills/health. |
| Core gRPC | `3774` | Bindu core | SDK calls `BinduService`. |
| SDK callback gRPC | dynamic | SDK process | Core calls `AgentHandler`. |

## Services

`BinduService` is SDK → core:

- `RegisterAgent`: config JSON, skill definitions, callback address → agent id, DID, agent URL.
- `Heartbeat`: periodic liveness for registered agent id.
- `UnregisterAgent`: cleanup registry and callback client.

`AgentHandler` is core → SDK:

- `HandleMessages`: core sends chat history; SDK calls developer handler.
- `HandleMessagesStream`: proto-declared streaming path; do not assume TypeScript support.
- `GetCapabilities`: SDK capability metadata.
- `HealthCheck`: callback server liveness.

## Registration lifecycle

1. SDK starts callback server.
2. SDK loads local skills into proto-compatible definitions.
3. SDK calls `RegisterAgent` on core `:3774`.
4. Core parses config JSON and creates `GrpcAgentClient(callback_address=...)`.
5. Core runs the same setup used by Python `bindufy()`: identity, manifest, HTTP/A2A app, storage/scheduler, optional auth/payment.
6. Core stores registry entry and returns `agent_id`, DID, and URL.
7. SDK heartbeats every 30 seconds.

## Runtime messages

External A2A request → core task manager/worker → `manifest.run(messages)` → `GrpcAgentClient` → SDK `HandleMessages` → developer handler → SDK response → worker state/artifact update.
