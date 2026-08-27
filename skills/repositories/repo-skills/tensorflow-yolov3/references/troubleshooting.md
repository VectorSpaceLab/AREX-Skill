# Cross-cutting Troubleshooting

## TensorFlow import fails

Symptoms:

- `AttributeError: module 'tensorflow' has no attribute 'Session'`
- `AttributeError: module 'tensorflow' has no attribute 'placeholder'`
- `tf.layers` or `tf.variable_scope` missing

Likely cause: TensorFlow 2.x environment without TF1 compatibility. Use a TensorFlow 1.x-compatible environment for the original scripts, or port the code to `tf.compat.v1` deliberately before running.

Symptoms:

```text
TypeError: Descriptors cannot not be created directly
```

Likely cause: TensorFlow 1.x with protobuf 4.x. Pin protobuf to 3.20.x.

## Imports fail outside the repo root

Symptoms:

```text
FileNotFoundError: ./data/classes/coco.names
```

Likely cause: `core.utils.draw_bbox` reads the class file during import using `cfg.YOLO.CLASSES`, and config paths are relative. Run source scripts from the YOLOv3 working-copy root, or use wrappers that pass explicit paths and avoid import-time defaults.

Run the skill-owned checker to see the failure before starting a long workflow:

```bash
python scripts/check_environment.py --repo-root <repo-root>
```

## Missing model artifacts

Symptoms:

- `yolov3_coco.pb` not found for image/video inference.
- `yolov3_coco.ckpt.meta` / `.index` / `.data-*` missing for conversion.
- `yolov3_coco_demo.ckpt` missing for training initialization.
- `cfg.TEST.WEIGHT_FILE` points to a checkpoint prefix that has no shards.

Likely cause: the repo checkout does not include pretrained weights. Use the conversion sub-skill to check checkpoint/PB prerequisites and keep large artifacts outside the skill directory.

## Custom class count mismatch

Symptoms:

- Shape mismatch while restoring variables.
- Empty detections after using a custom class file.
- Annotation class ids exceed the class-file length.

Likely cause: `cfg.YOLO.CLASSES`, annotation class ids, output-head variables, and checkpoint variables do not match. Use data-preparation validation first. For COCO-initialized custom training, `convert_weight.py --train_from_coco` intentionally skips the final output heads.

## NaN loss or unstable training

Common causes:

- Annotation boxes with `xmax <= xmin` or `ymax <= ymin`.
- Boxes outside image dimensions.
- Missing images in annotation rows.
- Class ids not present in the class file.
- Batch size or input size too large for available memory.

The source dataset parser clips boxes and skips invalid boxes, but bad labels can still starve batches or hide problems. Validate the annotation files before training.

## Headless display errors

Symptoms:

- `cv2.imshow` / `cv2.namedWindow` failures.
- `Image.show()` opens nothing or blocks.
- Video demo fails at end-of-file with `ValueError("No image!")`.

Likely cause: source demos are interactive examples. For servers, save frames/images to files and handle EOF cleanly rather than opening GUI windows.

## Legacy GPU mismatch

The README pins `tensorflow-gpu==1.11.0`. On modern systems, a visible GPU does not prove that TF1.11 can run it. Treat CUDA training/inference as an optional, environment-specific capability unless the user supplies a known-compatible TF1/CUDA/cuDNN stack and required model/data artifacts.

Use CPU graph checks only for API and shape sanity. Do not claim CPU checks prove real GPU throughput, convergence, or production inference performance.
