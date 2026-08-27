# Troubleshooting

## Changed Classes Or Head Shape Mismatch

Symptom: loading a checkpoint into a model with a different `classes` value raises size-mismatch errors, or `strict=False` emits a mismatched-keys warning.

Fix: pass the intended constructor override and `strict=False`:

```python
model = smp.from_pretrained("saved-model", classes=5, strict=False)
```

The warning is expected when the segmentation head changes shape. Train or fine-tune the new head before using predictions.

## Missing Optional Save/Hub Dependencies

Symptom: `save_pretrained`, `from_pretrained`, or Hub operations fail with import errors for `huggingface_hub` or `safetensors`.

Fix: install the missing optional dependency in the active project environment. `huggingface-hub` is required for Hub-backed load/push behavior, and `safetensors` is commonly used by Hub mixin save/load paths. Keep local save/load smoke tests separate from network-backed Hub tests.

## Hub Authentication Or Network Failure

Symptom: `push_to_hub=True` fails with authentication, permission, timeout, or repository-not-found errors.

Fix: verify that the repo id is correct, the token is available to the process, the token has write permission for pushes or read permission for private repos, and network access is allowed. For offline CI, save to a local directory and skip Hub push assertions.

## Local Path Versus Hub Repo Id Confusion

Symptom: `smp.from_pretrained("name")` unexpectedly tries to contact the Hub, or a Hub-like string is treated as the desired save directory.

Fix: use a clear filesystem path for local work, such as `./saved-model` or an absolute path outside public docs, and use `username/model-name` only for Hub repos. If loading locally, confirm the directory contains the saved SMP `config.json` and weights.

## Missing ONNX Dependency

Symptom: `import onnx` fails or the ONNX checker cannot run after `torch.onnx.export`.

Fix: install `onnx` for graph validation. Install `onnxruntime` only when you need runtime inference checks. The bundled readiness script reports whether `onnx` is importable without requiring it by default.

## Unsupported Dynamic Shape Or Backend

Symptom: ONNX export, `torch.export`, TorchScript, or `torch.compile` works for one shape/backend but fails for another.

Fix: first prove a static representative input. Then add dynamic batch/height/width axes one at a time. Compare eager and exported outputs on realistic image sizes. If the model requires input dimensions divisible by output stride, enforce padding or resizing before export and inference.

## Encoder Compile Or Export Incompatibility

Symptom: a model-level readiness flag is false, scripting raises a runtime error, or compile/export fails inside encoder code.

Fix: choose a deployment-friendly encoder, use `encoder_weights=None` for offline probes, and check encoder script/compile/export support before committing to a production export path. Timm and transformer-style encoders can have backend-specific limitations.

## Conversion Script Misuse

Symptom: a task tries to use DPT, SegFormer, or UPerNet conversion scripts for a normal trained SMP checkpoint.

Fix: do not use conversion scripts for ordinary user save/load. They are reference utilities for translating external checkpoint formats into SMP/Hugging Face artifacts. Use `model.save_pretrained`, `smp.from_pretrained`, and optional ONNX/Torch export checks for normal workflows.
