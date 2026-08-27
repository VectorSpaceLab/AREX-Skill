---
name: dataset-preparation
description: "Converts and merges Luminoth object-detection datasets, validates
  source layouts, and explains TFRecord and classes.json outputs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Luminoth Dataset Preparation

Use this sub-skill when the task is to turn raw object-detection data into the
TFRecord format that Luminoth consumes, or when several TFRecord files need to
be merged into a single dataset.

## Route here for

- `lumi dataset transform` planning and troubleshooting.
- `lumi dataset merge` planning and troubleshooting.
- Choosing a reader type: `coco`, `csv`, `flat`, `imagenet`, `openimages`,
  `pascal`, or `taggerine`.
- Filtering or limiting examples with `--only-classes`, `--only-images`,
  `--limit-examples`, or `--class-examples`.
- Verifying that a source dataset layout matches the reader you want to use.
- Explaining the generated `classes.json` file and TFRecord/SequenceExample
  output layout.

## Do not use this sub-skill alone for

- Model training or evaluation after the TFRecords already exist; route to
  [training](../training/SKILL.md).
- Checkpoint packaging, aliasing, or remote checkpoint downloads; route to
  [checkpoints](../checkpoints/SKILL.md).
- Prediction, the Flask demo server, or Python inference APIs; route to
  [prediction](../prediction/SKILL.md).
- Cloud submission or TensorBoard guidance; those belong to the training
  workflow once the dataset is ready.

## Fast operating procedure

1. Read [references/workflows.md](references/workflows.md) for the transform and
   merge command shapes.
2. Read [references/data-formats.md](references/data-formats.md) when you need
   to map a source dataset type to a directory layout or annotation schema.
3. Run the bundled layout checker before writing a transform command:

   ```bash
   python scripts/validate_dataset_layout.py --type pascal --data-dir ./data --split train
   ```

4. If the task is a merge-only request, confirm that all source files are already
   TFRecords and then use the merge workflow reference.
5. If the task mixes dataset conversion with training, route the training part to
   the sibling sub-skill instead of keeping everything here.

## Common commands at a glance

```bash
lumi dataset transform --type pascal --data-dir ./data --output-dir ./out --split train
lumi dataset transform --type csv --data-dir ./data --output-dir ./out --split train --override headers=false --override columns=image_id,xmin,ymin,xmax,ymax,label
lumi dataset transform --type coco --data-dir ./data --output-dir ./out --split train --split val --only-classes=car,truck,bus
lumi dataset merge ./a/train.tfrecords ./b/train.tfrecords ./merged/train.tfrecords
```

## What this sub-skill owns

- Reader-specific layout expectations.
- `classes.json` generation alongside each TFRecord split.
- Reader overrides such as CSV column names, flat annotation keys, and other
  reader constructor arguments exposed through `--override`.
- Limiting the dataset for debugging or class balancing.
- Safe preflight checks that avoid opening the original repository checkout.

## What to delegate away

- If the source data is already converted and the user is asking about
  fine-tuning, scheduling, or evaluation, move to training.
- If the user is asking how to use a checkpoint with a finished dataset, move to
  checkpoints or prediction as appropriate.
- If the user is asking about unsupported custom readers, explain the current
  built-in readers and route the rest to training or a custom implementation
  discussion.

## Working style

Keep answers concrete: name the reader, the required split names, the source
files or directories that must exist, the output files that will be created,
and the exact flag names that matter.

When in doubt, use the bundled references and the layout checker before
specifying a command.
