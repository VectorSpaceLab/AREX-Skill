# Troubleshooting

This guide focuses on deployment-specific failures: export, engine build, backend configs, backend inference, and optional dependency gates.

## Symptom → likely cause → recovery

| Symptom | Likely cause | Recovery path |
| --- | --- | --- |
| The exporter falls back to model-only | The chosen backend is not in the end-to-end export set. | Use the string backend names supported by the exporter, or switch to `--model-only` and handle decode/NMS downstream. |
| The exporter says `onnxsim` is missing or simplify failed | The optional simplifier is absent or incompatible with the graph. | Keep the ONNX export; simplification is optional. Install `onnxsim` only if simplification is needed. |
| A TensorRT build fails with missing CUDA/TensorRT | The machine does not have the vendor stack or a CUDA-capable GPU. | Stop the TensorRT path. Use a CPU ONNXRuntime plan instead, or move to a vendor-enabled environment before retrying. |
| TensorRT engine builder rejects the checkpoint suffix | The input is not an ONNX file. | Export ONNX first, then feed the exported file into the engine builder. |
| TensorRT dynamic build rejects the `--scales` value | The scale list is malformed or does not contain the three expected shapes. | Pass a min/opt/max list with three entries; keep all three equal for a static engine. |
| MMDeploy backend inference raises an import error | MMDeploy is not installed or not importable in the current environment. | Install MMDeploy and rerun the deploy/test route. |
| Backend inference or evaluation uses the wrong device | The backend and device do not match. | Use `cpu` for ONNXRuntime and `cuda:0` for TensorRT. |
| Backend image inference rejects the artifact suffix | The checkpoint/artifact suffix is not `.onnx`, `.engine`, or `.plan`. | Export to one of the supported backend artifact types first. |
| RKNN deployment cannot be proven from this machine | RKNN needs its own toolchain and target hardware. | Treat the path as blocked until the vendor stack is available; CPU inspection can only confirm imports. |
| DeepStream setup stalls at build or run time | Missing DeepStream, CUDA, GPU, or a TensorRT engine. | Build only in a DeepStream-capable NVIDIA environment with a prepared engine. |
| Static deployment config behaves like a dynamic config | The model config still contains resize behavior or batch-shape handling. | Use the static model template adjustments: disable scale-up/mini-pad and clear batch-shape policy. |
| TensorRT INT8 config has no calibration path | `calib_config` or calibration data is missing. | Keep the flow as FP16 or provide calibration data and rerun the INT8 path. |

## Specific backend rules

### CPU ONNXRuntime
- Use the ONNXRuntime backend name in the exporter.
- Keep the device on `cpu` for the common path.
- Use the ONNXRuntime inference route for the exported `.onnx` artifact.

### TensorRT
- Require CUDA and a compatible GPU.
- Use a TensorRT backend name in the exporter or a TensorRT deployment config.
- Keep `use_efficientnms` tied to TensorRT-capable deployments only.

### RKNN
- Treat the current CPU-only machine as insufficient for final verification.
- Use the RKNN deploy config family, target platform, and input-size list.
- Expect a narrow static-input workflow rather than a general end-to-end export.

### MMDeploy
- Keep the deploy config and model config paired.
- Use the backend model artifact that matches the deploy config backend.
- When the backend model exists but the visualizer or SDK fails, check the MMDeploy package first.

## Safe recovery order

1. Probe the environment with `scripts/check_deployment_dependencies.py`.
2. Decide whether the task is CPU ONNXRuntime, TensorRT, RKNN, MMDeploy, or DeepStream.
3. If the required backend package or hardware is missing, stop instead of forcing the command.
4. Re-run only after the correct environment or backend artifact exists.

## Known mismatch to avoid

If you see older prose examples that pass a numeric backend flag, follow the current exporter code path instead: use the backend names that the script accepts.
