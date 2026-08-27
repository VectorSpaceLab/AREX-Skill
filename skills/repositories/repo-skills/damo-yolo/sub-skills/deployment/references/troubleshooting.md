# DAMO-YOLO deployment troubleshooting

Use this when ONNX export, TensorRT export/evaluation, ONNX Runtime inference, OpenVINO conversion, or partial quantization fails.

## Dependency readiness

Start with:

```bash
sub-skills/deployment/scripts/check_deploy_env.py
sub-skills/deployment/scripts/check_deploy_env.py --json
```

Interpretation:

- ONNX export needs `damo`, CUDA/CPU PyTorch, torchvision, and `onnx`; `onnxsim` is optional.
- ONNX inference needs `onnxruntime` at demo/runtime time.
- TensorRT engine build/eval needs `tensorrt` plus CUDA runtime bindings (`cuda` package or PyCUDA depending on the path).
- Partial INT8 quantization needs TensorRT plus `pytorch_quantization` and calibration data.

## Common failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ModuleNotFoundError: onnx` | ONNX exporter dependency missing. | Install `onnx` in the active environment or use an environment prepared for ONNX export. |
| `ModuleNotFoundError: onnxscript` from an alternate export path | A newer `torch.onnx.export` path or a separate export script is using the dynamo exporter. | Use the bundled helper, which sets `dynamo=False`, or install `onnxscript` only if you intentionally chose the newer exporter. |
| `WARNING: ONNX simplification skipped` | `onnxsim` missing or simplification failed. | Export can still succeed; install `onnxsim` only if simplification is required. |
| `ModuleNotFoundError: onnxruntime` during ONNX demo | ONNX Runtime not installed. | Install `onnxruntime` or `onnxruntime-gpu` appropriate for the target device. |
| `ModuleNotFoundError: tensorrt` when checking TensorRT evaluator | TensorRT Python package/libraries missing. | Install a TensorRT version compatible with the CUDA driver/runtime, then rerun `check_deploy_env.py`. |
| `ModuleNotFoundError: pycuda` or CUDA copy errors | INT8 calibration/TensorRT path lacks PyCUDA or CUDA Python runtime. | Install the runtime package required by the selected source path and verify a tiny CUDA allocation. |
| `ModuleNotFoundError: pytorch_quantization` | Partial quantization stack missing. | Install NVIDIA `pytorch_quantization` from an approved index, usually after validating TensorRT/CUDA compatibility. |
| `ModuleNotFoundError: No module named 'tools'` when launching partial quantization directly | The source script expects sibling modules to be importable as a package, but the `tools/` directory is not a normal package. | Use the bundled deployment guidance instead of raw file execution, or explicitly make the repo root importable before running the source script. |
| `ValueError: unsupported model type` | Partial quantization `--model_type` is not `tiny`, `small`, or `medium`. | Choose one of the supported model types or create a new sensitivity mapping before claiming support. |
| Shape mismatch during ONNX export | Config, checkpoint, `--img-size`, `--batch-size`, or head class count mismatch. | Verify config/checkpoint pairing and use the same image size/batch as the deployment target. |
| `DeprecationWarning` / `TracerWarning` during ONNX export | The bundled helper uses the legacy TorchScript ONNX exporter on newer PyTorch builds; tracer warnings also appear because the model has control flow and tensor-to-Python conversions. | These warnings are expected during a successful export smoke. If you need the newer exporter, install `onnxscript` and choose that path explicitly. |
| TensorRT parser fails on NMS plugin | Exported end-to-end graph used TRT7 vs TRT8 symbolic that does not match runtime. | Re-export with the correct TRT plugin family; for ONNX Runtime use `--end2end --ort`. |
| INT8 calibration asserts too few images | Calibration image directory has fewer images than `batch_size * batch_num`. | Provide enough representative calibration `.jpg` files or reduce calibration batch/count intentionally. |

## Path and invocation pitfalls

The source partial-quantization script imports sibling tool modules and TensorRT at module import time. Direct file-path execution can fail before argparse help if the parent directory is not importable, and module invocation then fails if TensorRT is absent. Treat these as deployment-backend prerequisites, not training or inference errors.

Prefer generated-skill helpers for checks and ONNX export. When you intentionally operate in a full source checkout with TensorRT installed, set the working directory and import path explicitly in your runbook rather than assuming ambient shell state.

## End-to-end export choices

- Raw ONNX is the safest first artifact. It lets you validate checkpoint/config compatibility before adding NMS plugins.
- `--end2end --ort` creates an ONNX graph whose NMS behavior targets ONNX Runtime.
- `--end2end` without `--ort` creates TensorRT-plugin outputs. Match `--trt-version` to the runtime parser.
- `--with-preprocess` changes the input contract by embedding BGR-to-RGB and normalization. Use it only when the serving preprocessor expects raw BGR-ish input.

## Optional backend verification boundary

The skill construction environment verified CUDA PyTorch and the ONNX converter parser, but did not install TensorRT, PyCUDA, or `pytorch_quantization`. Therefore:

- Do not claim TensorRT or partial-quantization runtime success unless the user's active environment passes a real TensorRT/quantization smoke.
- Synthetic or CPU checks can validate instructions, not TensorRT performance or INT8 accuracy.
- If TensorRT execution is a required acceptance gate, run it on compatible NVIDIA hardware with the exact TensorRT/PyTorch/CUDA stack and record the result separately.
