# Model Conversion Troubleshooting

## `save_model.py` cannot read the Darknet weights

**Symptoms**

- `FileNotFoundError` for a `.weights` path.
- Shape or layer errors while `utils.load_weights` iterates conv layers.
- SavedModel output is missing after the command exits.

**Likely causes**

- The weights file was not downloaded or is a partial download.
- `--model` or `--tiny` does not match the weights family.
- Custom-trained weights use a class count or anchor configuration that no
  longer matches `core.config.cfg`.

**Recovery**

1. Confirm file size and provenance before running conversion.
2. Use the conversion planner with `--check-paths` to validate source and target
   path choices.
3. Match flags to weights: YOLOv4 full (`--model yolov4`), YOLOv4 tiny
   (`--model yolov4 --tiny`), YOLOv3 full (`--model yolov3`), YOLOv3 tiny
   (`--model yolov3 --tiny`).
4. For custom classes, align the class names file, class count, anchors, and
   training checkpoint before conversion.

## TFLite conversion succeeds but inference output shape is confusing

**Likely cause**: The SavedModel was exported with the wrong `--framework`.
TFLite workflows expect a `save_model.py --framework tflite` export that keeps
bbox and probability tensors separate.

**Recovery**

- Re-run `save_model.py` with `--framework tflite`.
- Re-run `convert_tflite.py` from that SavedModel directory.
- Use the inference sub-skill's TFLite route; TFLite output order differs for
  some tiny/model combinations.

## INT8 TFLite has low accuracy or conversion warnings

**Evidence**: The README notes YOLOv4 and YOLOv4-tiny int8 quantization had
issues and suggests trying YOLOv3/YOLOv3-tiny int8.

**Recovery**

- First verify float32 and float16 artifacts on the same image.
- Use a representative dataset list containing real image paths, not annotation
  lines with bbox tokens mixed in.
- Calibrate with images from the target deployment domain.
- Compare output boxes/classes against a SavedModel or float32 TFLite baseline
  before replacing Android assets.

## TensorFlow GPU or TensorRT is not usable

**Symptoms**

- TensorFlow imports but logs missing `libcudart.so.10.1`, `libcublas.so.10`,
  `libcudnn.so.7`, or similar libraries.
- `tf.config.experimental.list_physical_devices("GPU")` returns an empty list.
- `convert_trt.py` imports but fails during converter construction or saves a
  graph with no `TRTEngineOp` nodes.

**Likely cause**: The runtime does not match TensorFlow 2.3's CUDA/cuDNN/TensorRT
expectations.

**Recovery**

1. Use CPU SavedModel/TFLite conversion if TensorRT is not required.
2. For TF-TRT, move to a TensorFlow 2.3-compatible container or environment with
   matching CUDA 10.x, cuDNN 7, and TensorRT libraries.
3. Verify the same environment with a minimal TensorFlow GPU check before
   launching conversion.
4. Treat a visible `nvidia-smi` GPU as insufficient; TensorFlow must report a
   usable GPU device.

## INT8 TF-TRT calibration fails on `image_preporcess`

**Symptom**

```text
AttributeError: module 'core.utils' has no attribute 'image_preporcess'
```

**Cause**: The source `convert_trt.py` representative data function contains a
typo; the utility is named `image_preprocess`.

**Recovery**

- If the user controls the target checkout, patch the typo to
  `utils.image_preprocess` and rerun the calibration command.
- If source edits are not allowed, avoid INT8 TF-TRT and use FP16/FP32 TF-TRT or
  TFLite INT8 instead.

## Output path overwritten or mixed between variants

**Symptom**: Later inference uses the wrong model, or a `.tflite` file name does
not match the precision/model size.

**Recovery**

- Use explicit output names that include model family, tiny/full, input size,
  and precision.
- Keep SavedModel directories and `.tflite` files separate.
- Before overwriting, ask the user whether prior artifacts are disposable.
