---
name: models-training
description: "Fetch Nitrain architectures and train or evaluate Keras/TensorFlow
  or Torch/MONAI models."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# Models and training

Use this sub-skill when a user needs to discover an architecture, fetch a
pretrained network, build a `Trainer`, or run the CPU `TorchTrainer` path.

## What belongs here

- `fetch_architecture()` and `list_architectures()` for architecture discovery.
- `fetch_pretrained()` when the workflow needs pretrained network access.
- `Trainer` for Keras/TensorFlow models.
- `TorchTrainer` for the CPU Torch/MONAI path.
- Framework detection and trainer-default behavior.

## What does not belong here

- Dataset and reader construction: use `sub-skills/datasets-readers/`.
- Transform, sampler, and loader work: use `sub-skills/preprocessing-and-loading/`.
- Dataset-level prediction or explanation: use
  `sub-skills/prediction-and-explanation/`.

## Typical user requests

- "Create a U-Net or VGG architecture"
- "List available architectures"
- "Train a regression or segmentation model"
- "Use TorchTrainer with MONAI"
- "Load pretrained weights"

## Working pattern

1. Decide which framework the model actually uses: Keras/TensorFlow, torch, or
   monai-backed torch.
2. Pick `task='regression'`, `task='classification'`, or `task='segmentation'`
   when you want `Trainer` defaults.
3. Use `Loader` or `Loader.to_keras()` from the preprocessing sub-skill when the
   data needs batching first.
4. Keep training smoke tests tiny and CPU-only unless the user explicitly asks
   for a different backend.

## Read these references

- [references/api-reference.md](references/api-reference.md) for the
  verified signatures and default behavior.
- [references/workflows.md](references/workflows.md) for model-construction
  and training patterns.
- [references/troubleshooting.md](references/troubleshooting.md) for task
  mismatches, import quirks, and backend/version conflicts.

## Smoke checks

After installing dependencies, run the bundled helper [scripts/check_install.py](../../scripts/check_install.py):

```bash
python scripts/check_install.py --mode models
python scripts/check_install.py --mode torch
```

Use the first command for Keras/TensorFlow workflows and the second for the CPU
Torch/MONAI path.

## Key decisions

- `fetch_architecture(name, dim=None)` returns a callable from
  `antspynet.architectures`.
- `list_architectures()` returns `[name, dim]` pairs.
- `Trainer` compiles Keras models automatically when the framework is Keras.
- `TorchTrainer` delegates to the torch training helpers and needs an optimizer,
  loss, metrics, and device.
- `task=None` is only valid when you also provide the optimizer and loss.

## Common outcomes

- Keras models get compiled and can then call `fit`, `evaluate`, `predict`,
  `summary`, and `save`.
- Torch models are trained through the separate helper path rather than through
  `model.fit`.
- `Trainer` infers the framework from the model type string.

## Watch for these signals

- A `wrongtask` or missing-optimizer error usually means the trainer defaults
  were not selected correctly.
- `nitrain.fetch_pretrained` is a module object in this snapshot, so the actual
  function lives in `nitrain.models.fetch_pretrained`.
- `TorchTrainer` lives under `nitrain.trainers`, not the package root.
- The Torch/MONAI path is CPU-only in the verified snapshot.

## Before handing off

If the user really wants inference output post-processing, use the prediction
sub-skill instead of stretching this one further.
