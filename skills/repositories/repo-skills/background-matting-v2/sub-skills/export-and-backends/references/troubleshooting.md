# Export and backend troubleshooting

## Purpose

Use this page when a conversion or exported runtime fails.

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| checkpoint file missing | export CLIs require a real weight file | point `--model-checkpoint` at a real checkpoint or use the bundled smoke helper that does not need one |
| scripted model attribute changes do not stick | TorchScript wrapper was not used or the exported artifact was not scripted from the wrapper | use the repo's TorchScript wrapper pattern and re-run the smoke helper |
| ONNX export fails on patch ops | the chosen crop/replace methods are not backend-friendly | retry with `roi_align` and `scatter_element` |
| ONNX export fails before runtime load | `onnx` is not installed or the exporter hit an unsupported op | install `onnx`, lower the opset, or simplify the patch methods |
| ONNX Runtime cannot load the model | runtime package missing or exported graph uses unsupported ops | install `onnxruntime`, lower the opset, or simplify the patch methods |
| validation differs too much | model, dtype, or runtime path differs from the intended export path | re-run with the same model type, precision, and backend settings |
| `float16` export or inference fails on CPU | half precision is not a safe CPU path here | use `float32` or switch to CUDA |
| `backbone_scale should not be greater than 1/2` | invalid model parameter | keep `backbone_scale` at or below `0.5` |
| export is slow or memory heavy | dummy inputs or target resolution are too large | keep the smoke helper tiny and only scale up after the basic path passes |

## Extra guidance

- Prefer the smoke helper before a real export, especially when the target
  runtime is experimental.
- Use the dry-run wrappers when you need the exact command but not execution.
- ONNX export may work on one backend combination and fail on another even when
  the same source model code is used.
- If the smoke helper fails on a GPU host, confirm the PyTorch wheel matches the
  available CUDA runtime before blaming the exporter.
