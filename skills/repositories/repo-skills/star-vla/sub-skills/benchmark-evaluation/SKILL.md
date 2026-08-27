---
name: benchmark-evaluation
description: "Plan StarVLA simulation benchmark evaluations and two-environment
  policy-server flows without launching simulators."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# benchmark-evaluation

Use this sub-skill when a task asks how to plan, audit, or dry-run a StarVLA simulation benchmark evaluation. It covers LIBERO, SimplerEnv, RoboCasa, RoboTwin, DOMINO, BEHAVIOR, VLA-Arena, Calvin, RoboDojo, and closely related benchmark wrappers.

This skill is for safe planning. Do not start a policy server, download datasets/checkpoints, launch simulators, patch third-party repositories, or run benchmark-scale scripts unless the user explicitly asks for execution and the required environments are prepared.

## Route first

- Policy server internals, websocket/ZMQ protocol details, server response schemas, or client contract failures: [policy-deployment](../policy-deployment/SKILL.md).
- Training command construction, YAML overrides, Accelerate/DeepSpeed, checkpoint production, or resume logic: [training-config](../training-config/SKILL.md).
- Dataset registry, LeRobot modality files, data mixtures, or statistics creation: [data-integration](../data-integration/SKILL.md).
- Benchmark flow selection, two-terminal planning, simulator readiness, result/log/video expectations, and benchmark caveats: stay here.

## Operating checklist

1. Identify the benchmark family and whether the user wants planning only, a safe dry run, or actual evaluation.
2. Confirm the policy-serving environment and simulator environment are separate unless the benchmark explicitly provides a safe local mock. Actual simulator evaluations normally require two terminals/process groups: one for StarVLA policy serving and one for the benchmark client.
3. Collect placeholders before any execution: checkpoint path, host, port, device/GPU allocation, simulator project directory, benchmark data/assets, task/suite/mode, output directory, `unnorm_key`, and expected action chunk/replanning cadence.
4. Use [scripts/plan_benchmark_eval.py](scripts/plan_benchmark_eval.py) to print a safe plan for a named benchmark. This script only emits checklists; it never launches servers, downloads assets, or imports simulator packages.
5. Consult [references/evaluation-protocols.md](references/evaluation-protocols.md) for terminal roles and data contracts.
6. Consult [references/simulation-benchmarks.md](references/simulation-benchmarks.md) for benchmark-specific readiness and caveats.
7. Consult [references/troubleshooting.md](references/troubleshooting.md) for common failure triage.

## Key operating facts

- Current StarVLA websocket clients should request server-side unnormalization by passing `unnorm_key` and should consume `response["data"]["actions"]`, not hand-roll unnormalization from `normalized_actions`.
- Clients should use server metadata for `action_chunk_size` instead of recomputing it from checkpoint config. Action chunk mismatch often looks like poor policy behavior rather than a hard error.
- A checkpoint path has multiple roles: policy-server model loading, client-side run/result naming, and sometimes local access to metadata. It is not a substitute for benchmark data/assets.
- Source benchmark launchers are reference-only by default because they may start long-running servers, simulators, downloads, GPU jobs, or third-party bootstrap steps.
- If a protocol-level failure appears, stop benchmark triage and route to [policy-deployment](../policy-deployment/SKILL.md).
