---
name: services-cli-operations
description: "Operate AReaL 2.0 service CLIs, service lifecycles, model
  registration, status/log/state inspection, Hermes online RL session/reward
  wiring, and safe command validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# AReaL Services And CLI Operations

Use this sub-skill when the task is to operate AReaL 2.0 service surfaces rather than author a new training algorithm or backend. Covered surfaces are:

- `areal inf`: inference gateway/router lifecycle, model registration, model listing, logs, status, state, and OpenAI-compatible inference endpoints.
- `areal agent`: agent-service gateway/router/worker/data-proxy lifecycle, session-affine agent calls, status, logs, and state.
- `areal train`: safe driver invocation shape for AReaL training scripts.
- Service HTTP APIs: inference, agent, training, and weight-update gateway/router/worker/data-proxy contracts.
- Online RL service wiring: start a session, route external or agent traffic through the inference gateway, set rewards, export or refresh trajectories, and shut down cleanly.

## Route boundaries

- If the user needs to write or repair an `AgentRunnable`, `AgentWorkflow`, `RolloutWorkflow`, dataset loader, reward function, or framework adapter, route to [`../custom-data-rewards-workflows/SKILL.md`](../custom-data-rewards-workflows/SKILL.md).
- If the service starts but SGLang/vLLM/FSDP/Megatron/Archon workers fail, GPUs are misallocated, weight sync hangs, CUDA/NCCL fails, or backend specs need cluster planning, route to [`../distributed-engines-backends/SKILL.md`](../distributed-engines-backends/SKILL.md).
- This sub-skill may generate commands and validate them, but bundled scripts must not start services, training, model downloads, or credentialed provider calls.

## Operating checklist

1. Identify the surface: `areal inf`, `areal agent`, `areal train`, direct service module, online RL session/reward, or weight update.
2. Read [`references/service-cli-reference.md`](references/service-cli-reference.md) for command/API contracts, state locations, config precedence, and side effects.
3. For online RL, Hermes, or self-evolution loops, read [`references/online-rl-service-recipes.md`](references/online-rl-service-recipes.md) before composing commands. Keep admin keys, agent-service keys, and `sk-sess-*` session keys distinct.
4. Validate command text before handing it to a user or scheduler:

   ```bash
   python scripts/check_service_cli.py --command 'areal inf register --model-name qwen --backend sglang:d1 --model-path /models/qwen'
   python scripts/check_service_cli.py --config service.toml --config-type inf
   ```

   The checker is static: it uses shell parsing and TOML inspection only. It does not import AReaL, contact HTTP endpoints, start services, start training, or read model files.
5. Use `areal <group> status`, `ps`, and `logs` as the first live checks once the user has confirmed that live service inspection is allowed. Use [`references/troubleshooting.md`](references/troubleshooting.md) to map symptoms to fixes.

## Safety defaults

- Treat every `run`, `register`, `deregister`, `stop`, `train run`, direct `python -m areal.v2.*` service module, and weight-update request as side-effecting.
- Never paste real API keys into generated examples; use shell variables such as `$INF_ADMIN_KEY`, `$AGENT_ADMIN_KEY`, and `$SESSION_API_KEY`.
- Do not use built-in demo keys for non-local services. For production or shared hosts, require user-provided secrets and explicit bind host/port decisions.
- Do not run native repo tests, example services, training jobs, or model downloads as part of this sub-skill. Classify those as native candidates or live operations requiring user approval.

## Bundled references

- [`references/service-cli-reference.md`](references/service-cli-reference.md) — CLI matrix, config/state/log layout, HTTP API summaries, model registration, direct module entrypoints.
- [`references/online-rl-service-recipes.md`](references/online-rl-service-recipes.md) — online proxy and Hermes/session/reward recipes with concrete request payloads.
- [`references/troubleshooting.md`](references/troubleshooting.md) — service, key, session, reward, state, port, and backend-boundary failure modes.
- [`scripts/check_service_cli.py`](scripts/check_service_cli.py) — safe static validator for service CLI commands, TOML snippets, backend specs, and quoted engine/proxy args.
