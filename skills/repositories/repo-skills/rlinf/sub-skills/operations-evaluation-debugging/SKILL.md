---
name: operations-evaluation-debugging
description: "Guides RLinf evaluation operations, metric and checkpoint
  inspection, profiling, data/checkpoint utilities, CI test selection, and
  runtime failure triage."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# RLinf operations, evaluation, and debugging

Use this sub-skill when a task asks a future agent to inspect RLinf run outputs, reason about training or evaluation logs, choose metric backends, resume from checkpoints, plan embodied evaluation, profile or auto-place a run, select safe CI/tests, use data/checkpoint utilities, or triage common runtime failures.

Do **not** start training, evaluation, Ray clusters, robot motion, downloads, or destructive data conversion just because this skill is loaded. Begin with static inspection of the user's target run directory, config tree, logs, checkpoint tree, and stated hardware/credential availability.

## Start here

1. Inspect existing outputs with [`scripts/check_run_artifacts.py`](scripts/check_run_artifacts.py). It is read-only and works from any current directory.
2. Summarize candidate YAML families with [`scripts/summarize_config_matrix.py`](scripts/summarize_config_matrix.py) before choosing an evaluation or CI matrix.
3. Use the references below to decide whether the request is an evaluation plan, resume plan, artifact audit, profiling/placement pass, utility workflow, CI selection, or troubleshooting triage.

## References

- [`references/evaluation-operations.md`](references/evaluation-operations.md) — embodied eval architecture, benchmark prerequisites, config overrides, output inspection, videos, and standalone-eval guardrails.
- [`references/metrics-checkpoints.md`](references/metrics-checkpoints.md) — TensorBoard/W&B/SwanLab logging, metric namespaces, log layout, checkpoint layouts, resume procedure, and conversion guardrails.
- [`references/data-checkpoint-utilities.md`](references/data-checkpoint-utilities.md) — replay buffer, LeRobot, dual-Franka, standalone eval, and checkpoint utility safety rules.
- [`references/debugging-and-ci.md`](references/debugging-and-ci.md) — profiling, tracing, auto-placement, parity/log analysis, static test choice, CI filter implications, and safe verification ladders.
- [`references/troubleshooting.md`](references/troubleshooting.md) — Ray/GCS, NCCL/Gloo, CUDA/OOM/offload, SGLang restore, EGL/MuJoCo/Vulkan, asset/model path, and service credential triage.

## Routing boundaries

- Initial install, Ray cluster startup syntax, node-rank environment setup, and cluster lifecycle commands belong to `setup-and-cluster`.
- Task-specific training launches and model/env YAML recipes belong to `embodied-workflows` or `reasoning-agent-workflows`.
- New source-code implementation, registry changes, new tests, Docker stages, and extension PR work belong to `extension-development`.
- This sub-skill may identify which component likely failed, which artifact is missing, and which narrow test family to run, but it should not silently convert data, delete buffers, upload metrics, or run long GPU/robot jobs without explicit user approval.

## Safe defaults

- Prefer artifact inspection, config summarization, and small unit/static checks over long e2e jobs.
- Treat real-world robot evaluation, replay-buffer mutation, checkpoint conversion, and cloud logger authentication as explicit-approval operations.
- When logs mention multiple symptoms, triage the earliest root-cause fragment first; later Gloo/NCCL timeouts are often secondary.
- Preserve user artifacts. Do not overwrite checkpoints, replay buffers, LeRobot datasets, logs, or videos unless the user explicitly requests a mutation and a backup/target path is clear.
