---
name: training
description: "Training, fine-tuning, evaluation, distillation, custom COCO
  dataset setup, and distributed launch workflows for DAMO-YOLO."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# DAMO-YOLO training

Use this sub-skill when the task involves DAMO-YOLO training, fine-tuning, evaluation, distillation, dataset setup, config editing, checkpoints, or distributed CUDA launch commands.

Do **not** use this sub-skill for image/video/camera demos, ONNX/TensorRT export, partial quantization, or deployment-only backend diagnostics; route those to the inference or deployment sub-skill.

## First actions

1. Identify the workflow: train from scratch, fine-tune from detector weights, resume an interrupted run, evaluate a checkpoint, or run teacher-student distillation.
2. Read the relevant bundled references before writing commands:
   - [Training and evaluation workflows](references/training-workflows.md)
   - [Custom COCO dataset setup](references/custom-coco-datasets.md)
   - [Config editing guide](references/config-editing.md)
   - [Training troubleshooting](references/troubleshooting.md)
3. Confirm the runtime has an installed `damo` package, CUDA-enabled PyTorch, NCCL support, a user-owned config file, and any dataset/checkpoint files needed by that config.
4. Prefer a copied/edited config file for durable changes. In this repo version, nested command-line config overrides are not reliable because `Config.merge()` only replaces existing top-level attributes.
5. Use `--workdir` with bundled scripts when the config reads relative TinyNAS structure files or relative dataset paths.

## Bundled helper scripts

These scripts adapt the repository train/eval behavior into generated-skill-owned launchers. They import the installed `damo` package and do not call repo-local `tools/train.py` or `tools/eval.py`.

- `scripts/launch_train.sh`: validates config/dataset/CUDA/NCCL state, then launches bundled `train_entrypoint.py` through `torch.distributed.run`; supports single/multi-GPU runs and optional teacher args for distillation.
- `scripts/launch_eval.sh`: validates config/dataset/checkpoint/CUDA/NCCL state, then launches bundled `eval_entrypoint.py` through `torch.distributed.run`; supports `--fuse` and source-compatible parser flags.
- `scripts/validate_coco_config.py`: checks that a config, path catalog entries, annotation JSON, class names, and head class count agree before a long run.

## Operating rules

- Dataset entries are COCO-only by default. Dataset names must contain `coco` because the base config routes by substring and raises `Only support coco format dataset now!` otherwise.
- `cfg.dataset.class_names` is required. Annotation category names must match these names exactly; category ids may be non-contiguous, but they are remapped by category name into contiguous class indices.
- Training currently supports only one dataset name in `cfg.dataset.train_ann`; validation may list multiple dataset names.
- `cfg.model.head['num_classes']` must equal `len(cfg.dataset.class_names)` and match the checkpoint head whenever strict loading is used.
- `cfg.train.finetune_path` starts a new run from pretrained detector weights. `cfg.train.resume_path` restores model, optimizer, and epoch. If both are set, finetune wins in `Trainer.__init__`, so never set both for an intended resume.
- For training/eval, choose `--gpus` equal to the number of visible GPUs and make `cfg.train.batch_size` or `cfg.test.batch_size` divisible by that count.
