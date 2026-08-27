# Export and Deployment Troubleshooting

## Missing ONNX packages

Symptoms:

- `ModuleNotFoundError: No module named 'onnx'`, `onnxruntime`, or `onnxsim`.

Recovery:

```bash
python -m pip install onnx onnxruntime onnxsim
```

For GPU ONNXRuntime, install the appropriate provider package deliberately. CPUExecutionProvider is enough for functional export/inference smoke.

## Exported model has extra outputs

Symptoms:

- ONNXRuntime outputs include extra raw detection feature maps.
- `drive_area_seg` or `lane_line_seg` has a detection feature-map shape instead of `[1, 2, H, W]`.

Likely cause: exporting `lib.models.get_net(cfg)` directly. The active model returns a nested detection tuple in eval mode. Use the source `export_onnx.py` wrapper or bundled `export_onnx_model.py`, which imports that export-specific `MCnet`.

## Checkpoint format mismatch

Symptoms:

- `KeyError: 'state_dict'`.
- `load_state_dict` missing/unexpected key errors.

Recovery:

- Use an epoch checkpoint dictionary for source scripts.
- For bare state dicts, use the bundled exporter, which accepts either `checkpoint['state_dict']` or a direct state dict.
- Confirm architecture matches the checkpoint.

## ONNX simplification fails

Likely causes:

- Unsupported opset/backend combination.
- Shape inference differences with the installed torch/onnx/onnxsim versions.
- Export graph was already invalid.

Recovery:

1. Re-run with `--no-simplify --check` to separate export/check from simplification.
2. Try the README-era dependency stack if exact historical export behavior is required.
3. Keep `--height` and `--width` multiples of 32.

## ONNXRuntime cannot find named outputs

The expected output names are `det_out`, `drive_area_seg`, and `lane_line_seg`. If a model lacks those names, inspect its session outputs before running postprocessing:

```bash
python sub-skills/export/scripts/run_onnx_inference.py --repo-root /path/to/YOLOP --onnx model.onnx --image image.jpg --output-dir /tmp/out --dry-run
```

## TensorRT build fails

Recovery checklist:

- Verify CUDA, TensorRT, ZED SDK, OpenCV C++, compiler, and CMake versions.
- Adapt hard-coded include/library paths for the host architecture.
- Ensure `.wts` and C++ binding constants match the intended input size/output names.
- Delete stale engine files when changing weights, TensorRT version, or GPU target.
- Treat C++ deployment as unverified until the actual engine builds and runs on the target hardware.
