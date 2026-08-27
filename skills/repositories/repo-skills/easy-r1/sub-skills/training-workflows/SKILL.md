---
name: training-workflows
description: "Configure and launch EasyR1 distributed RL post-training jobs with
  OmegaConf configs, CLI overrides, Ray/FSDP/vLLM runtime assumptions,
  algorithms, LoRA, logging, checkpoint resume, and launch troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# EasyR1 Training Workflows

Use this sub-skill when the task is to configure, lint, explain, or launch an EasyR1 RL post-training job through `python -m verl.trainer.main`.

## Start here

- [references/training-configuration.md](references/training-configuration.md): Explains the EasyR1 config hierarchy, merge order, algorithm and loss knobs, Ray/FSDP/vLLM assumptions, LoRA, logging, validation, save, and resume options.
- [references/example-launch-recipes.md](references/example-launch-recipes.md): Provides distilled launch recipes for GRPO, DAPO, Reinforce++, GSPO, CISPO, SAPO, LoRA, VL, logging, resume, and multi-node runs.
- [references/troubleshooting.md](references/troubleshooting.md): Maps common training, Ray, CUDA, vLLM, FSDP, LoRA, online filtering, logging, and checkpoint-resume failures to fixes.
- [scripts/easyr1_config_lint.py](scripts/easyr1_config_lint.py): Safely parses an EasyR1-style YAML config and reports structural, enum, batching, runtime, DAPO, and LoRA warnings without starting training.
- [scripts/easyr1_command_builder.py](scripts/easyr1_command_builder.py): Builds a shell-quoted `python -m verl.trainer.main config=... key=value...` command from a config path and CLI overrides without executing it.

## Scope boundaries

This sub-skill owns training configuration and launch decisions: OmegaConf files, CLI overrides, `python -m verl.trainer.main`, Ray resource assumptions, FSDP actor/ref/critic settings, vLLM rollout settings, GRPO/DAPO/Reinforce++/ReMax/RLOO/GSPO/CISPO/SAPO choices, LoRA launch cautions, logger selection, validation, save, and resume.

Route these tasks elsewhere in the EasyR1 skill graph:

- Dataset columns, prompt templates, reward-function implementation, Android GUI reward details, and reward smoke tests belong to `data-and-rewards`.
- `DataProto`, padding/unpadding, dynamic batching internals, and low-level algorithm tensor APIs belong to `core-apis`.
- Converting actor checkpoints to Hugging Face format or inspecting checkpoint shards belongs to `checkpoint-export`.

## Safety contract

Static config checks and command construction are CPU-safe and do not prove that a full training run will work. Full EasyR1 training requires a CUDA-capable runtime with the EasyR1 training stack, including Ray, vLLM, flash-attn, a compatible PyTorch build, sufficient GPUs, and accessible model and dataset assets.
