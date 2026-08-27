# Export Troubleshooting

## Missing optional packages

Symptoms:

- `ImportError` for `onnx`, `onnxslim`, `onnxruntime`, `openvino`, `coremltools`, `tensorflow`, `tensorflowjs`, `keras`, or Paddle packages.
- Export code fails immediately after selecting a non-PyTorch format.

Recovery:

- Install only the package family required by the chosen format list.
- Use `scripts/check_export_prereqs.py` to inspect which optional dependencies are visible before launching a conversion.

## TensorRT errors

Symptoms:

- Engine deserialization fails.
- The runtime complains about version mismatch or unsupported engine.
- CUDA is available but the engine still does not load.

Recovery:

- Rebuild the engine on the target runtime stack.
- Match TensorRT major/minor version, GPU architecture, and driver/runtime environment.
- Do not assume a successful ONNX export means the TensorRT engine is portable.

## ONNX/OpenVINO issues

- Install `onnx` first; many conversion paths depend on it.
- Some export paths also want `onnxslim` or `onnxruntime`.
- OpenVINO conversion usually starts from ONNX and may need matching runtime packages.
- Keep dynamic shape and NMS choices intentional when debugging runtime discrepancies.

## TensorFlow/TFLite/TF.js issues

- The TensorFlow family is heavy and version-sensitive.
- `tensorflowjs` pulls in additional tooling and may not be worth installing for a non-TF task.
- Keras version pinning matters for some paths.
- Prefer a smaller export family when the user only needs interoperability.

## CoreML and platform issues

- CoreML is best validated on macOS.
- `mlpackage` handling is backend/platform sensitive.
- Do not expect macOS-only packages to be practical on Linux inspection hosts.

## Edge TPU and compiler issues

- Edge TPU export may depend on external compiler/runtime tooling.
- A shell-safety or parser check does not prove the compiler exists.
- Treat Edge TPU as an optional deployment target that needs dedicated tooling.

## Path and shell safety

- Do not build commands by concatenating untrusted model paths into a shell string.
- The export invariant test confirms `shell=True` should not be used in the Edge TPU path.
- Use argument lists and explicit paths for all export helpers.
