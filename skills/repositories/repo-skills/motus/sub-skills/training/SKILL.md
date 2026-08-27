---
name: training
description: "Configure, validate, launch, and resume Motus three-stage training
  on a single node or SLURM cluster without confusing fine-tuning, checkpoint
  resume, or backbone initialization."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Motus training

Use this skill when a user needs to prepare a Motus training configuration, check
it safely, construct a `torchrun`/DeepSpeed command, or reason about resuming a
run. It covers the three-stage intent, not dataset conversion or inference.

- Read [configuration.md](references/configuration.md) for the config contract,
  derived values, and checkpoint-mode rules.
- Read [workflows.md](references/workflows.md) for single-node, SLURM, and
  checkpoint export procedures. Launchers in the repository are reference-only:
  they are long-running and may submit external cluster jobs.
- Read [troubleshooting.md](references/troubleshooting.md) when validation,
  imports, CUDA, flash-attn, NCCL, logging, data, or checkpoint loading fails.
- For dataset directory/layout preparation, use the sibling
  [data-preparation skill](../data-preparation/SKILL.md). For inference, use
  [model-inference](../model-inference/SKILL.md).

## Operating procedure

1. **Identify intent before editing YAML.** Select `pretrain`, `finetune`, or
   resume. Record whether this is Stage 1 VGM training, Stage 2 Motus
   pretraining with latent actions, or Stage 3 target-robot SFT with actions.
   A checkpoint resume is a fourth *execution mode*, not a new training stage.
2. **Choose an example config.** Use `configs/latent_action.yaml` for the
   explicit `training_mode: pretrain` latent-action pipeline; use the
   embodiment config matching the dataset (`robotwin`, `ac_one`,
   `aloha_agilex_2`, or `lerobot`) for fine-tuning. Replace all example paths
   with paths valid on the target machine.
3. **Run safe checks before any launch.** Parse YAML, check the required
   sections and enum-like fields, calculate `action_chunk_size`, verify local
   dataset/checkpoint/VAE/config paths where available, and check GPU count,
   CUDA, bfloat16, DeepSpeed, and flash-attn. A parser/import check is allowed
   on CPU; model construction, VAE access, and training require CUDA and the
   large WAN/VLM checkpoints.
4. **Make checkpoint intent mutually clear.** Never set a resume checkpoint and
   a fine-tune checkpoint accidentally. Resume loads the complete Accelerator
   state and continues its step number; fine-tune partially initializes a
   `finetune` model and skips action input/decoder weights; scratch loads WAN
   and VLM backbones from `model.*.checkpoint_path`.
5. **Review the rendered command.** Check node count, GPUs per node, master
   address/port, config path, DeepSpeed JSON, logging mode, output/checkpoint
   directory, and the absence of accidental shell comments after `\\`.
   Prefer a short, bounded smoke configuration before an expensive run.
6. **Launch only with explicit approval.** `torchrun`, `sbatch`, `srun`, WAN/VLM
   downloads, and full training are external, long-running, or expensive
   operations. This skill explains and constructs them but does not silently
   execute them. Use the repository launchers only as templates; do not copy
   their placeholder paths into a public skill or run them as validation.
7. **Verify expected signals.** Rank 0 should report the selected dataset and
   training mode, checkpoint directory, logging backends, model creation,
   dataloader creation, and step/loss lines. A saved checkpoint directory
   should contain Accelerator/DeepSpeed state and the filtered `config.json`.
   Use [scripts/export_config_json.py](scripts/export_config_json.py) to create
   that JSON deliberately for an existing checkpoint directory.

## Hard boundary

This skill does not prescribe dataset layouts, conversion, or inference CLI
flags. It does not promise CPU training: Motus uses CUDA autocast and a very
large WAN/VLM stack, and the documented training requirement is more than 80
GB VRAM (typically eight 80-GB GPUs for the supplied examples). Keep missing
model checkpoints, datasets, optional packages, cluster topology, and
unverified hardware as explicit blockers rather than guessing.
