---
name: training
description: "Routes Ultra-Fast-Lane-Detection training, checkpoint, resume,
  finetune, and multi-GPU launch workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# training

Use this sub-skill when a task is about fitting the lane detector: choosing optimizer and scheduler settings, launching single-GPU or distributed training, resuming checkpoints, or understanding how the repo logs and saves models.

## Read this when

- You need to start a training run from `train.py`.
- You need to resume or finetune from a checkpoint.
- You need to translate the repo's shell launcher into a safer command.
- You need to explain the repo's losses, metrics, or checkpoint naming.

## What this sub-skill owns

- Training command construction.
- DDP/NCCL launch advice.
- Optimizer, scheduler, loss, and metric selection.
- Checkpoint save/resume/finetune behavior.
- TensorBoard logging and code-backup side effects.

## What it does not own

- Dataset root preparation and TuSimple conversion: see `data-and-config`.
- Evaluation, scoring, and demo output files: see `evaluation-and-visualization`.
- TorchScript export and benchmark timing: see `export-and-speed`.

## Start here

- Read `references/training-workflows.md` for the practical command patterns.
- Read `references/api-reference.md` for verified function signatures and model dimensions.
- Read `references/troubleshooting.md` for CUDA, checkpoint, and launch failures.
- Run `scripts/model_cuda_smoke.py` when you need a quick proof that the model can build and run on CUDA.
- Use `scripts/launch_training_template.sh` as the safer replacement for the repo's raw launch shell snippet.

## Typical flow

1. Pick the dataset family and matching config from `data-and-config`.
2. Decide whether the run is single-GPU or distributed.
3. Set `data_root`, `log_path`, and any checkpoint path overrides explicitly.
4. Confirm the backbone, `griding_num`, `num_lanes`, and `use_aux` match the chosen dataset family.
5. Start the run and keep the logs outside the repository tree.

## Caution points

- The source training loop calls `.cuda()` directly.
- The launcher assumes NCCL for multi-GPU runs.
- `cp_projects` can copy a large working tree if `log_path` points at a directory inside the repo.
- The checkpoint filename convention matters for resume logic.

## Reference and script links

- `references/training-workflows.md` for the command patterns and checkpoint lifecycle.
- `references/api-reference.md` for the verified signatures.
- `references/troubleshooting.md` for launch, CUDA, and checkpoint problems.
- `scripts/launch_training_template.sh` for a parameterized shell launcher.
- `scripts/model_cuda_smoke.py` for a small model/build smoke check.
