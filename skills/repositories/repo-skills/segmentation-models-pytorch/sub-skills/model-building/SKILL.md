---
name: model-building
description: "Create and debug segmentation_models_pytorch model architectures,
  create_model calls, output shapes, auxiliary heads, and encoder freezing."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Model Building

Use this sub-skill when the task asks to create, choose, inspect, or debug a `segmentation_models_pytorch` semantic segmentation model. SMP models are PyTorch `torch.nn.Module` objects that consume NCHW tensors and return segmentation masks, or `(mask, label)` when an auxiliary classification head is enabled.

## Start Here

- Read [API Reference](references/api-reference.md) for supported architecture keys, class names, constructor parameters, `smp.create_model`, output contracts, and encoder freeze helpers.
- Read [Model Selection](references/model-selection.md) to choose between `Unet`, `FPN`, `DeepLabV3Plus`, `Segformer`, `DPT`, and the other SMP architectures.
- Read [Troubleshooting](references/troubleshooting.md) when model construction, pretrained weights, tensor shapes, aux outputs, or DPT image sizes fail.
- Run [model_smoke_test.py](scripts/model_smoke_test.py) to create a model offline and verify a deterministic tiny forward pass.

## Common Tasks

- **Create by class:** instantiate `smp.Unet`, `smp.FPN`, `smp.DeepLabV3Plus`, or another architecture class when the architecture is fixed in code.
- **Create by name:** use `smp.create_model(arch="unet", encoder_name="resnet34", encoder_weights=None, in_channels=1, classes=1)` for config-driven architecture selection.
- **Configure channels/classes:** set `in_channels` to the input tensor channel count and `classes` to the number of mask channels the model should emit.
- **Enable aux output:** pass `aux_params={"pooling": "avg", "classes": label_count, "dropout": 0.5, "activation": "sigmoid"}` and unpack `mask, label = model(x)`.
- **Freeze encoders:** call `model.freeze_encoder()` before decoder-only fine-tuning and `model.unfreeze_encoder()` when full-model training should resume.
- **Smoke check shapes:** run the bundled script with `encoder_weights=None` by default before wiring the model into a training or export workflow.

## Boundaries

- Encoder catalogs, `encoder_name` discovery, pretrained preprocessing functions, and input normalization belong in [Encoders And Preprocessing](../encoders-preprocessing/SKILL.md).
- Losses, metrics, dataloaders, optimizer loops, and validation logic belong in [Training And Evaluation](../training-evaluation/SKILL.md).
- Checkpoint save/load, Hugging Face Hub loading, TorchScript, ONNX, tracing, and deployment export belong in [Model Export](../model-export/SKILL.md).

## Minimal Pattern

```python
import torch
import segmentation_models_pytorch as smp

model = smp.create_model(
    arch="unet",
    encoder_name="resnet34",
    encoder_weights=None,
    in_channels=1,
    classes=1,
).eval()

x = torch.zeros(1, 1, 64, 64)
with torch.inference_mode():
    mask = model(x)
assert tuple(mask.shape) == (1, 1, 64, 64)
```
