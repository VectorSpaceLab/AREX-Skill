---
name: post-training-experiments
description: "Plan and validate AReaL GRPO/PPO/SFT/DPO/RW experiments,
  Hydra-style overrides, trainer invocation, checkpoint/logging/recovery
  settings, and safe launch commands."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Post-Training Experiments

Use this sub-skill when the task is to set up or sanity-check AReaL post-training runs:
GRPO, PPO, SFT, DPO, and reward-model training.

This sub-skill helps you:
- pick the right trainer/config pair
- validate YAML + Hydra-style overrides before launch
- plan safe launch commands for local, Ray, or Slurm execution
- choose logging, checkpointing, and recovery settings
- confirm backend/GPU budget compatibility at a planning level

## When to use
- "run GRPO on GSM8K"
- "convert this PPO config"
- "validate a DPO YAML"
- "plan checkpoint/recovery settings"
- "figure out the right override syntax"

## Do not use for
- custom datasets, reward functions, or rollout/workflow authoring → [`../custom-data-rewards-workflows/SKILL.md`](../custom-data-rewards-workflows/SKILL.md)
- engine/backend internals, parallelism design, or NCCL/OOM debugging → [`../distributed-engines-backends/SKILL.md`](../distributed-engines-backends/SKILL.md)
- v2 service lifecycle, online RL sessions, or gateway operations → [`../services-cli-operations/SKILL.md`](../services-cli-operations/SKILL.md)

## Workflow
1. Identify the experiment family and trainer.
2. Validate the config with [`scripts/validate_experiment_config.py`](scripts/validate_experiment_config.py).
3. Check the launcher choice and backend/GPU plan.
4. Apply the command template from [`references/experiment-workflows.md`](references/experiment-workflows.md).
5. Verify logging, saver, and recover settings before launch.
6. If the request moves into custom data, backend, or service work, hand off to the matching sibling skill.

## Trainer map
- GRPO / PPO → `PPOTrainer`
- SFT → `SFTTrainer`
- DPO → `DPOTrainer`
- RW → `RWTrainer`

`GRPOConfig` is the backward-compatible alias of `PPOConfig`.

## Bundled references
- [`references/config-api.md`](references/config-api.md): config classes, override syntax, trainer/config mapping, migration notes, and validator output.
- [`references/experiment-workflows.md`](references/experiment-workflows.md): experiment-family recipes, launch skeletons, logging/checkpoint/recovery, and safe preflights.
- [`references/troubleshooting.md`](references/troubleshooting.md): config, dataset/trainer, algorithm, runtime launch, and metric/checkpoint failure modes.
- [`scripts/validate_experiment_config.py`](scripts/validate_experiment_config.py): safe YAML/override parser and summary helper.

## Practical rule
Do not launch training until the config validator passes and the family-specific
constraints in the bundled references are satisfied.
