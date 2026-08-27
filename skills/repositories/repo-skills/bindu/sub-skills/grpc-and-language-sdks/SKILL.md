---
name: grpc-and-language-sdks
description: "Operate Bindu's gRPC core, proto contract, and TypeScript SDK
  lifecycle for language-agnostic agents."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# gRPC and Language SDKs

Use this sub-skill for Bindu agents written outside Python: core gRPC service, SDK callback servers, `GrpcAgentClient`, shared proto fields, TypeScript `@bindu/sdk`, heartbeat/registration lifecycle, proto regeneration, and gRPC troubleshooting.

## Route elsewhere

- Python-only handler/config/A2A basics → `../agent-authoring-and-a2a/`.
- DID/Hydra/mTLS/x402 security details → `../security-identity-and-payments/`.
- Deployment/runtime-boxd/process operations → `../deployment-runtime-and-operations/`.

## References and helper

- `references/grpc-architecture.md` — two services, directions, ports, registration, registry, heartbeat, and runtime message flow.
- `references/typescript-sdk.md` — TS config/types, skill loading, callback server, response mapping, cleanup.
- `references/proto-and-regeneration.md` — proto messages, generated-code policy, regeneration commands.
- `references/troubleshooting.md` — connection, registration, timeout, callback, heartbeat, proto, streaming, and skill-content issues.
- `scripts/check_proto_regen_readiness.py` — read-only regeneration readiness check.

## Key facts

- Core gRPC defaults to `localhost:3774`; HTTP/A2A defaults to `localhost:3773`.
- SDK process owns an `AgentHandler` callback gRPC server on an explicit or auto-assigned port.
- `BinduService.RegisterAgent` accepts `config_json`, `skills`, and `grpc_callback_address`, creates `GrpcAgentClient`, and runs shared Bindu core setup in the background.
- `AgentHandler.HandleMessages` returns plain content for completion or non-empty `state`/`prompt` for open task states.
- Generated stubs are outputs. Edit `proto/agent_handler.proto`, then regenerate.
