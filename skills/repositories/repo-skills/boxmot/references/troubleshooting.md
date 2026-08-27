# Cross-Cutting Troubleshooting

Use this page for BoxMOT issues that cut across several workflows.

## Import or CLI entry point problems

If a script cannot import `boxmot`, prefer module execution from a proper install:

```bash
boxmot --help
python -c "import boxmot"
```

If you are running from a source checkout and the package dependencies are missing, install the public package or sync the repo environment before retrying.

## Missing optional extras

Some workflows need extra packages beyond the core install:

- `yolo` for detector-backed tracking and benchmark replay
- `evolve` for `tune`
- `research` for `research`
- `onnx` for ONNX export
- `openvino` for OpenVINO export
- `tflite` for LiteRT/TFLite export

If a workflow says a module is missing, install the matching extra instead of widening the whole environment blindly.

## CUDA / ONNX / TensorRT

For GPU-backed ReID or export issues, check runtime visibility first:

```bash
python -c "import torch; print(torch.cuda.is_available())"
python -c "import onnxruntime as ort; print(ort.get_available_providers())"
```

If TensorRT is involved, a wheel install alone is not enough. The machine still needs a compatible CUDA/NVIDIA driver stack.

## OBB shape mismatches

BoxMOT switches between AABB and OBB from tensor shape:

- AABB detections: `(x1, y1, x2, y2, conf, cls)`
- OBB detections: `(cx, cy, w, h, angle, conf, cls)`

If you get a shape error, verify the detector is emitting the right column count and that the tracker actually supports OBB.

## Benchmark cache confusion

`generate`, `eval`, `tune`, and `research` share cache keys based on benchmark, split, detector, ReID, and backend choices. If you change any of those, BoxMOT will build a new cache bucket.

## Native C++ backend failures

`--tracker-backend cpp` requires a C++17 toolchain, CMake, OpenCV, and Eigen. If build or load fails, check those tools first and confirm the requested tracker is one of the supported native backends.

## ReID checkpoints and datasets

ReID training and evaluation expect the dataset layout or YAMLs to be correct. If `train` or `eval-reid` fails early, confirm the dataset root, split names, and preprocess choice before investigating model code.
