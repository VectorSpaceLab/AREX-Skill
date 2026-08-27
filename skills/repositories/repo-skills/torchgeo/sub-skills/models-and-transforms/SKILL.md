---
name: models-and-transforms
description: "Use for TorchGeo model registry, pretrained weights, model
  builders, timm/SMP integration, and spectral/SAR/color/spatial/temporal
  transforms."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# TorchGeo models and transforms

Use this sub-skill for pre-trained geospatial models, weight enums, model registry queries, transform composition, spectral indices, and optional model dependency troubleshooting.

## Model registry

`torchgeo.models.api` registers named model builders and weights. Core helpers:

- `list_models()` returns registered model names.
- `get_model(name, *args, **kwargs)` instantiates a registered model builder.
- `get_model_weights(name_or_builder)` returns the `WeightsEnum` class associated with a model.
- `get_weight(full_enum_string)` returns one concrete weight enum value by its string representation.

Registered families at the distilled commit include Aurora, CopernicusFM, CROMA, DEO, DOFA, EarthLoc, OlmoEarth, Panopticon, Presto, ResNet, SatCLIP, ScaleMAE, Swin, Tessera, TileNet, UNet, and ViT variants.

## Weight and dependency rules

- Use `weights=None` for construction-only smoke tests.
- Passing a TorchGeo weight enum or enum string may download checkpoints through `get_state_dict`; check network/cache policy first.
- Some model families require optional extras (`microsoft-aurora`, `olmoearth-pretrain-minimal`, or other upstream packages). Guard optional imports with clear user guidance.
- When changing input channel counts, update both model construction parameters and any weight-loading adaptation logic.

## Transform families

- `torchgeo.transforms.indices` appends spectral indices such as NDVI, NBR, NDBI, NDSI, NDWI, MNDWI, and related normalized-difference features.
- SAR, color, spatial, and temporal transforms are in neighboring modules and are built around tensor/Kornia-style batch operations.
- Verify channel ordering before applying a spectral index. For example, NDVI needs NIR and red channel indexes in the image tensor.
- In Lightning workflows, put GPU-compatible Kornia augmentations in `on_after_batch_transfer` through datamodule augmentation fields.

## Read next

- [reference](references/models-and-transforms.md) for examples and verification candidates.
- Root [backend plan](../../references/backend-verification-plan.md) before running model/task smoke checks.
