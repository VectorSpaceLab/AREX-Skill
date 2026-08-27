# Conversion Workflows

This reference distills the repository's conversion scripts and README commands
into task-oriented plans. Commands assume a target checkout root as the current
working directory.

## Darknet weights to TensorFlow SavedModel

Use `save_model.py` when the input is a Darknet `.weights` file and the output
should be a TensorFlow SavedModel directory.

```bash
python save_model.py \
  --weights ./data/yolov4.weights \
  --output ./checkpoints/yolov4-416 \
  --input_size 416 \
  --model yolov4
```

Variants:

- YOLOv4 tiny: add `--tiny` and use tiny weights/output names.
- YOLOv3: change `--model yolov3` and use YOLOv3 weights.
- TFLite-friendly SavedModel: add `--framework tflite`; this keeps separate
  bbox/prob outputs expected by the TFLite conversion and inference paths.
- TensorRT preparation: the README uses ordinary `--framework tf` SavedModels
  before `convert_trt.py`.

Expected output is a SavedModel directory containing TensorFlow model files. Do
not proceed to TFLite or inference until the directory exists and loads with
`tf.saved_model.load` in the chosen environment.

## SavedModel to TFLite

Use `convert_tflite.py` after a SavedModel was written by `save_model.py`.

```bash
python save_model.py \
  --weights ./data/yolov4.weights \
  --output ./checkpoints/yolov4-416 \
  --input_size 416 \
  --model yolov4 \
  --framework tflite

python convert_tflite.py \
  --weights ./checkpoints/yolov4-416 \
  --output ./checkpoints/yolov4-416.tflite \
  --quantize_mode float32
```

Quantization modes:

| Mode | Extra inputs | Script behavior | Notes |
|---|---|---|---|
| `float32` | none | default TFLite conversion | Safest first artifact. |
| `float16` | none | sets `Optimize.DEFAULT`, supported type float16, allows select TF ops/custom ops | Good mobile-size compromise. |
| `int8` | representative dataset list | reads up to the first 10 accessible image paths from `--dataset` | README warns YOLOv4 and YOLOv4-tiny int8 had issues; verify before mobile release. |

For int8 calibration:

```bash
python convert_tflite.py \
  --weights ./checkpoints/yolov4-416 \
  --output ./checkpoints/yolov4-416-int8.tflite \
  --quantize_mode int8 \
  --dataset ./coco_dataset/coco/val2017.txt
```

The dataset file is whitespace-split by the script; every token considered as
an image path may be checked. Use a clean representative-image list when
possible rather than a training annotation line containing boxes.

## SavedModel to TF-TRT

Use `convert_trt.py` for TensorFlow-TensorRT conversion. This path requires a
TensorFlow build with TF-TRT support and a compatible NVIDIA CUDA/TensorRT
runtime.

```bash
python save_model.py \
  --weights ./data/yolov4.weights \
  --output ./checkpoints/yolov4.tf \
  --input_size 416 \
  --model yolov4

python convert_trt.py \
  --weights ./checkpoints/yolov4.tf \
  --quantize_mode float16 \
  --output ./checkpoints/yolov4-trt-fp16-416
```

`convert_trt.py` supports `float16`, `int8`, and a fallback FP32 branch. INT8
uses `representative_data_gen`; note that this function contains a source typo
`utils.image_preporcess`, so INT8 TF-TRT calibration needs a target-checkout fix
or a wrapper before use.

Expected signal after conversion:

- `Done Converting to TF-TRT` is printed.
- The output SavedModel directory exists.
- The script prints operation names and counts `TRTEngineOp` nodes. A count of
  zero means TensorRT did not capture useful subgraphs.

## Conversion validation checklist

- The `--model` flag matches the source weights family.
- Tiny weights use `--tiny` consistently in `save_model.py` and downstream
  inference.
- `--input_size` matches the artifact name and downstream inference size.
- The class file and anchor constants in `core/config.py` match the trained
  weights. Custom class counts require retraining/conversion consistency.
- The output path is new or intentionally overwritten.
- For TFLite, the artifact is tested with `tf.lite.Interpreter` before Android
  asset replacement.
- For TensorRT, `tf.config.experimental.list_physical_devices("GPU")` and
  TensorRT library availability are verified in the same environment that runs
  conversion.
