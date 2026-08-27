---
name: training
description: "Train LaneNet on prepared data, manage checkpoints, and debug training runs."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# LaneNet Training

Use this sub-skill when the task is to train or resume LaneNet, choose the config-driven backbone, inspect TensorBoard/checkpoints, or debug why a run produced no snapshots or unstable loss.

## Route here for

- Training on prepared TFRecords from TuSimple or custom lane data.
- Selecting the front end through `MODEL.FRONT_END` (`bisenetv2` default, `vgg` supported).
- Single-GPU vs multi-GPU behavior through `TRAIN.MULTI_GPU.ENABLE`.
- Restore-from-snapshot runs, warm-up/poly learning rate behavior, mIoU summaries, and loss inspection.
- Understanding where snapshots, TensorBoard logs, and training logs are written.

## Route elsewhere

- Raw dataset conversion or TFRecord generation: [data-preparation](../data-preparation/SKILL.md)
- Checkpoint inference, evaluation, and postprocess tuning: [inference-evaluation](../inference-evaluation/SKILL.md)
- Frozen PB or MNN export: [model-export](../model-export/SKILL.md)

## Required context before acting

1. Confirm the prepared data root contains LaneNet TFRecords, especially `tusimple_train.tfrecords` and, for multi-GPU validation, `tusimple_val.tfrecords`.
2. Confirm the runtime is CUDA-capable with TensorFlow 1.15 compatibility. That is the validated training path in this repo.
3. Confirm whether the user wants from-scratch training or restore-from-snapshot behavior.
4. Confirm the backbone and device mode. The current source uses config-driven backbone selection rather than a command-line `--net` flag.
5. Use the bundled wrapper in `scripts/train_lanenet_tusimple.py`; it resolves `REPO_ROOT_PATH` placeholders, checks the training data size, and refuses to start the no-iteration tiny-data trap.

## Key outputs

- Checkpoints under `TRAIN.MODEL_SAVE_DIR/<front_end>_lanenet/`.
- TensorBoard summaries under `TRAIN.TBOARD_SAVE_DIR/<front_end>_lanenet/`.
- Training log file under `LOG.SAVE_DIR/`.
- A copied `model_train_config.json` beside the TensorBoard event files.

## References and wrapper

- [Workflows](references/workflows.md)
- [API reference](references/api-reference.md)
- [Troubleshooting](references/troubleshooting.md)
- [Training wrapper](scripts/train_lanenet_tusimple.py)
