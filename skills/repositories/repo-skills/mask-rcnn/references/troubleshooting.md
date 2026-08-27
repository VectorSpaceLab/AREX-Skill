# Cross-cutting Troubleshooting

## Import fails: `No module named 'keras.engine'`

**Likely cause:** A modern standalone Keras package changed its public module layout, while Mask_RCNN imports `keras.engine`.

**Recovery:** Use a TensorFlow 1 / Keras 2.3-style environment for faithful execution. If the task explicitly asks to modernize the code, route it as a porting task and update imports plus graph operations deliberately; do not treat a one-line shim as verified training support.

## Import fails: `module 'tensorflow' has no attribute 'log'` or `tf.random_shuffle`

**Likely cause:** TensorFlow 2 removed or moved TF1 symbols used by Mask_RCNN.

**Recovery:** Prefer TensorFlow 1.15 for package use. For a port, replace `tf.log` with `tf.math.log`, `tf.random_shuffle` with `tf.random.shuffle`, `tf.to_float` with `tf.cast(..., tf.float32)`, and graph/session assumptions with compatible TF2 or `tf.compat.v1` patterns.

## Model build fails with image-size or reshape errors

**Symptoms:** Errors about image size divisibility, `None values not supported` in reshape, or tensor shape conversion.

**Likely causes:**

- `IMAGE_MIN_DIM`/`IMAGE_MAX_DIM` are not compatible with the feature pyramid; dimensions must be divisible by 64 after resizing/padding.
- Modern Keras shape semantics are incompatible with legacy graph code.
- `NUM_CLASSES` or config values do not match the loaded weights.

**Recovery:** Use dimensions such as 128, 256, 512, or 1024 for graph-building smoke checks. Verify with `scripts/check_env.py --build-tiny-graph`. For new datasets, set `NUM_CLASSES = 1 + object_class_count` and exclude class-specific heads when loading COCO weights.

## Weights fail to load or classes are mismatched

**Symptoms:** HDF5 shape mismatch, missing layers, incorrect number of classes, or poor predictions after loading.

**Likely causes:** The checkpoint was trained with a different `NUM_CLASSES`, backbone, or layer naming; COCO weights include 80 object classes and should not directly initialize the final class/mask heads for a one-class dataset.

**Recovery:** For transfer learning from COCO to a new class set, call `load_weights(..., by_name=True, exclude=["mrcnn_class_logits", "mrcnn_bbox_fc", "mrcnn_bbox", "mrcnn_mask"])`. For ImageNet, use `get_imagenet_weights()` only when network access/cache policy allows it.

## Dataset appears empty or masks are wrong

**Symptoms:** `Image Count: 0`, empty masks, `IndexError`, all-zero bounding boxes, no training positives, or visualization shows no instances.

**Likely causes:** Dataset subclass did not call `add_class`/`add_image`, `prepare()` was skipped, mask dtype/shape is wrong, paths do not match expected layout, or polygon/RLE annotations were parsed with the wrong convention.

**Recovery:** Route to [data-preparation](../sub-skills/data-preparation/SKILL.md). Run [validate_dataset_layout.py](../sub-skills/data-preparation/scripts/validate_dataset_layout.py) for known sample layouts, and inspect [dataset-contract.md](../sub-skills/data-preparation/references/dataset-contract.md) for the required mask shape `[height, width, instance_count]` and class id array.

## Training is very slow or exhausts memory

**Likely cause:** Mask R-CNN with a ResNet/FPN backbone is compute- and memory-heavy; the original examples assume GPU acceleration for practical training.

**Recovery:** Lower `IMAGES_PER_GPU`, use smaller image dimensions for smoke tests, train `heads` first, and treat CPU training as a syntax/data-pipeline check only. Verify actual CUDA runtime before claiming GPU training support.

## Original sample script or notebook path is missing

This generated skill intentionally does not require the original checkout. Use the bundled references and scripts instead of asking future agents to run source sample files. If a task specifically involves maintaining the original repository, use a repository-maintenance workflow, not this self-contained package operating skill.
