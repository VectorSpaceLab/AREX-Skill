# Training workflows

## Prepare and approve the run

DeepDanbooru training consumes a project directory containing `project.json`
and `tags.txt`; `database_path` in the JSON selects the SQLite dataset. Prepare
those inputs with [project-data-setup](../../project-data-setup/SKILL.md), then
run both bundled checks from the model-training directory:

```console
python scripts/validate_project_config.py PROJECT --check-paths
python scripts/training_preflight.py PROJECT --check-packages
```

The commands are read-only. Add `--probe-imports --probe-tensorflow` to the
preflight when the installed runtime itself must be checked. A TensorFlow CPU
must be visible. A listed GPU is only discovery information; GPU support is
optional and was not verified.

The default data-path interpretation matches the training command: an absolute
`database_path` stays absolute, while a relative value is resolved from the
process working directory, not from the project directory. Prefer an absolute
path for an unattended job, or launch from a deliberately recorded working
directory.

Before allocating a long job, record:

- the project and database paths;
- the ordered tag count;
- eligible and checked row counts;
- selected model, optimizer, loss, precision, and image dimensions;
- expected epoch count and checkpoint interval;
- whether a latest checkpoint exists;
- CPU/memory/storage budget and the explicit decision to run.

## New training run

Launch only after preflight passes:

```console
deepdanbooru train-project PROJECT
```

The command performs these stages:

1. Deserialize `PROJECT/project.json`.
2. Dispatch the optimizer, optional loss-scaling wrapper, model constructor,
   and loss from exact string values.
3. Load the ordered, nonblank lines from `PROJECT/tags.txt`; this length is the
   model output dimension.
4. Construct an NHWC float32 input with shape
   `(image_height, image_width, 3)` and sigmoid multi-label outputs.
5. Compile with the configured loss plus Keras precision and recall metrics.
6. Query eligible SQLite records, create checkpoint variables, and restore the
   latest checkpoint if one exists.
7. Shuffle records deterministically for the checkpointed epoch seed, apply
   the current learning rate, train in slices, and save a checkpoint after
   every slice.
8. Advance the epoch/seed, optionally export an epoch model, then save the final
   model after the configured epoch count is reached.

Full training is skip-expensive for verification because every model is a
large convolutional network and a realistic dataset may require extensive
image decode/augmentation, CPU/GPU compute, checkpoint I/O, and model export.
A config/database preflight is not evidence of model quality or convergence.

## Initialize from a saved model

Use:

```console
deepdanbooru train-project PROJECT --source-model MODEL.keras
```

The saved model is loaded before compilation. The project model string is still
validated and still controls output filenames. Confirm that the loaded model's
input height/width/channels and output width agree with `project.json` and the
number of tags. Shape or variable mismatches otherwise emerge as TensorFlow
errors during compile, restore, or the first batch.

Existing checkpoints are restored after the source model is loaded. Therefore:

- use an empty/new `checkpoints/` directory for a genuinely new lineage;
- preserve the old directory before moving it;
- do not assume `--source-model` overrides a checkpoint;
- do not combine `--source-model` with `mixed_precision: true` in 1.0.0: the
  float32 export helper's reconstruction model is undefined on that branch,
  so periodic or final export can fail.

## Resume from checkpoints

Resume is automatic when TensorFlow's checkpoint manager finds a latest
checkpoint under `PROJECT/checkpoints/`. The checkpoint contains:

- optimizer state and model variables;
- `used_epoch`;
- `used_minibatch`;
- `used_sample`;
- `offset` within the shuffled epoch records;
- `random_seed` used for the next epoch shuffle.

The manager keeps at most three checkpoints. A slice contains
`minibatch_size * checkpoint_frequency_mb` records. After iterating that slice,
`offset` advances by the full slice size and the manager saves. Decode failures
can be removed by `ignore_errors()`, so offset and checkpoint progress do not
prove that every selected row produced a batch.

Changing image shape, tags, model structure, optimizer, or precision while
reusing checkpoints can make restoration incompatible or semantically unsafe.
Start a new project/checkpoint lineage for structural changes. A learning-rate
change is less structural, but restored optimizer state and the epoch schedule
still determine the effective value.

## Learning-rate schedule

`learning_rate` defaults to `0.001` if absent. Optional `learning_rates` is a
JSON list such as:

```json
[
  {"used_epoch": 0, "learning_rate": 0.001},
  {"used_epoch": 5, "learning_rate": 0.0001}
]
```

At each epoch, entries are visited in list order. Every entry whose
`used_epoch` is less than or equal to the current epoch replaces the current
rate, so sorted unique thresholds are the least surprising form. The selected
value is assigned to `optimizer.learning_rate`, including when mixed precision
wraps the optimizer.

## Artifacts and handoff

Periodic model names are `model-MODEL.eEPOCH.keras`; the final model is
`model-MODEL.keras`. They omit optimizer state. With mixed precision, the code
also attempts `ARTIFACT.float32.keras`, resulting in names such as
`model-resnet_custom_v2.keras.float32.keras` and
`model-resnet_custom_v2.e10.keras.float32.keras`.

Existing model files at the same names may be replaced. Use checkpoints for
resume and `.keras` files for inference or a deliberate source model. After the
run, validate at least one real image with
[inference-evaluation](../../inference-evaluation/SKILL.md), then route TFLite
or Grad-CAM work to [post-training-tools](../../post-training-tools/SKILL.md).
