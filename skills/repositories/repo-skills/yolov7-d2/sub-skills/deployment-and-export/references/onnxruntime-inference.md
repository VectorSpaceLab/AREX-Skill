# ONNXRuntime Inference

The source ORT demo is oriented toward YOLOX-style output postprocessing and optional mask handling. A separate DETR ORT demo (`tools/demo_onnx_detr.py`) is reference-only because it hard-codes input name, image locations, resize shape, and visualization behavior. The ORT demo accepts:

- `-m, --model`: ONNX model path.
- `-i, --image_path`: image path.
- `-o, --output_dir`: output directory.
- `-s, --score_thr`: score threshold.
- `--input_shape`: shape string such as `640,640`.
- `--with_p6`: whether the model has a P6 feature level.
- `-int8, --int8`: whether the model is quantized int8.

## Command shape

```bash
python deploy/ort_infer.py \
  --model path/to/model.onnx \
  --image_path path/to/image.jpg \
  --output_dir path/to/out \
  --score_thr 0.3 \
  --input_shape 640,640
```

## Preflight

Use the bundled ONNX inspector first:

```bash
python scripts/inspect_onnx_model.py path/to/model.onnx --providers
```

Check that:

- The model input layout matches the export path (some YOLOv7-d2 export paths use NHWC-like tensors).
- Output names and shapes match the postprocessing code.
- The model family matches the chosen postprocess assumptions: SparseInst masks are not the same as YOLOX box grids.

## Runtime dependencies

CPU ORT inference needs `onnxruntime`, OpenCV, NumPy, and visualization dependencies if drawing outputs. GPU ORT requires provider-specific packages and drivers; do not claim GPU ORT works until `InferenceSession(..., providers=[...])` uses the requested provider.
