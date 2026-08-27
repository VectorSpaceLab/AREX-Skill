# Speed and Deployment

## Purpose

Read this when you need to time the model or understand the C++ deployment example.

## Verified speed script behavior

- `speed_simple.py` creates a `parsingNet` on CUDA and runs a repeated synthetic forward pass.
- `speed_real.py` captures from a camera or video source, preprocesses frames, and measures practical throughput.

## Model dimensions that matter

- CULane uses `griding_num=200` and 18 row anchors.
- TuSimple uses `griding_num=100` and 56 row anchors.
- The model output shape is controlled by `cls_dim = (griding_num + 1, cls_num_per_lane, num_lanes)`.

## C++ deployment notes

- The `cpp/` example uses LibTorch and OpenCV C++.
- It hardcodes Torch and OpenCV install paths in `CMakeLists.txt`.
- It also hardcodes a TorchScript model path and a video path in `src/main.cpp`.
- The example assumes CUDA and half precision in the runtime path.

## Practical guidance

- Use the synthetic benchmark before the camera/video benchmark when you only need a stable timing estimate.
- Keep the model dimensions aligned with the chosen dataset family before exporting or benchmarking.
- Treat the C++ example as a deployment reference rather than a portable command until the hardcoded paths are replaced.
