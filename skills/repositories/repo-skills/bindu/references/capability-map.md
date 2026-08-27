# Capability Map

| Capability family | Sub-skill owner | Key bundled references | Verification evidence |
|---|---|---|---|
| Python agent authoring and A2A task lifecycle | `agent-authoring-and-a2a` | API reference, A2A lifecycle, skills/negotiation, troubleshooting | `bindufy` signatures, CLI help, selected unit tests for config and task manager |
| Security, identity, private catalogs, mTLS, x402 | `security-identity-and-payments` | security stack, auth/DID, x402, private skills/mTLS, troubleshooting | DID signing helper, security docs/source, selected unit tests; live services optional |
| gRPC core and TypeScript SDK | `grpc-and-language-sdks` | gRPC architecture, TS SDK, proto/regeneration, troubleshooting | proto readiness helper, generated-code policy, selected unit/integration gRPC tests |
| CLI, runtime, storage, scheduler, observability, repo operations | `deployment-runtime-and-operations` | CLI/runtime, storage/scheduler/observability, source packaging/secrets, repo maintenance | runtime preflight helper, CLI help, selected runtime/source-packager tests |
| Gateway, Inbox, recipes, orchestration | `gateway-inbox-and-orchestration` | gateway workflows, inbox workflows, recipes/auth, troubleshooting | request-template helper, optional Node tests, source-script inventory |

## Cross-skill workflow examples

- **Create a paid TypeScript agent**: start with `grpc-and-language-sdks`, cross-link to `security-identity-and-payments` for `execution_cost`, and use `deployment-runtime-and-operations` for deploy/dry-run.
- **Debug a caller seeing auth errors**: use `security-identity-and-payments` for 401/403/DID/x402 meaning; use `agent-authoring-and-a2a` if the A2A request body or task state is malformed; use `gateway-inbox-and-orchestration` if Gateway/Inbox is the caller.
- **Ship a local Python agent**: use `agent-authoring-and-a2a` for code/config, then `deployment-runtime-and-operations` for `bindu serve` or `bindu deploy`.
- **Plan across multiple agents**: use `gateway-inbox-and-orchestration` for peer catalog and Gateway auth, then jump into sibling sub-skills for peer-specific Bindu server behavior.

## Optional services and credentials

Bindu can integrate with external systems: Hydra, step-ca, x402 facilitators/blockchains, Postgres, Redis, boxd, OpenRouter, Sentry, OTLP collectors, and tunnels. This skill treats them as optional service dependencies unless the user's task explicitly provides or requests them. Use dry-runs, help, import checks, and mocked/tiny fixtures before live service calls.
