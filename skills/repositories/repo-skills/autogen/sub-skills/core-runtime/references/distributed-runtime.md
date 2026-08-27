# Distributed Runtime and gRPC Boundaries

This reference explains distributed AutoGen runtime concepts for maintenance work without requiring network services or extension packages. Concrete `autogen_ext` gRPC worker runtime setup, Docker/service operation, and package extras belong in `../extensions-integrations/`.

## Conceptual Model

AutoGen core separates application semantics from transport:

- Agents process typed messages through `AgentRuntime` operations.
- Topics and subscriptions describe event fan-out independent of whether the recipient is local or remote.
- Agent identity (`AgentId(type, key)`) must remain stable across process boundaries.
- Serializers turn message types into transport payloads; all remotely delivered messages need known serializers.
- Worker/runtime protocols define how remote workers host agent types and exchange messages.

The in-process `SingleThreadedAgentRuntime` is the best place to reproduce most logic bugs before adding distributed transport. If a problem reproduces locally, fix handler, topic, subscription, or serialization logic first.

## Boundary Checklist

Before blaming gRPC or a worker service, verify the local semantics:

1. Can the same message be handled by `SingleThreadedAgentRuntime` with the same agent type and handler annotations?
2. Does every message class have a known serializer or a schema suitable for the runtime boundary being used?
3. Do all publishers and subscribers agree on `TopicId.type`, `TopicId.source`, `AgentId.type`, and `AgentId.key` meanings?
4. Are component/provider imports available in the worker environment, not just the controller process?
5. Are protocol buffers or generated protocol files matched to the installed AutoGen package versions?
6. Are cancellation and shutdown paths explicit so workers do not keep processing after the controller exits?

## Serialization Requirements

Distributed runtimes make serialization failures more visible than local runtime tests. Watch for these patterns:

- Local-only classes or closures used as messages cannot be imported on workers.
- Dataclass/Pydantic/protobuf serializers must be discoverable for every handler target type.
- A handler registered for a union of types still needs each concrete type to serialize cleanly.
- Provider strings in component configs must import in the worker process and pass trusted-namespace checks.
- Version skew between controller and worker packages can manifest as missing fields or unknown provider names.

When debugging, reduce to one message class and one handler. Confirm the serializer/provider path before restoring the full workflow.

## Topic and Subscription Across Processes

Distributed delivery does not change topic matching semantics:

- `TypeSubscription(topic_type="x", agent_type="y")` matches `TopicId.type == "x"`.
- The recipient key is derived from `TopicId.source`.
- Direct sends still require an exact `AgentId(type="registered-type", key="instance-key")`.
- Subscription registration must happen in the runtime/worker that owns the target agent type.

If a distributed publish disappears, inspect subscription registration and topic IDs before inspecting network transport.

## gRPC and Protobuf Boundary

The design docs describe an agent worker protocol built around typed agent identifiers, topic identifiers, message payloads, and service operations. For Python maintenance:

- Treat gRPC/protobuf as transport and compatibility surfaces, not replacement APIs for `RoutedAgent` logic.
- Keep protocol version and package version aligned; avoid mixing old Magentic-One/Studio dependency pins with `autogen-core==0.7.x` in one environment.
- Do not install incompatible tooling packages into the same runtime just to inspect protocol behavior. Use separate environments or static inspection.
- Route concrete extension imports, server startup, worker registration commands, TLS/network settings, and Docker orchestration to `extensions-integrations`.

## Local-First Debugging Plan

1. Reproduce handler behavior with `SingleThreadedAgentRuntime(ignore_unhandled_exceptions=False)`.
2. Add explicit message IDs and log `AgentId`, `TopicId`, message type, and handler method.
3. Verify serializers/component configs by dumping and loading representative objects in the same environment.
4. Move the same minimal message/agent pair to the distributed runtime only after the local test is deterministic.
5. If distributed-only failure remains, compare installed package versions, generated protocol definitions, provider imports, and subscription registration on each side.

## What Not To Do

- Do not make `.NET` implementation details the target of this Python skill; use protocol concepts only when they clarify boundaries.
- Do not depend on source checkout docs, examples, or tests at runtime. Bundle any needed maintenance scripts under the skill tree.
- Do not use remote services, Docker, or open ports in a smoke test for this sub-skill; keep those checks in integration-specific verification.
