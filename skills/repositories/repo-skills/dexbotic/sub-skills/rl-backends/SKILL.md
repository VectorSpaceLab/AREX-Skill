---
name: rl-backends
description: "Integrate Dexbotic policies with SimpleVLA-RL or RLinf as external
  reinforcement-learning backends while preserving clear runtime boundaries."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Dexbotic RL backends

Use this route only when the task is RL post-training or an RLinf model/registry adapter. Dexbotic owns model definitions, policy adapters, and Hydra-facing configs; SimpleVLA-RL or RLinf owns distributed rollout/training services. Standard SFT belongs to [training](../training/SKILL.md), serving to [inference-serving](../inference-serving/SKILL.md), and simulator installation remains external.

## Operating sequence

1. Identify the frontend: Dexbotic-side entrypoint or external RLinf frontend. Do not mix their launch contracts.
2. Confirm the external runtime, embodied environment, accelerator, cluster launcher, checkpoint paths, and config composition are installed and compatible. Core Dexbotic imports do not prove RL readiness.
3. For RLinf backend mode, register the model in the driver and worker processes, usually through the configured extension-module hook, then validate the Hydra config before cluster creation.
4. Start with a config/registry inspection or `--help`; do not launch rollouts, Ray workers, simulator environments, or long RL training as a default verification.
5. Keep checkpoint/action/norm-stat contracts consistent between SFT and RL adapters. Record the backend marker and exact suite/config in logs.

Missing RLinf, simulator, or vendor packages is an explicit optional-unverified limitation, not a core Dexbotic failure.
