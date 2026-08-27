---
name: data-preparation
description: "Prepare TuSimple labels, masks, index files, and TFRecords for
  LaneNet training."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Data preparation

Use this sub-skill to turn raw TuSimple labels into LaneNet-ready masks, dataset lists, and TFRecords.

## Use when
- You have an unzipped TuSimple archive and need `training/gt_image`, `training/gt_binary_image`, `training/gt_instance_image`, and `training/train.txt`.
- You need a prepared dataset with `gt_image/`, `gt_binary_image/`, `gt_instance_image/`, `train.txt`, `val.txt`, `test.txt`, and `tfrecords/tusimple_*.tfrecords`.
- You need to fix placeholder paths such as `REPO_ROOT_PATH` or `ROOT_PATH` before TFRecord generation.

## Do not use for
- Model fitting, checkpoint management, or loss/debugging. Use the training sub-skill.
- Single-image inference, batch evaluation, or postprocess tuning. Use the inference-evaluation sub-skill.
- TensorFlow checkpoint freezing or MNN export. Use the model-export sub-skill.

## Start here
- [workflows](references/workflows.md)
- [data formats](references/data-formats.md)
- [troubleshooting](references/troubleshooting.md)

## Bundled scripts
- `scripts/generate_tusimple_dataset.py` converts raw TuSimple JSON labels into LaneNet training masks and a `training/train.txt` index.
- `scripts/make_tusimple_tfrecords.py` validates the prepared dataset layout and writes `tusimple_train.tfrecords`, `tusimple_val.tfrecords`, and `tusimple_test.tfrecords`.

## Expected outputs
- Raw conversion: `training/gt_image/`, `training/gt_binary_image/`, `training/gt_instance_image/`, `training/train.txt`, and copied label JSONs under `training/` and `testing/`.
- TFRecord stage: `tfrecords/tusimple_train.tfrecords`, `tfrecords/tusimple_val.tfrecords`, `tfrecords/tusimple_test.tfrecords`.

## Notes
- The TFRecord wrapper auto-discovers the repository root and can override the dataset root in memory.
- If the shipped sample lists still contain placeholders, regenerate or replace them before writing TFRecords.
