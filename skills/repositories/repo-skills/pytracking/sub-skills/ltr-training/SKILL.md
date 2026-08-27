---
name: ltr-training
description: "Configure, launch, and modify PyTracking LTR training settings for
  ATOM, DiMP/PrDiMP, KeepTrack, KYS, LWL, RTS, TaMOs, and ToMP."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# LTR training operating skill

Use this sub-skill when the task is to configure, inspect, launch, resume, or modify the LTR training stack in a PyTracking checkout. It covers `run_training`, `train_settings` module/name pairs, local training configuration, datasets, data processing/sampling/loading, actors, trainers, models, checkpoints, TensorBoard, CUDA, and training-only optional dependencies.

## Route elsewhere

- Runtime tracker execution, video/webcam/dataset evaluation, dataset alias selection, Visdom/debug behavior, and result directories belong to `tracking-evaluation`.
- Implementing a new runtime tracker class, parameter file, or tracker registry layout belongs to `tracker-development`.
- Result plotting, benchmark result packaging, VOT integration, and raw-result analysis belong to `analysis-and-packaging`.

## Start here

1. Read [references/workflows.md](references/workflows.md) for setup, command construction, launch/resume, TensorBoard, and safe modification workflows.
2. Read [references/training-settings.md](references/training-settings.md) to choose the valid `train_module` / `train_name` pair and identify datasets/checkpoints required by each family.
3. Read [references/data-and-model-api.md](references/data-and-model-api.md) before editing a setting file, adding a dataset, replacing a model, changing a sampler, or changing an actor/loss/trainer path.
4. Use [scripts/build_training_command.py](scripts/build_training_command.py) to validate available training settings and print a command. The script scans a target checkout and never launches training.
5. Use [references/troubleshooting.md](references/troubleshooting.md) for `local.py`, dataset path, checkpoint, CUDA/OOM, TensorBoard, PreciseRoIPooling, and KYS correlation-sampler failures.

## Quick command builder usage

From a PyTracking checkout:

```bash
python skills/disco/pytracking/sub-skills/ltr-training/scripts/build_training_command.py --list
python skills/disco/pytracking/sub-skills/ltr-training/scripts/build_training_command.py bbreg atom
python skills/disco/pytracking/sub-skills/ltr-training/scripts/build_training_command.py tomp tomp50 --no-cudnn-benchmark
```

The default output is a shell command in the source style, for example `python ltr/run_training.py bbreg atom`. With `--no-cudnn-benchmark`, the helper emits a Python API one-liner because the source CLI parses boolean strings unsafely; do not replace it with `--cudnn_benchmark False` unless you have fixed the parser.

## Operating invariants

- Training is long-running and dataset/checkpoint dependent. Do not start full epochs unless the user explicitly requested execution and required data, workspace, checkpoints, CUDA/backend, and budget are available.
- `train_module` is the subdirectory under `ltr/train_settings`; `train_name` is the Python file stem in that subdirectory. Validate against the checkout instead of relying on prose examples.
- A writable local training configuration is mandatory. At minimum configure `workspace_dir`, `tensorboard_dir`, `pretrained_networks`, and every dataset path used by the selected setting.
- Checkpoints are saved under the configured workspace in a project path shaped like `ltr/<train_module>/<train_name>`; TensorBoard logs use the same project path under the configured TensorBoard directory.
- Most settings assume CUDA and large tracking datasets. Some settings set `multi_gpu=True`; some compute batch size from `torch.cuda.device_count()`. Adjust settings intentionally for CPU-only or single-GPU dry work.
