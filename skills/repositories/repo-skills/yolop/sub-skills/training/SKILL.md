---
name: training
description: "Guides YOLOP training, validation, evaluation metrics, staged
  multitask flags, checkpoints, auto-anchor behavior, and training smoke
  diagnostics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# YOLOP Training and Evaluation

Use this sub-skill when the task asks to train YOLOP, run validation/evaluation, change end-to-end versus staged/single-task modes, diagnose `tools/train.py` or `tools/test.py`, reason about `MultiHeadLoss`, configure auto-anchor, or interpret YOLOP detection/segmentation metrics.

Do not use this sub-skill for only preparing data roots (use `data-preparation`), running demo inference (use `inference`), or exporting ONNX/TensorRT artifacts (use `export`).

## Read first

- [references/workflows.md](references/workflows.md) gives the source training and evaluation command shapes, config fields, checkpoint behavior, and staged/single-task modes.
- [references/evaluation.md](references/evaluation.md) explains validation outputs, detection metrics, segmentation metrics, and visualization side effects.
- [references/troubleshooting.md](references/troubleshooting.md) covers data/config errors, torch-version loss issues, GPU/DDP pitfalls, batch size problems, and auto-anchor failures.
- Run [scripts/train_smoke.py](scripts/train_smoke.py) before expensive training to verify imports, model construction, forward shapes, and optionally expose loss-version incompatibilities on a tiny tensor.

## Minimal workflow

1. Validate BDD100K roots and masks with the `data-preparation` sub-skill.
2. Edit or patch `lib.config.cfg` values for dataset roots, image size, batch sizes, workers, training mode flags, pretrained checkpoint paths, and `LOG_DIR`.
3. Run a CPU or CUDA model smoke:

```bash
python sub-skills/training/scripts/train_smoke.py --repo-root /path/to/YOLOP --device cpu --image-size 128
```

4. Start training from the YOLOP checkout root:

```bash
PYTHONPATH=. python tools/train.py
```

5. For distributed training, only after a compatible CUDA torch/torchvision stack is installed and dataset/batch settings are ready:

```bash
PYTHONPATH=. python -m torch.distributed.launch --nproc_per_node=N tools/train.py
```

6. Evaluate a checkpoint:

```bash
PYTHONPATH=. python tools/test.py --weights weights/End-to-end.pth
```

## Important decisions

- All staged/single-task flags false means end-to-end multitask training.
- `TRAIN.SEG_ONLY`, `DET_ONLY`, `ENC_SEG_ONLY`, `ENC_DET_ONLY`, `DRIVABLE_ONLY`, and `LANE_ONLY` change both parameter freezing and loss components.
- `NEED_AUTOANCHOR=True` is not a cheap smoke check; it runs k-means/evolution over the training labels.
- `tools/train.py` and `tools/test.py` use the yacs config more than their parser suggests; several parsed arguments are not applied by `update_config` in the current source.
- CPU smokes validate code shape, but full training and reported paper/README metrics require real BDD100K data and practical GPU runtime.

## Cross-links

- If dataset construction fails before the model starts, switch to [../data-preparation/SKILL.md](../data-preparation/SKILL.md).
- If the trained checkpoint should be used for a demo, switch to [../inference/SKILL.md](../inference/SKILL.md).
- If the checkpoint should become ONNX or TensorRT artifacts, switch to [../export/SKILL.md](../export/SKILL.md).
