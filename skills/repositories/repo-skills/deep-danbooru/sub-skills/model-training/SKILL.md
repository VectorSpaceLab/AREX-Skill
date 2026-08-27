---
name: model-training
description: "Configure, preflight, run, resume, and troubleshoot DeepDanbooru
  1.0.0 model training with a CPU-first TensorFlow workflow."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Model training

Use this sub-skill after a DeepDanbooru project and Danbooru-style dataset
exist. It covers configuration, a read-only preflight, training dispatch,
checkpoint resume, and saved-model artifacts for DeepDanbooru 1.0.0.

CPU TensorFlow is the required verified backend. GPU execution is optional and
unverified; never infer GPU readiness from device discovery or a CPU success.
Full training is intentionally **skip-expensive** during skill verification:
the ResNet variants, image pipeline, multiple epochs, checkpoint I/O, and model
exports can consume substantial compute, memory, and storage. Verify structure
and a bounded data sample first, then launch training only with an explicit
runtime and resource decision.

## Route the request

| Need | Read or run |
|---|---|
| Create `project.json`, `tags.txt`, or the SQLite/image layout | [project-data-setup](../project-data-setup/SKILL.md) |
| Validate configuration values without training | [`validate_project_config.py`](scripts/validate_project_config.py) |
| Validate config, tags, SQLite rows, image paths, checkpoints, and packages | [`training_preflight.py`](scripts/training_preflight.py) |
| Start, resume, or initialize from a saved model | [Training workflows](references/training-workflows.md) |
| Understand row selection, image paths, labels, and augmentation | [Training data pipeline](references/training-data-pipeline.md) |
| Choose a model, optimizer, loss, schedule, or precision policy | [Model and loss reference](references/model-and-loss-reference.md) |
| Diagnose empty runs, missing images, unsupported values, or resume surprises | [Troubleshooting](references/troubleshooting.md) |
| Evaluate the resulting Keras model | [inference-evaluation](../inference-evaluation/SKILL.md) |
| Convert to TFLite or create Grad-CAM output | [post-training-tools](../post-training-tools/SKILL.md) |

## Supported dispatch values

Use these exact lowercase strings in `project.json`:

- Models: `resnet_152`, `resnet_custom_v1`, `resnet_custom_v2`,
  `resnet_custom_v3`, `resnet_custom_v4`.
- Optimizers: `adam`, `sgd`, `rmsprop`.
- Losses: `binary_crossentropy`, `focal_loss`.

Any other value fails before training. The default project uses
`resnet_custom_v2`, `adam`, `binary_crossentropy`, and an image shape of
`299` by `299` with three channels. Shape order in the model is
`(image_height, image_width, 3)` even though the JSON fields list width and
height separately.

## Safe preflight

From this sub-skill directory, run:

```console
python scripts/validate_project_config.py PROJECT --check-paths
python scripts/training_preflight.py PROJECT --check-packages
```

Both helpers are read-only, deterministic, offline, and use the standard
library for configuration, filesystem, tag, and SQLite checks. They do not
launch training. Package and TensorFlow import probes are opt-in so basic
validation still works when optional runtime packages are absent.

The preflight checks a bounded, ID-ordered image sample by default. Use
`--max-image-checks 0` only when a complete filesystem scan is intended and its
I/O cost is acceptable. Use `--probe-imports --probe-tensorflow` to test the
installed modules and confirm that TensorFlow exposes a CPU; this still does
not train or verify a GPU.

Do not launch training unless all of these hold:

1. `project.json` parses and all dispatch values and numeric ranges are valid.
2. `tags.txt` is non-empty and is the intended fixed output vocabulary.
3. The SQLite `posts` table has the required columns and at least one eligible
   row at `minimum_tag_count`.
4. Derived image paths exist for the checked rows, and the image format is
   actually decodable by the training environment.
5. Checkpoint state is understood: an existing latest checkpoint causes an
   automatic resume.
6. The CPU TensorFlow environment can import DeepDanbooru, TensorFlow, and
   TensorFlow I/O.

## Launch boundary

The side-effecting command is:

```console
deepdanbooru train-project PROJECT_PATH
```

To load initial weights/model structure from an existing saved model:

```console
deepdanbooru train-project PROJECT_PATH --source-model MODEL.keras
```

`--source-model` is not a no-resume flag. After the model is loaded, any latest
checkpoint under `PROJECT_PATH/checkpoints/` is restored and can supersede its
state. Preserve or deliberately relocate checkpoints before changing training
lineage. Also confirm source-model input/output compatibility with the image
shape and number of tags; the training function does not perform a friendly
compatibility check.

## Runtime behavior to preserve

Training compiles with precision and recall metrics, shuffles records once per
epoch from a checkpointed seed, applies an optional epoch learning-rate
schedule, trains in checkpoint-sized slices, and saves after each slice.
Checkpoint state includes optimizer/model variables plus `used_epoch`,
`used_minibatch`, `used_sample`, `offset`, and `random_seed`; only the latest
three checkpoints are retained.

Periodic exports are named:

```text
model-MODEL.eEPOCH.keras
```

The final export is:

```text
model-MODEL.keras
```

Exports omit optimizer state. Resume therefore depends on `checkpoints/`, not
on a `.keras` export. `export_model_per_epoch: 0` means export every epoch;
otherwise an epoch export occurs when the completed epoch is divisible by that
positive interval.

With `mixed_precision: true`, training uses a `mixed_float16` model and a
loss-scaled optimizer, then attempts separate float32 exports ending in
`.float32.keras`. The 1.0.0 implementation reconstructs a float32 model and
restores checkpointed model variables into it. Treat those exports as needing
explicit load/inference validation. In particular, combining
`--source-model` with mixed precision leaves the float32 export model
unconstructed and can fail during export; the bundled preflight rejects that
combination.

## Failure semantics

A missing image is not reliably fatal at the dataset boundary because
`Dataset.ignore_errors()` can drop load/decode failures. A run with many bad
paths can therefore appear to progress while using fewer samples; a run with
no usable records can produce checkpoints or model files without meaningful
updates. Treat missing files, empty eligible selections, empty tag records, and
zero usable batches as failures, not warnings to ignore.

Unsupported model, optimizer, or loss strings fail during dispatch. A
`checkpoint_frequency_mb` of zero can prevent offset progress; a
`console_logging_frequency_mb` of zero causes modulo-by-zero; non-positive
batch/image/epoch values are invalid for an intended training run. Use the
validators rather than discovering these conditions after allocating a long
job.

## Handoff

After training, retain `project.json`, the exact ordered `tags.txt`, the final
`.keras` model, and any checkpoints needed for further resume. Validate the
saved model through [inference-evaluation](../inference-evaluation/SKILL.md)
before conversion or Grad-CAM work in
[post-training-tools](../post-training-tools/SKILL.md). If project/data checks
fail, return to [project-data-setup](../project-data-setup/SKILL.md) instead of
changing model hyperparameters to mask a data problem.
