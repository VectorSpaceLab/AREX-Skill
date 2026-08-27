---
name: training-and-configs
description: "Plan detrex LazyConfig training, evaluation, dataset, launcher,
  and runtime override workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# detrex training and configs

Use this sub-skill when the task involves launching, adapting, or debugging detrex training/evaluation commands or Python LazyConfig files.

## Route here when

- The task mentions `tools.train_net`, `hydra_train_net`, `LazyConfig`, `get_config`, `train.max_iter`, `train.init_checkpoint`, command overrides, or `DETECTRON2_DATASETS`.
- The user needs a train, eval-only, resume, fast debug, multi-GPU, multi-machine, Hydra, or submitit/Slurm command plan.
- The user is changing datasets, dataloaders, optimizers, schedulers, DDP fields, AMP, EMA, WandB, checkpoints, output directories, or custom backbones.
- The user is deciding whether a project-specific trainer such as DINO or CO-MOT is required instead of the generic detrex trainer.

## Fast route

1. Read [references/configuration.md](references/configuration.md) when the task is about config namespaces, common fragments, dataset names, optimizers/schedules, AMP, EMA, WandB, DDP, or custom backbone wiring.
2. Read [references/training-workflows.md](references/training-workflows.md) when the task is about train/eval commands, resume, fast debug, distributed launch, Hydra/submitit, project trainers, datasets, or output directories.
3. Run [scripts/build_train_command.py](scripts/build_train_command.py) with `--help` before constructing commands. The helper only prints commands; it never launches training or downloads assets.
4. Read [references/troubleshooting.md](references/troubleshooting.md) when imports, datasets, CUDA, ports, checkpoints, config paths, logging, Hydra, or trainer selection fails.

## Operating rules

- Prefer command construction and config inspection before expensive jobs. Do not start long training/evaluation without explicit user approval, available data, intended checkpoint paths, and suitable backend resources.
- Use `DETECTRON2_DATASETS` or a user-defined dataset registration before claiming a COCO-style command is runnable.
- Use `train.fast_dev_run.enabled=True` for a short smoke/debug path; it changes `max_iter`, `eval_period`, and `log_period` inside the trainer.
- Treat DINO, CO-MOT, and similar project-specific trainer files as separate workflow contracts when they change optimizer grouping, data movement, or model-specific assumptions.
- Do not download datasets, checkpoints, or pretrained backbones by default. Use user-provided local paths unless the user explicitly authorizes downloads.
- Keep full native training/evaluation tests out of routine guidance; use dry-run command building, config loading, and explicit preflight checks first.

## Quick command builder examples

```bash
python scripts/build_train_command.py \
  --config-file user_configs/dab_detr_r50_50ep.py \
  --num-gpus 8 --fast-dev-run
```

```bash
python scripts/build_train_command.py \
  --eval-only --config-file user_configs/dino_r50_4scale_12ep.py \
  --checkpoint weights/dino_r50_4scale_12ep.pth \
  --override train.device=cuda
```

```bash
python scripts/build_train_command.py \
  --launcher hydra --config-file user_configs/detr_r50_300ep.py \
  --num-gpus 8 --auto-output-dir --override model.num_queries=50
```

The helper prints the command and non-fatal warnings; it does not execute the training loop.
