---
name: deployment-serving
description: "Export, optimize, validate, and serve Lightning models for
  prediction and production with checkpoints, pure PyTorch, TorchScript, ONNX,
  torch.export, pruning/quantization, and ServableModule flows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Lightning Deployment Serving

Use this sub-skill when the task is about prediction-only scripts, checkpoint loading for inference, removing Lightning from a production artifact, model export, inference optimization, or validating a `lightning.pytorch.serve` model before deployment.

## Start Here

1. Choose the deployment route before editing code: Lightning `Trainer.predict`, direct `model(x)` inference, pure `torch.nn.Module`, `torch.export`, ONNX, TorchScript, quantization/pruning, or `ServableModule` validation.
2. For Lightning inference, load with `MyModule.load_from_checkpoint("model.ckpt")`, call `model.eval()`, and run under `torch.no_grad()` or `torch.inference_mode()`.
3. Put request-independent inference math in `forward`; put dataloader-aware prediction logic, preprocessing, postprocessing, or Monte Carlo prediction in `predict_step`.
4. Use `Trainer.predict(model, dataloaders=..., return_predictions=...)` when Lightning should own batching/devices; use pure PyTorch when the production runtime should not depend on Lightning.
5. Run `python sub-skills/deployment-serving/scripts/servable_smoke.py --help` to validate that the bundled serving example is available without starting a long-lived server.

## Route Tasks

- Prediction loops, checkpoint inference, pure PyTorch extraction, ONNX/TorchScript/`torch.export`, pruning/quantization, or `lightning.pytorch.serve`: stay in this sub-skill.
- Training a model or creating checkpoints from scratch: route to `../training-core/SKILL.md`.
- Distributed production training, strategy selection, GPU/TPU/MPS/FSDP/DeepSpeed behavior, or hardware launch issues: route to `../distributed-accelerators/SKILL.md`.
- `LightningCLI`, YAML config, parser subclasses, or CLI wiring around deployment scripts: route to `../cli-configuration/SKILL.md`.

## References

- `references/serving-reference.md`: prediction APIs, checkpoint inference, `ServableModule`, `ServableModuleValidator`, and safe serving validation workflow.
- `references/export-workflows.md`: pure PyTorch conversion, `torch.export`, ONNX, TorchScript, TensorRT positioning, pruning, and quantization choices.
- `references/troubleshooting.md`: import/install failures, optional serving dependencies, validator misconfiguration, backend/hardware limits, and prediction/export failure signals.
- `scripts/servable_smoke.py`: tiny self-contained `ServableModule` shape/serialization smoke with `--help`, `--check-shape`, and optional one-shot validator mode.

## Quick Validation

```bash
python sub-skills/deployment-serving/scripts/servable_smoke.py --help
python sub-skills/deployment-serving/scripts/servable_smoke.py --check-shape
```

Expected signal: the help command prints options; the shape check imports Lightning and Torch, constructs a tiny `ServableModule`, validates payload serialization and `serve_step`, and prints `SERVABLE_SMOKE_OK`. The optional validator mode may require `fastapi`, `uvicorn`, `requests`, and a free localhost port.
