---
name: advanced-rl-distributed
description: "Plan and debug advanced ms-swift RLHF, GRPO/GKD, rollout, Ray, and
  Megatron distributed workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Advanced RL and Distributed Execution

Use this sub-skill when the task involves advanced preference optimization, GRPO rollout orchestration, custom rewards/plugins, Ray scheduling, or Megatron-SWIFT distributed execution in ms-swift.

## Route Here For

- `swift rlhf` with `--rlhf_type grpo`, `gkd`, `ppo`, `dpo`, `kto`, `rm`, `cpo`, `simpo`, or `orpo` when the task asks for RLHF mechanics, reward behavior, rollout placement, or advanced algorithm options.
- `swift sample` and `swift rollout` when sampling, PRM/ORM filtering, rollout servers, vLLM weight sync, or multi-turn rollout servers are part of an RL plan.
- `megatron rlhf`, `megatron sft`, `megatron export`, Ray YAML configs, Mcore-Bridge, TP/PP/CP/EP/VPP, sequence parallel, and multi-node launch debugging.
- Custom GRPO reward functions, async rewards, reward models, multi-turn schedulers, gym environments, and plugin registration.

## Reroute Instead

- Basic SFT/pretraining command construction belongs in the sibling training sub-skill.
- Dataset field conversion, custom data schemas, and template/data registration belong in the sibling data-model-customization sub-skill.
- Inference, serving, and deployment belong in the sibling inference-deployment sub-skill, except when the server is a GRPO rollout server.
- Export and standalone evaluation belong in the sibling export-evaluation sub-skill, except Megatron conversion choices needed for RL training.

## Required Reads

- [RLHF and GRPO workflows](references/rlhf-grpo-workflows.md) for algorithm choice, `swift rlhf`, reward/plugin patterns, sampling, rollout servers, and multi-turn guidance.
- [Ray and Megatron workflows](references/ray-megatron-workflows.md) for Megatron-SWIFT, Ray configs, Mcore-Bridge, parallelism dimensions, and hardware placement.
- [Troubleshooting](references/troubleshooting.md) for missing extras, reward field pass-through, rollout placement, Ray JSON/YAML, torchrun variables, and Megatron shape/parallel errors.
- [RLHF command builder](scripts/build_rlhf_command.py) to produce safe command or Ray YAML skeletons without executing training.
- [Optional backend checker](scripts/check_optional_backends.py) to report CLI/module availability for Ray, Megatron, Mcore-Bridge, vLLM, LMDeploy, SGLang, evalscope, and CUDA without requiring GPUs.

## Fast Decision Guide

| User Need | Start With | Key Checks |
| --- | --- | --- |
| GRPO with custom rewards | `swift rlhf --rlhf_type grpo` | `num_generations >= 2`, reward names registered, required dataset columns passed through |
| External rollout server | `swift rollout` plus `swift rlhf --vllm_mode server` | host/port/base URL, `--vllm_server_pass_dataset true` for multi-turn/env rows |
| Megatron GRPO/GKD | `megatron rlhf` | optional Megatron stack, TP×PP×CP divisibility, completion-level batch formulas |
| Ray Megatron GRPO/GKD | `megatron rlhf --use_ray true --config CONFIG.yaml` | `train`, `rollout`, optional `teacher` GPU groups, colocate vs separate mode |
| Sampling/RFT data generation | `swift sample` | sampler engine, PRM/ORM memory split, cache file pass, plugin registration |

## Optional Dependency Caveats

A minimal ms-swift install can expose the base `swift` routes while advanced backends remain absent. Treat missing `ray`, `megatron-core`, `mcore-bridge`, `transformer-engine`, `apex`, `flash-attn`, `vllm`, `lmdeploy`, `sglang`, or `evalscope` as optional capability gaps to solve only for the requested workflow. For Megatron-SWIFT, install the Megatron extra and a compatible Megatron-style stack such as `pip install "ms-swift[megatron]" -U`, then validate with the backend checker before planning GPU-heavy commands.
