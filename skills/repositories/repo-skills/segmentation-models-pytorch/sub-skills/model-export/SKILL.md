---
name: model-export
description: "Save, reload, share, and deployment-check
  segmentation_models_pytorch models with local directories, Hugging Face Hub,
  ONNX, TorchScript, torch.export, and torch.compile."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Model Export

Use this sub-skill when a task mentions `save_pretrained`, `from_pretrained`, changed class counts on load, Hugging Face Hub sharing, ONNX export, TorchScript, tracing, `torch.export`, or `torch.compile` readiness for Segmentation Models PyTorch (SMP).

## Route The Work

- For architecture, decoder, auxiliary-head, or model-constructor choices, read `../model-building/SKILL.md` first.
- For encoder selection, preprocessing functions, encoder weights, or encoder compatibility trade-offs, read `../encoders-preprocessing/SKILL.md` first.
- For training loops, losses, metrics, validation, or fine-tuning procedure, read `../training-evaluation/SKILL.md` first.
- For local save/load, Hub sharing, changed-output-head reloads, or deployment export checks, stay here.

## Core APIs

SMP segmentation model classes inherit Hugging Face Hub mixin behavior and can be saved with `model.save_pretrained(...)`. The package root exposes `segmentation_models_pytorch.from_pretrained(...)`, which reads the saved SMP config, reconstructs the original model class, and loads weights.

```python
import segmentation_models_pytorch as smp

model = smp.Unet("resnet34", encoder_weights=None, classes=1)
model.save_pretrained("my-smp-model", dataset="my-dataset", metrics={"miou": 0.91})
restored = smp.from_pretrained("my-smp-model")
```

Use `strict=False` when intentionally changing shape-dependent constructor arguments, especially `classes`, while reusing all compatible weights:

```python
model = smp.from_pretrained("my-smp-model", classes=5, strict=False)
```

That path drops mismatched tensors such as `segmentation_head.0.weight` and `segmentation_head.0.bias`, warns that the new head must be trained, and preserves matching weights.

## References

- `references/deployment-and-sharing.md`: local save/load, Hub publishing/loading, model-card metadata, preprocessing transform notes, and changed-class reloads.
- `references/export-compatibility.md`: ONNX, TorchScript, tracing, `torch.export`, and `torch.compile` readiness checks and caveats.
- `references/troubleshooting.md`: optional dependency, Hub, class mismatch, path/repo-id, and backend/export failure guidance.

## Bundled Checks

- `scripts/check_save_load.py`: creates a tiny local model, saves it, reloads with `smp.from_pretrained`, optionally checks `strict=False` class mismatch behavior, and prints JSON.
- `scripts/check_export_readiness.py`: reports installed Torch/SMP/export features, optional `onnx` presence, model compatibility flags, and optional dry-run forward output as JSON.

Run scripts from any project environment where `torch` and `segmentation_models_pytorch` are importable:

```bash
python path/to/model-export/scripts/check_save_load.py --class-mismatch
python path/to/model-export/scripts/check_export_readiness.py --dry-run
```

## Practical Rules

- Prefer `encoder_weights=None` for offline smoke tests and export probes; pretrained encoder weights can require network/cache access.
- Save model-card metadata with `dataset="..."` and `metrics={...}` when sharing a trained model.
- Save an inference preprocessing transform separately with a compatible library such as Albumentations when downstream users need identical normalization/resizing.
- Treat Hub push/load as optional: it requires `huggingface-hub`, credentials for private or write operations, and network access.
- Treat ONNX and runtime backends as optional deployment targets: check dependencies and run a representative input before promising compatibility.
