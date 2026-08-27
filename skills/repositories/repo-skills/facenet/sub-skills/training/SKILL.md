---
name: training
description: "Train Facenet models with softmax or triplet loss, model
  definitions, and checkpoint/log workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Facenet Training

Use this sub-skill when the user wants to train or fine-tune a Facenet model, inspect loss functions, choose a model definition, or debug checkpoints/logs from `train_softmax.py` or `train_tripletloss.py`.

## When to read

- The user asks how to run softmax or triplet-loss training.
- The task mentions `center_loss`, `triplet_loss`, `moving_average_decay`, `learning_rate_schedule_file`, `prelogits_norm`, `validation_set_split_ratio`, or `lfw_dir` inside training.
- The user wants to pick between `inception_resnet_v1`, `inception_resnet_v2`, `squeezenet`, or `dummy` model definitions.
- Training failures mention checkpoint saving, missing models, bad batch sizes, or invalid learning-rate schedules.

## Core model and loss facts

- `src/models/*` exposes `inference(images, keep_probability, phase_train=True, bottleneck_layer_size=128, weight_decay=0.0, reuse=None)`.
- `train_softmax.py` builds a classifier head over model prelogits and optionally adds center loss and prelogits norm regularization.
- `train_tripletloss.py` reshapes embeddings into anchor/positive/negative groups and uses hard-negative mining over sampled people/images.
- Both training scripts can run LFW evaluation during training when `--lfw_dir` is provided.
- `facenet.train()` wraps optimizer selection, gradient application, and moving-average tracking.

## Safe workflow

1. Read [`references/workflows.md`](references/workflows.md) for softmax/triplet training details.
2. Build a command with [`scripts/build_softmax_train_command.py`](scripts/build_softmax_train_command.py) or [`scripts/build_triplet_train_command.py`](scripts/build_triplet_train_command.py).
3. Validate the learning-rate schedule with [`scripts/validate_learning_rate_schedule.py`](scripts/validate_learning_rate_schedule.py) when `--learning_rate` is negative.
4. Confirm the data directory is aligned and class-folder structured before training.
5. Check that the selected model definition matches the intended bottleneck size and image size.
6. Treat long training, pretrained model download, and full LFW validation as user-approved operations.

## Choosing a training path

- **Softmax** is the standard classifier-style training path and is the best fit when the user wants a trainable identity classifier over many classes.
- **Triplet loss** is best when the user wants embedding learning with anchor/positive/negative sampling.
- **`dummy` model** is only for tests and smoke checks; do not use it for real training.

## Preflight checklist

Before launching a run, verify the aligned class counts, model import, image/bottleneck sizes, batch grouping, optimizer name, learning-rate schedule, log/model output permissions, and whether LFW assets are available. Start with a short bounded run only to debug the graph/control flow; do not interpret it as model quality.

## Common outputs

Training writes per-run subdirectories under the configured log/model roots, including:

- `arguments.txt`
- `revision_info.txt`
- TensorBoard event files
- checkpoint files (`model-<timestamp>.ckpt-*`)
- optional `lfw_result.txt`
- optional `stat.h5`

## Troubleshooting

Read [`references/troubleshooting.md`](references/troubleshooting.md) for invalid data layouts, bad learning-rate schedules, center-loss issues, checkpoint save problems, and expensive run warnings.
