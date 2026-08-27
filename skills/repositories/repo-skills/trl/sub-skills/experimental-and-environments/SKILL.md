---
name: experimental-and-environments
description: "Use TRL experimental trainers and environment-based GRPO
  integrations with stability warnings and explicit service contracts."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Experimental And Environments

Use this sub-skill when work touches `trl.experimental.*`, `GRPOTrainer(environment_factory=...)`, OpenEnv, OpenReward, Harbor, custom agent environments, or `rollout_func`-based agent training.

## Route First

- Use [experimental-trainers](references/experimental-trainers.md) for unstable trainer imports such as `trl.experimental.kto`, `ppo`, `cpo`, `orpo`, `gkd`, `gold`, `sdft`, `sdpo`, `ssd`, `tpo`, `xpo`, and other incubating trainers.
- Use [environment-training](references/environment-training.md) for OpenEnv/OpenReward/Harbor, custom environment classes, typed tool methods, reward state, and `environment_factory` vs `rollout_func` choices.
- Use [troubleshooting](references/troubleshooting.md) before debugging optional extras, warning noise, backend services, Docker/sandbox issues, credentials, concurrency, or version gates.
- Use [check_environment_integration.py](scripts/check_environment_integration.py) to inspect a candidate environment class or installed optional extras without starting training, networks, servers, or sandboxes.

## Boundaries

- Prefer the stable root `trl` APIs for normal GRPO/SFT/DPO/RM workflows; `trl.experimental` can change or disappear in any release.
- Route stable GRPO loss configuration, reward functions, dataset formatting, and trainer basics to `core-training`.
- Route vLLM memory, server/colocate backend tuning, and distributed backend setup to `scaling-and-backends`.
- Route reusable reward utilities, reward model training, or dataset reward shaping to `data-and-rewards`.
- Do not present OpenEnv/OpenReward/Harbor examples as zero-dependency local runs: they require appropriate clients, servers, credentials, sandbox backends, or optional extras.

## Required Cautions

- Importing `trl.experimental` emits `TRLExperimentalWarning` unless `TRL_EXPERIMENTAL_SILENCE=1` is set.
- `environment_factory` is itself experimental and requires `transformers>=5.2.0`; direct `tools=` requires `transformers>=5.0.0`; both need a tool-calling chat template and `jmespath`.
- OpenReward requires the `openreward` extra/SDK and typically `OPENREWARD_API_KEY` for catalog environments.
- Harbor requires the `harbor` extra, Python-compatible Harbor dependencies, vLLM for documented training flows, and a reachable sandbox backend such as Docker or E2B.
- Never assume shared public environment servers have enough concurrency for training; match server/session capacity to the generation batch size.
