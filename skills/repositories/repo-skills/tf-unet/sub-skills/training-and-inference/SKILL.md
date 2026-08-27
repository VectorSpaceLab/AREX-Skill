---
name: training-and-inference
description: "Configure tf_unet model graphs, training loops, checkpoints,
  predictions, and visual outputs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# training-and-inference

Use this sub-skill when the task is about `Unet`, `Trainer`, graph construction, losses, optimizers, checkpoints, prediction, accuracy, or image-visualization helpers.

This is the sub-skill for the TensorFlow 1.x model graph. If the task is really about input pipelines, file naming, or dataset loaders, switch to `../data-providers-and-launchers/SKILL.md`.

## Start here

- Read `references/api-reference.md` for signatures, tensor shapes, and return values.
- Read `references/workflows.md` for toy training and restore recipes.
- Run `scripts/smoke_train_restore.py` when you need a tiny train/save/restore/predict smoke.
- If the environment itself looks suspicious, run the root smoke helper `../../scripts/check_tf_unet_env.py` first.

## Core decisions

- Use `layers` and `features_root` to size the U-Net. `VALID` convolutions shrink the output and create an `offset`.
- Use `cost="cross_entropy"` for the default one-hot segmentation setup.
- Use `cost="dice_coefficient"` only when the task needs that segmentation-style objective.
- Pass `class_weights` or `regularizer` through `cost_kwargs` when the workflow needs imbalance handling or L2.
- Keep `summaries=False` for tiny inspection runs unless you explicitly want TensorBoard outputs.
- Crop labels with `util.crop_to_shape(label, prediction.shape)` before comparing against predictions.

## What to mention in answers

- The `Unet` constructor resets the default graph and prepares placeholders for `x`, `y`, and `keep_prob`.
- `Trainer.train(...)` expects a callable data provider that returns training and verification batches.
- `Trainer.train(...)` writes checkpoint and prediction outputs under the paths you provide.
- `predict(...)` restores from a checkpoint base path such as `model.ckpt`.
- `error_rate(...)` compares argmax classes across the channel axis.

## Bundled references

- `references/api-reference.md` — read for the public functions, classes, and shape contracts.
- `references/workflows.md` — read for the tiny smoke, checkpoint, and training recipes.
- `references/troubleshooting.md` — read when you hit TF1, shape, checkpoint, or loss-selection issues.

## Bundled script

- `scripts/smoke_train_restore.py` — run a one-step synthetic training flow when you want to verify the training loop and checkpoint restore path.

## Common safety notes

- Keep the smoke tiny and temporary. A long training run is not needed to answer routing or API questions.
- Do not assume TensorFlow 2 eager execution. This package is a graph/session workflow.
- If a checkpoint restore fails after changing `layers` or `features_root`, treat the checkpoint shape as stale and rebuild the graph.
