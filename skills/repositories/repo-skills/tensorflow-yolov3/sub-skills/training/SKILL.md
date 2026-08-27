---
name: training
description: "Guides tensorflow-yolov3 YOLOv3 training setup, custom datasets,
  COCO-initialized weights, cfg.TRAIN/cfg.YOLO edits, logs, checkpoints, NaN
  fixes, and GPU/TF1 prerequisites."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Training

Use this sub-skill when a user wants to configure or run this repository's
YOLOv3 training workflow from scratch or from COCO-initialized weights, adjust
`cfg.TRAIN`/`cfg.YOLO`, diagnose dataset/class/annotation mismatches, understand
losses and checkpoints, or prepare a long TF1 training run.

Before launching `python train.py`, load these bundled references:

- [Training workflows](references/workflows.md) for from-scratch and
  COCO-initialized procedures, two-stage training behavior, monitoring, and
  output files.
- [Training API/config reference](references/api-reference.md) for exact
  `cfg.TRAIN`, `cfg.YOLO`, `Dataset`, and `YOLOV3` training contracts.
- [Training troubleshooting](references/troubleshooting.md) for missing
  checkpoints, custom class-count bugs, NaN losses, path/cwd issues, TF1/GPU
  compatibility, and data-loader edge cases.
- [Safe config checker](scripts/check_training_config.py) to validate paths,
  class files, anchors, annotation rows, input sizes, and optional checkpoint
  prefixes without importing TensorFlow or running training.

## Operating rules

1. Treat full training as expensive and state prerequisites first: a TensorFlow
   1.x-compatible Python environment, images reachable from the training working
   directory, writable `./data/log/` and `./checkpoint/`, enough GPU/CPU memory
   for the chosen `TRAIN.BATCH_SIZE` and multi-scale `TRAIN.INPUT_SIZE`, and a
   clear time budget.
2. Run or recommend the checker before training. For COCO-initialized training,
   pass `--require-checkpoint`; for intentional scratch training, omit it and
   set or tolerate a missing `TRAIN.INITIAL_WEIGHT`.
3. Keep `core/config.py` and dataset files consistent. `cfg.YOLO.CLASSES`
   determines `num_classes`, output-head width, and valid annotation class ids.
4. Remember the repo's typo: the first-stage epoch field is
   `cfg.TRAIN.FISRT_STAGE_EPOCHS`, not `FIRST_STAGE_EPOCHS`.
5. Do not imply that CPU-only checks prove throughput or convergence. CPU graph
   construction can validate APIs, but long training normally needs a compatible
   GPU stack and real data.

## Quick diagnostic command

From the repository root, validate the default training config without running
training:

```bash
python sub-skills/training/scripts/check_training_config.py \
  --repo-root . \
  --config-py ./core/config.py
```

For expected COCO-initialized training, require the checkpoint prefix:

```bash
python sub-skills/training/scripts/check_training_config.py \
  --repo-root . \
  --config-py ./core/config.py \
  --require-checkpoint
```
