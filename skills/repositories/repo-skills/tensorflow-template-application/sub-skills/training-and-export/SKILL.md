---
name: training-and-export
description: "Route questions about TF1 dense and sparse training,
  checkpointing, SavedModel export, inference, TensorBoard events, and legacy
  queue/distributed notes."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Training and Export

Use this sub-skill when a user asks about:

- dense or sparse training
- checkpoint save/restore and SavedModel export
- local inference from checkpoints or exported models
- supported models, optimizers, losses, and data flags
- TensorBoard event reading
- legacy queue or distributed training variants

## Read first

- `references/model-overview.md` — model families, losses, optimizers, and export outputs.
- `references/cli-reference.md` — current flags, default modes, and README-era aliases.
- `references/workflows.md` — train/export/inference/TensorBoard recipes plus advanced notes.
- `references/troubleshooting.md` — TF1-only runtime, DuplicateFlagError, shape, export, and log issues.
- `scripts/build_training_command.py` — validates and normalizes dense/sparse commands.
- `scripts/read_tensorboard_events.py` — path-parameterized TensorBoard event inspection.

## What this sub-skill covers

- Dense `tf.data` training and sparse TFRecords training.
- Checkpointing, SavedModel export, and checkpoint-based inference.
- Supported models, optimizers, losses, and data-layout flags.
- TensorBoard scalar/event reading.
- Legacy queue and distributed notes when the user explicitly asks for them.

## Route elsewhere

- Dataset conversion, CSV/LIBSVM/TFRecords creation, and fixture generation belong to the data-preparation sub-skill.
- TensorFlow Serving clients, prediction requests, and HTTP/mobile clients belong to the serving-and-clients sub-skill.
- Cross-repo tuning, benchmark sweeps, or package installation are out of scope unless they are needed to answer a training/export question.

## Fast routing rules

- If the question is about flag names or legacy README examples, open `references/cli-reference.md` first.
- If the question is about model choices or loss/optimizer support, open `references/model-overview.md` first.
- If the user wants a safe command, use `scripts/build_training_command.py` to normalize aliases and check combinations before hand-writing the command.
- If the user wants to inspect TensorBoard output, use `scripts/read_tensorboard_events.py` against the event file or log directory.
- If the user mentions TF2, missing `tf.contrib`, or `DuplicateFlagError`, go straight to `references/troubleshooting.md`.
- Keep dense and sparse trainers in separate processes; both register `tf.app.flags` at import time.
- Dense uses `mode=train|savedmodel|inference`; sparse uses `mode=train|save_model|inference|inference_with_tfrecords`.

## Common answers this sub-skill can give

- Which dense or sparse mode to use.
- How to restore from checkpoint and export a SavedModel.
- Which model name fits a given feature layout.
- Which flag names are current versus README-era aliases.
- Why a TensorBoard log or SavedModel export failed.
