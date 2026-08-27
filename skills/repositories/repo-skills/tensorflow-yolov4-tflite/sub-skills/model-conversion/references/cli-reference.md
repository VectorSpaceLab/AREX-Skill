# Conversion CLI Reference

The repository exposes conversion as top-level Python scripts. Run them from a
target checkout root unless every relevant path is absolute.

## `save_model.py`

Purpose: build YOLOv3/YOLOv4 Keras graph, load Darknet weights, decode outputs,
and save a TensorFlow SavedModel directory.

Verified help flags:

| Flag | Default | Meaning |
|---|---|---|
| `--weights` | `./data/yolov4.weights` | Darknet `.weights` source file. |
| `--output` | `./checkpoints/yolov4-416` | SavedModel output directory. |
| `--tiny` / `--notiny` | false | Select tiny model head/backbone. |
| `--input_size` | `416` | Square input size for Keras input and decode grid. |
| `--score_thres` | `0.2` | Score threshold used before non-max suppression for non-TFLite exports. |
| `--framework` | `tf` | `tf`, `trt`, or `tflite`; controls decode/export tensor shape. |
| `--model` | `yolov4` | `yolov3` or `yolov4`. |

Important source behavior:

- `utils.load_config(FLAGS)` selects strides, anchors, class count, and XY scale
  from `core.config.cfg` based on `--model` and `--tiny`.
- `utils.load_weights(model, FLAGS.weights, FLAGS.model, FLAGS.tiny)` expects
  Darknet binary layout for the selected model family.
- For `--framework tflite`, the SavedModel output returns `(pred_bbox,
  pred_prob)`; for ordinary `tf`/`trt`, it applies `filter_boxes` and saves a
  concatenated prediction tensor.

## `convert_tflite.py`

Purpose: convert a SavedModel directory into `.tflite` and run a random-input
interpreter demo after conversion.

Verified help flags:

| Flag | Default | Meaning |
|---|---|---|
| `--weights` | `./checkpoints/yolov4-416` | Input SavedModel directory. |
| `--output` | `./checkpoints/yolov4-416-fp32.tflite` | Output `.tflite` file. |
| `--input_size` | `416` | Representative image resize size. |
| `--quantize_mode` | `float32` | `float32`, `float16`, or `int8`. |
| `--dataset` | source-author local path | Representative image list for int8 calibration. |

Notes:

- Float16 sets `supported_types` and allows select TF/custom ops.
- Int8 assigns `representative_dataset = representative_data_gen`, but the
  script also uses select TF ops/custom ops. Verify the final interpreter and
  Android target support the produced ops.
- `representative_data_gen` reads only up to 10 accessible images.

## `convert_trt.py`

Purpose: convert a SavedModel into a TF-TRT SavedModel and inspect TensorRT
engine nodes.

Verified help flags:

| Flag | Default | Meaning |
|---|---|---|
| `--weights` | `./checkpoints/yolov4-416` | Input SavedModel directory. |
| `--output` | `./checkpoints/yolov4-trt-fp16-416` | Output TF-TRT SavedModel directory. |
| `--input_size` | `416` | Representative input size. |
| `--quantize_mode` | `float16` | `int8`, `float16`, or FP32 fallback for other values. |
| `--dataset` | source-author local path | Representative dataset list for INT8 calibration. |
| `--loop` | `8` | Batch count used in representative data generation. |

Notes:

- FP16 and FP32 paths call `converter.convert()` without calibration input.
- INT8 path calls `converter.convert(calibration_input_fn=representative_data_gen)`.
- `max_workspace_size_bytes` is set to 4 GB and `max_batch_size` to 8 in source.

## Artifact naming conventions

Use explicit names that encode model family, size, and precision:

- SavedModel: `checkpoints/yolov4-416`, `checkpoints/yolov4-tiny-416`,
  `checkpoints/yolov3.tf`.
- TFLite: `checkpoints/yolov4-416.tflite`,
  `checkpoints/yolov4-416-fp16.tflite`,
  `checkpoints/yolov4-416-int8.tflite`.
- TF-TRT: `checkpoints/yolov4-trt-fp16-416`.

Avoid generic output names when the user will compare multiple variants.
