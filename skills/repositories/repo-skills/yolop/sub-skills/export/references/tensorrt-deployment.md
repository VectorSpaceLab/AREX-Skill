# YOLOP TensorRT and ZED Deployment Notes

## When to read

Read this when a task asks about the `toolkits/deploy` path, `.wts` conversion, TensorRT engine building, ZED camera inference, or why deployment was not verified by a CPU Python smoke.

## Source deployment shape

The README describes:

1. Convert a PyTorch checkpoint to `yolop.wts`:

   ```bash
   PYTHONPATH=. python toolkits/deploy/gen_wts.py
   ```

2. Build and run the C++ TensorRT application under `toolkits/deploy`.
3. The C++ `main.cpp` builds `yolop.engine` from `yolop.wts` if an engine file is absent, then deserializes and runs inference.
4. The application uses ZED camera frames, CUDA buffers, TensorRT bindings, custom YOLO layer/plugin code, OpenCV CUDA preprocessing, NMS, segmentation/lane outputs, and visualization.

## Bundled `.wts` helper

The generated skill includes [../scripts/export_wts.py](../scripts/export_wts.py), which preserves the Python state-dict serialization pattern but requires explicit output:

```bash
python sub-skills/export/scripts/export_wts.py \
  --repo-root /path/to/YOLOP \
  --checkpoint /path/to/YOLOP/weights/End-to-end.pth \
  --output /tmp/yolop.wts
```

Use `--dry-run` first to print the number of state-dict tensors and parameters without writing a large text file.

## External prerequisites

The source CMake evidence is CUDA/TensorRT/ZED-specific. Expect to verify or adapt:

- NVIDIA GPU and compatible driver.
- CUDA toolkit/runtime. The source CMake references CUDA 10.2 paths.
- TensorRT headers/libraries (`nvinfer`, plugin build).
- ZED SDK and camera APIs (`find_package(ZED 3 REQUIRED)`).
- OpenCV C++ with CUDA modules if using the camera/preprocess path.
- C++11 compiler and CMake.
- Correct platform library paths; the source references aarch64 TensorRT include/library directories.

## Skill verification boundary

The generated repo skill verifies Python-level ONNX export/inference and `.wts` serialization logic only. It does not bundle or validate the full C++ TensorRT/ZED source tree, build a TensorRT engine, or prove embedded real-time speed.

If a user provides a deployment machine with the needed SDKs, use this reference as a checklist, then inspect the live checkout's deployment sources and build logs. Do not claim deployment success from Python CPU checks.

## Common deployment failure surfaces

- CMake typo or macro mismatch: the source `CMakeLists.txt` uses `coda_add_library`, which may need correction to `cuda_add_library` or a modern CUDA CMake target pattern depending on local tooling.
- Library path mismatch: x86_64 systems will not use the source aarch64 TensorRT library paths.
- Engine/cache mismatch: a stale `yolop.engine` may not match the current TensorRT version, GPU, input size, or `.wts` file.
- Binding mismatch: C++ code asserts four bindings and specific names; changing the ONNX/TensorRT output contract requires matching C++ edits.
- ZED camera availability: C++ runtime assumes a ZED camera path, not just static image inference.
