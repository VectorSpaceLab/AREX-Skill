---
name: training
description: "Guides gaussian-splatting train.py optimization, feature flags,
  checkpoints, outputs, and training troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Training

Use this sub-skill when the task is to train, resume, configure, or debug the Python optimizer that creates a 3D Gaussian model from a prepared scene.

## Read First

- Read [references/training-workflows.md](references/training-workflows.md) for end-to-end training recipes, feature combinations, output artifacts, and resume flow.
- Read [references/cli-reference.md](references/cli-reference.md) for verified `train.py` parameter groups and defaults.
- Read [references/troubleshooting.md](references/troubleshooting.md) for CUDA/OOM/data/viewer/debug/feature failures.
- Use [scripts/build_train_command.py](scripts/build_train_command.py) to construct a command safely. It prints a command and never runs training.

## Preconditions

Before training:

1. Use [../setup-and-backends/SKILL.md](../setup-and-backends/SKILL.md) to prove CUDA, PyTorch, and custom extensions are available.
2. Use [../data-preparation/SKILL.md](../data-preparation/SKILL.md) to validate the scene layout.
3. Decide whether the network viewer should attach during training. Add `--disable_viewer` for headless/non-interactive runs.
4. Decide whether the training is for all images, evaluation split (`--eval`), depth regularization (`-d/--depths`), exposure compensation, antialiasing, or accelerated Sparse Adam.

## Primary Commands

Standard training:

```bash
python train.py -s <scene> -m <model-output> --disable_viewer
```

Evaluation split:

```bash
python train.py -s <scene> -m <model-output> --eval --disable_viewer
```

Short debugging or smoke-style run:

```bash
python train.py -s <scene> -m <model-output> --iterations 100 --test_iterations -1 --save_iterations 100 --disable_viewer --quiet
```

After training, route render/metrics tasks to [../rendering-evaluation/SKILL.md](../rendering-evaluation/SKILL.md).

## Decision Points

- Use `--data_device cpu` when large/high-resolution image tensors consume too much VRAM; training may be slower.
- Use `--resolution 1` to keep original input resolution; otherwise images wider than about 1.6K are automatically downscaled.
- Use `--checkpoint_iterations <N ...>` to save checkpoints and `--start_checkpoint <path>` to resume.
- Use the exposure preset in the workflow reference only when exposure varies and the evaluation methodology change is acceptable.
- Use `--optimizer_type sparse_adam` only after installing the accelerated rasterizer variant.

## Output Contract

A successful training run creates a model directory containing `cfg_args`, `cameras.json`, `input.ply`, `point_cloud/iteration_<N>/point_cloud.ply`, optional `chkpnt<N>.pth`, and `exposure.json`. Use the rendering-evaluation validator if a later stage cannot find these files.
