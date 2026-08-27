# LaneNet workflow overview

This overview helps choose the right sub-skill before opening deeper references.

## 1. Prepare TuSimple data

Use the **data-preparation** sub-skill when you start from raw TuSimple labels or a partially prepared lane dataset.

Typical path:

1. Convert `label*.json` files into `training/gt_image/`, `training/gt_binary_image/`, and `training/gt_instance_image/`.
2. Generate or normalize `train.txt`, `val.txt`, and `test.txt` rows.
3. Write `tfrecords/tusimple_train.tfrecords`, `tfrecords/tusimple_val.tfrecords`, and `tfrecords/tusimple_test.tfrecords`.

Owner: [data-preparation](../sub-skills/data-preparation/SKILL.md)

## 2. Train LaneNet

Use the **training** sub-skill when the dataset is ready and the next step is checkpoint production.

Typical path:

1. Confirm the TFRecords exist and the training batch size is realistic for the dataset size.
2. Choose the backbone through `MODEL.FRONT_END`.
3. Run the single- or multi-GPU trainer based on `TRAIN.MULTI_GPU.ENABLE`.
4. Inspect checkpoints, TensorBoard summaries, and the saved `model_train_config.json`.

Owner: [training](../sub-skills/training/SKILL.md)

## 3. Run inference or evaluation

Use the **inference-evaluation** sub-skill when you already have a checkpoint and want overlays, lane fits, or Tusimple batch output.

Typical path:

1. Restore the checkpoint.
2. Preprocess images to the LaneNet input size.
3. Decode binary/instance outputs.
4. Tune DBSCAN and lane-fit behavior when custom data produces empty masks.

Owner: [inference-evaluation](../sub-skills/inference-evaluation/SKILL.md)

## 4. Freeze or export the model

Use the **model-export** sub-skill when you need a frozen PB or an MNN-oriented deployment handoff.

Typical path:

1. Freeze the TensorFlow checkpoint into `lanenet.pb`.
2. If you have the external MNN converter toolchain, convert the frozen PB into an MNN model.
3. Update the MNN runtime config with the frozen model path and DBSCAN parameters.

Owner: [model-export](../sub-skills/model-export/SKILL.md)

## Shared constraints

- The repo config loader uses relative paths, so a script run from the wrong directory can fail even when the files exist.
- The sample `train.txt` and `val.txt` files under `data/training_data_example/` are placeholders and should not be treated as production-ready.
- TensorFlow 1.15 + CUDA 10.0 + cuDNN 7.6 was the verified runtime for this skill generation pass.
