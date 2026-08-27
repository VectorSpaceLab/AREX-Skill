# Troubleshooting

## Purpose

Read this when export or speed timing fails.

## Hardcoded path failures

### Symptoms
- `FileNotFoundError` for a checkpoint in `export.py`.
- The C++ example cannot find the model or video path.

### Cause
- The source files were written as local demos with hardcoded absolute paths.

### Recovery
- Use the bundled helper scripts with explicit `--checkpoint`, `--output`, and `--repo-root` arguments.
- Do not try to keep the hardcoded source paths in a portable workflow.

## Wrong device or map_location

### Symptoms
- The export step fails on CPU-only hardware.
- The TorchScript load or trace path fails because the checkpoint was loaded on the wrong device.

### Cause
- The source demo assumes CUDA in its example path.

### Recovery
- Pick the device explicitly in the bundled export helper.
- If the user wants a CPU-compatible artifact, say so up front and avoid a CUDA-only demo path.

## Checkpoint and shape mismatches

### Symptoms
- The model loads but the output shape does not match the expected lane dimensions.
- Export or benchmark runs fail because `griding_num`, `num_lanes`, or the backbone choice is wrong.

### Cause
- The helper was pointed at the wrong dataset family or checkpoint.

### Recovery
- Use `data-and-config` to confirm the row anchors and class dimensions first.
- Keep the `cls_dim` setting aligned with the checkpoint.

## Half precision and C++ example issues

### Symptoms
- The C++ example fails at runtime with CUDA or dtype errors.

### Cause
- The example assumes CUDA and half precision.
- The install paths in `CMakeLists.txt` and `src/main.cpp` are hardcoded.

### Recovery
- Treat the C++ demo as a deployment reference until the paths are replaced.
- Build and run it only in an environment that has the required LibTorch/OpenCV setup.

## Speed benchmark issues

### Symptoms
- `speed_real.py` hangs on camera capture or does not read frames.
- The benchmark reports suspiciously fast or slow timing because the device setup is inconsistent.

### Cause
- No camera/video input is available.
- The benchmark was run on a different device from the one the user intended.

### Recovery
- Prefer the synthetic benchmark when a real camera/video source is not available.
- Use an explicit device and loop count.
