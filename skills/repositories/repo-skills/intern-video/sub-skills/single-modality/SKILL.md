---
name: single-modality
description: "Operate InternVideo2 single-modality visual workflows for
  pretraining, finetuning, probing, distillation, model selection, datasets,
  launch adaptation, and troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
  source-branch: InternVideo2-single_modality
  source-commit: 3965eef16e2dadd0ea6c8d0cc29c8a3039df52e3
license: Apache 2.0
---

# InternVideo2 Single-Modality Operating Skill

Use this sub-skill when a user asks about the visual-only `single_modality` branch of InternVideo2: masked video pretraining, action-classification finetuning, linear or attentive probing, distillation from larger teachers, model-zoo choice, dataset/weight paths, SLURM or DeepSpeed launch adaptation, or single-modality failure diagnosis.

Do not use this sub-skill for video-text/audio retrieval, chat/video-MLLM work, InternVideo3, InternVideo-Next, or InternVid dataset acquisition beyond the action-recognition annotation layouts needed here. Route those to the appropriate sibling sub-skill or root repo guidance.

## Operating protocol

1. **Classify the requested workflow.** Choose one of: pretraining, distillation, full finetuning, linear probing, attentive probing, or eval-only classification. Use [references/workflows.md](references/workflows.md) for entry points and command shapes.
2. **Collect required user inputs before executing anything expensive.** Confirm dataset split root or pretraining CSV, checkpoint/model root, desired model size, launcher (`srun`, `torchrun`, or plain `python`), GPU count, precision, and whether the user is asking for command construction only or an actual run.
3. **Check prerequisites.** Use [references/configuration.md](references/configuration.md) to verify Python/CUDA dependencies, `INTERNVIDEO2_DATA_PATH`, `INTERNVIDEO2_MODEL_PATH`, annotation CSV layout, teacher weight locations, and model registry names. Full training/evaluation requires user-provided datasets, checkpoints, CUDA-capable dependencies, and cluster resources.
4. **Generate commands safely.** Prefer the bundled helper [scripts/build_single_modality_command.py](scripts/build_single_modality_command.py) to render a dry-run command. The helper prints command text only; it has no training side effects. Review paths, GPUs, batch size, DeepSpeed flags, and dataset class before running.
5. **Adapt launchers deliberately.** Source workflows are SLURM-first and usually use DeepSpeed with BF16. For local `torchrun`, preserve distributed environment variables and port selection. For single-process debugging, remove `--enable_deepspeed`, `--dist_eval`, and large batch sizes unless the user explicitly prepared that stack.
6. **Diagnose by symptom.** Use [references/troubleshooting.md](references/troubleshooting.md) for missing CUDA extensions, teacher checkpoint failures, dataset parsing errors, stale source shell scripts, class-head mismatches, distributed hangs, and OOM recovery.

## Quick route table

| User intent | Use | Key inputs |
|---|---|---|
| Train Stage1 1B/6B visual model on K-Mash-style data | `run_pretraining.py` recipe in [workflows](references/workflows.md#pretraining) | pretraining CSV, InternVL visual teacher, VideoMAEv2-g teacher, large multi-GPU launch |
| Distill S/B/L from InternVideo2 Stage2-1B | `run_distill.py` recipe in [workflows](references/workflows.md#distillation) | K-Mash CSV, teacher checkpoint registry patched to portable paths, model size |
| Full tune on Kinetics/K400/K600/K700/MiT/SSV2/ANet/HACS | `run_finetuning.py` recipe in [workflows](references/workflows.md#full-finetuning-and-evaluation) | split root with `train.csv`, `val.csv`, `test.csv`; checkpoint; classes; frames/crops |
| Linear probe or attentive probe | `run_linear_probing.py` recipe in [workflows](references/workflows.md#linear-and-attentive-probing) | checkpoint, dataset class, `open_clip_projector`/`open_block_num`, frame schedule |
| Select checkpoint/model family | [configuration model table](references/configuration.md#model-and-checkpoint-selection) | target dataset, model scale, stage, available weights |
| Fix a run failure | [troubleshooting](references/troubleshooting.md) | first error line, command, environment summary, dataset/checkpoint existence |

## Non-negotiable boundaries

- Do not submit source shell scripts blindly. They are cluster-specific and some contain stale names or non-portable checkpoint assumptions; distill their options into a reviewed command first.
- Do not claim CPU validation proves training readiness. The selected verification for this skill is static/helper-script verification; native training and evaluation remain optional heavyweight GPU/SLURM work.
- Do not expose private machine paths, local environment prefixes, or credentials in generated commands or reports.
- Do not modify user code to patch checkpoint paths or loader bugs without explicit user approval. If a patch is needed, explain the exact portable change and why.
