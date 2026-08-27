# YOLOX Export And Deployment Troubleshooting

## First checks

```bash
python scripts/export_yolox_template.py --format onnx --name yolox-s --dry-run
python -c "import yolox, torch, onnx; print(yolox.__version__, torch.__version__, onnx.__version__)"
```

## Failure matrix

| Symptom | Likely cause | Fix |
|---|---|---|
| `--checkpoint is required` | Real export requested without weights. | Use `--dry-run` or supply an existing checkpoint path. |
| Checkpoint shape mismatch | Wrong model selector, custom `Exp`, `num_classes`, depth/width, or depthwise setting. | Match `--name`/`--exp-file` to checkpoint source. |
| ONNX package missing | Export dependencies not installed. | Install `onnx`; install `onnx-simplifier` only when simplification is required. |
| `onnxsim` / simplifier failure | Simplifier package/runtime incompatibility or graph unsupported. | Re-run with simplification disabled; validate raw ONNX first. |
| ONNXRuntime output boxes scaled wrong | Preprocessing ratio, decode setting, or postprocess interpretation differs. | Verify `decode_in_inference`, resize ratio, tensor names, NMS/conf thresholds, and class count. |
| TorchScript tracing error | Model forward path or custom ops not trace-friendly for given settings. | Try ONNX, adjust `decode_in_inference`, or inspect custom modules in the `Exp`. |
| TensorRT import error | TensorRT/torch2trt not installed or ABI mismatch. | Install a TensorRT stack matching CUDA/PyTorch, or use ONNX/TorchScript instead. |
| TensorRT engine fails on another host | Engines are hardware/runtime-specific. | Build and validate the engine on the deployment hardware/runtime. |
| OpenVINO conversion fails | Unsupported opset/operator or Focus/decode mismatch. | Try opset 10/11, raw outputs, and runtime-specific conversion guidance. |
| Legacy checkpoint unsupported in deployment | Old preprocessing-compatible weights only work with `--legacy` in PyTorch demo/eval. | Use a compatible old YOLOX version for deployment or retrain/regenerate weights. |
| Output path points to a directory | Helper expects a file path. | Provide an output filename with `.onnx` or `.pt`. |

## Safe recovery order

1. Dry-run model construction.
2. Verify checkpoint path and model/Exp compatibility.
3. Export without optional simplification.
4. Validate with the target runtime's simplest smoke.
5. Only then add dynamic axes, simplification, TensorRT, vendor SDKs, or benchmarking.
