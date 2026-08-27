---
name: "platform-deployment"
description: "Use Unstract platform-deployment to launch, inspect, and
  troubleshoot the multi-service stack that surrounds the backend APIs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# Platform Deployment

Use this sub-skill for repository tasks about starting, wiring, or debugging the full Unstract service stack: Docker bootstrap, service entrypoints, ports, env files, and startup order.

## Owns

- `run-platform.sh` and the deployment bootstrap flow.
- `backend/entrypoint.sh`, `platform-service/entrypoint.sh`, `runner/entrypoint.sh`, `x2text-service/run.py`, and `tool-sidecar/entrypoint.sh`.
- Service-level `.env` setup, Docker / Compose prerequisites, and container start failures.
- The runtime relationships among backend, platform service, runner, x2text, sidecar, and the supporting data services.

## Excludes

- Backend route families, MCP endpoints, and Django auth internals — use `backend-platform`.
- Worker queue routing and PG-queue runtime details — use `workers`.
- Frontend route / runtime config behavior — use `frontend`.
- Shared Python package APIs and tool authoring — use `sdk-and-tools`.
- Test-group selection and critical-path coverage — use `testing-rig`.

## Start Here

Read `references/service-topology.md` first when a user asks to:

- start the full stack,
- understand which container owns a given port,
- debug an entrypoint that will not launch,
- determine which env file a service consumes,
- or reason about how the sidecar / runner / x2text pieces fit together.

Read `references/troubleshooting.md` when the problem is a launch failure, Docker issue, missing env file, or port conflict.

## Smoke Check

For deployment work, the usual safe check is the launcher help path rather than starting the stack:

```bash
./run-platform.sh --help
```

For service-specific debugging, inspect the entrypoint help or run the service in dev mode only when the supporting services are already available.

## Shared References

- `references/service-topology.md` — service map, ports, entrypoints, and launch relationships.
- `references/troubleshooting.md` — Docker, env-file, startup, and shutdown failures.
- `../references/service-map.md` — repo-wide service ownership map.
- `../references/installation-and-env.md` — install and env matrix for each service.
- `../references/repo-provenance.md` — source snapshot used to build this skill.

## Common Task Routing

| User request | Read next |
| --- | --- |
| "How do I start the stack?" | `references/service-topology.md` |
| "Which service owns this port?" | `references/service-topology.md` |
| "Why is Docker / Compose failing?" | `references/troubleshooting.md` |
| "How does x2text / sidecar / runner fit in?" | `references/service-topology.md` |
| "I changed env vars and the stack behaves oddly" | `references/troubleshooting.md` |

## Safety Boundaries

- Do not assume Docker is available or the daemon is reachable.
- Do not start services as a smoke test unless the user explicitly wants the stack booted.
- Do not send the user back to the original repository files for startup instructions; keep the launch contract inside this skill tree.
