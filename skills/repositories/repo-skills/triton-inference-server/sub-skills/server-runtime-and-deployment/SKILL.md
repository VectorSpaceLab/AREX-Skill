---
name: server-runtime-and-deployment
description: "Plan, launch, build, deploy, observe, and troubleshoot NVIDIA
  Triton Inference Server runtime and containers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Server Runtime and Deployment

Use this sub-skill when the user asks how to run `tritonserver`, choose a container, build a custom Triton image, deploy Triton, configure readiness/metrics/tracing/logging, or debug runtime availability.

## Route Within This Sub-skill

- **Launch commands, ports, model-control mode, CPU/GPU Docker selection**: read [`references/runtime-commands.md`](references/runtime-commands.md) and use [`scripts/plan_triton_launch.py`](scripts/plan_triton_launch.py).
- **Custom images, `compose.py` style composition, source builds, Docker/Kubernetes/cloud boundaries**: read [`references/build-and-deployment.md`](references/build-and-deployment.md) and use [`scripts/plan_triton_build.py`](scripts/plan_triton_build.py).
- **Metrics, trace, logs, readiness, performance symptoms**: read [`references/observability-and-debugging.md`](references/observability-and-debugging.md).
- **Startup, port, model-load, GPU/runtime, and production failure recovery**: read [`references/troubleshooting.md`](references/troubleshooting.md).

If the problem is a model repository or `config.pbtxt`, route to [`../model-repository-and-config/SKILL.md`](../model-repository-and-config/SKILL.md). If the user is building a request payload, route to [`../client-protocols/SKILL.md`](../client-protocols/SKILL.md). If the user runs Triton's OpenAI-compatible frontend, route to [`../openai-llm-frontend/SKILL.md`](../openai-llm-frontend/SKILL.md).

## Safe Default Workflow

1. Confirm model repository path, container tag or binary source, CPU/GPU availability, backend family, and whether live Docker/service execution is approved.
2. Generate a dry-run command with `plan_triton_launch.py` before running it.
3. For CPU-only systems, omit Docker `--gpus` and warn that GPU-required model configs/backends will not load.
4. Mount model repositories read-only unless the user explicitly needs model management or polling updates.
5. Keep HTTP `8000`, gRPC `8001`, and metrics `8002` explicit in command plans and firewall/service manifests.
6. Verify readiness with `GET /v2/health/ready`; verify model status with repository index or model metadata; inspect `/metrics` only if metrics are enabled.

## Do Not Do Without Approval

- Pull large NGC images, download models, build Triton from source, run benchmarks, start production services, mutate live model repositories, or use cloud credentials.
- Treat a generated Docker command as a successful live launch.
- Claim GPU inference/metrics are verified from a CPU-only or package-import check.
