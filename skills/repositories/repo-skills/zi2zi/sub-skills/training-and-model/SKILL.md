---
name: training-and-model
description: "Train, fine-tune, and understand zi2zi's TensorFlow 1.x
  conditional adversarial U-Net, experiment layout, losses, label shuffling, and
  checkpoint monitoring."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# zi2zi training and model

Use this sub-skill when a task is about zi2zi training, fine-tuning, model
structure, loss terms, checkpoint management, or experiment diagnostics. It does
not run long training automatically; it explains the legacy workflow and gives
safe command planning and preflight checks.

## Use this sub-skill when

- The user wants to train zi2zi from `train.obj` and `val.obj`.
- The user wants to fine-tune only a subset of labels or freeze the encoder.
- The task mentions `train.py`, `experiment_dir`, `checkpoint`, `sample`,
  `logs`, `flip_labels`, `fine_tune`, `inst_norm`, `freeze_encoder`, or loss
  names such as L1, constant, category, or total variation.
- The user needs to understand why `d_loss` saturates, why label shuffling was
  added, or how checkpoints and TensorBoard outputs are organized.

## Route elsewhere

- Data rendering and `.obj` packaging go to
  [data-preparation](../data-preparation/SKILL.md).
- Inference, interpolation, and export go to
  [inference-and-export](../inference-and-export/SKILL.md).
- Cross-cutting compatibility issues go to the root
  [compatibility](../../references/compatibility.md) and
  [troubleshooting](../../references/troubleshooting.md) references.

## Core training model facts

- `UNet` is a pix2pix-like encoder/decoder generator with skip connections and
  a discriminator that predicts real/fake and style category.
- The model combines several losses: adversarial cheat loss, L1 loss, category
  loss, constant/encoding loss, and optional total variation loss.
- `flip_labels=1` enables the no-target-source branch used for label shuffling
  and saturation recovery.
- `freeze_encoder=1` excludes encoder variables from generator updates.
- `fine_tune` accepts a comma-separated list of integer labels, which the data
  provider uses to filter training and validation records.
- `inst_norm=1` switches decoder normalization to conditional instance
  normalization instead of batch normalization.

## Standard experiment layout

The README and source expect an experiment tree like this:

```text
experiment/
  data/
    train.obj
    val.obj
  checkpoint/
  logs/
  sample/
```

`train.py` creates the checkpoint, log, and sample directories if they do not
exist. Checkpoints are saved under a batch-size-specific model directory named
`experiment_<id>_batch_<batch>`.

## Recommended workflow

1. Confirm `train.obj` and `val.obj` are present and non-empty.
2. Choose `--embedding_num` large enough for the highest label in the data.
3. Decide whether you want batch norm or conditional instance norm.
4. For a normal full run, set batch size, learning rate, epoch count, and sample
  /checkpoint cadence deliberately rather than accepting defaults blindly.
5. Use `--resume=1` only when you want to continue an existing experiment.
6. Use `--fine_tune` for label-subset adaptation and `--flip_labels=1` when the
   discriminator saturates during later fine-tuning.
7. Watch TensorBoard logs and the `sample/` images for collapse or label issues.

Read [training-workflow.md](references/training-workflow.md) for command shapes,
preflight checks, and safe run-planning. Read [model-architecture.md](references/model-architecture.md)
for architecture and loss details. Read [troubleshooting.md](references/troubleshooting.md)
for TensorFlow, checkpoint, OOM, and data-layout failures.

## Bundled helper

- [scripts/plan_zi2zi_training.py](scripts/plan_zi2zi_training.py) validates a
  training command and prints the intended legacy zi2zi invocation without
  launching the TensorFlow loop.

## What not to promise automatically

- Do not promise a successful long training run without a compatible legacy
  TensorFlow environment, valid `.obj` files, and explicit runtime budget.
- Do not claim GPU verification from a CPU-only graph build.
- Do not infer checkpoint compatibility across different batch sizes,
  embedding sizes, or normalization settings without checking the variable
  names and shapes.
