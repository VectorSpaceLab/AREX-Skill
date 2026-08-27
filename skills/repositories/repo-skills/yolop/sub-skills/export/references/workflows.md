# YOLOP ONNX Export and ONNXRuntime Workflows

## When to read

Read this when creating an ONNX model from `End-to-end.pth`, validating existing YOLOP ONNX files, or adapting the source `export_onnx.py` and `test_onnx.py` behavior with safer paths.

## Source ONNX export

The source command shape is:

```bash
PYTHONPATH=. python export_onnx.py --height 640 --width 640
```

The source script:

- Defines an export-specific `MCnet` and `YOLOP` architecture list.
- Loads `weights/End-to-end.pth`.
- Exports to `weights/yolop-{height}-{width}.onnx`.
- Uses opset 12 and output names `det_out`, `drive_area_seg`, `lane_line_seg`.
- Runs `onnx.checker.check_model`.
- Simplifies with `onnxsim.simplify`.
- Opens the model with ONNXRuntime.

Use the bundled exporter when you need an explicit `--output` path or a random-init smoke.

## Bundled exporter

```bash
python sub-skills/export/scripts/export_onnx_model.py \
  --repo-root /path/to/YOLOP \
  --checkpoint /path/to/YOLOP/weights/End-to-end.pth \
  --output /tmp/yolop-640-640.onnx \
  --height 640 --width 640 --simplify --check
```

For a dependency-only smoke without a checkpoint:

```bash
python sub-skills/export/scripts/export_onnx_model.py \
  --repo-root /path/to/YOLOP \
  --output /tmp/yolop-smoke.onnx \
  --height 128 --width 128 --random-init --check
```

The helper imports `MCnet` and `YOLOP` from the source `export_onnx.py` to preserve the three-output ONNX contract.

## Expected ONNX interface

For the shipped `640x640` model, ONNXRuntime reports:

```text
input:  images [1, 3, 640, 640]
output: det_out [1, 25200, 6]
output: drive_area_seg [1, 2, 640, 640]
output: lane_line_seg [1, 2, 640, 640]
```

For other square sizes, the detection count changes by grid size while segmentation outputs stay `[1, 2, height, width]`.

## Source ONNX inference

The source command shape is:

```bash
PYTHONPATH=. python test_onnx.py --weight yolop-640-640.onnx --img test.jpg
```

The source script:

- Looks for the ONNX file under `weights/` by filename.
- Saves images under `pictures/detect_onnx.jpg`, `pictures/da_onnx.jpg`, `pictures/ll_onnx.jpg`, and `pictures/output_onnx.jpg`.
- Uses `resize_unscale`, ImageNet normalization, ONNXRuntime, YOLOP NMS, and mask blending.

Use the bundled ONNX inference helper when you need explicit model/image/output paths and no mutation of the checkout's `pictures/` directory.

## Bundled ONNX inference

```bash
python sub-skills/export/scripts/run_onnx_inference.py \
  --repo-root /path/to/YOLOP \
  --onnx /tmp/yolop-640-640.onnx \
  --image /path/to/image.jpg \
  --output-dir /tmp/yolop-onnx-output
```

It saves `detect.jpg`, `drivable.png`, `lane.png`, and `merged.jpg` under the output directory.

## Output interpretation

- `det_out` is post-grid, pre-NMS detection predictions with columns compatible with YOLOP `non_max_suppression`.
- `drive_area_seg` and `lane_line_seg` are two-class logits/probabilities; `argmax(axis=1)` yields masks.
- The inference helper crops letterbox padding and resizes masks back to the original image size before saving.
