# FCOS Config and Model Catalog

## Config families

| Family | Typical files | Use |
| --- | --- | --- |
| Baseline ResNet FPN | `fcos_R_50_FPN_1x.yaml`, `fcos_R_101_FPN_2x.yaml` | Original paper-style FCOS configs. |
| Improved FCOS | `fcos_imprv_R_50_FPN_1x.yaml`, `fcos_imprv_R_101_FPN_2x.yaml` | Adds normalized regression, centerness-on-regression, center sampling, and GIoU. Recommended general baseline. |
| Deformable conv | names with `dcnv2` | Higher AP variants; require compiled deformable convolution support and compatible CUDA/PyTorch. |
| ResNeXt | names with `X_101` | Larger backbones; higher memory and runtime. |
| MobileNetV2 | names with `MNV2` | Lighter models for speed or lower memory; SyncBN variants need compatible PyTorch. |

## Selecting a config

- For a standard training/eval recipe, start with `fcos_imprv_R_50_FPN_1x`.
- For quick or lower-resource experimentation, inspect MobileNetV2 configs.
- For maximum reported AP, use larger ResNeXt/deformable configs only after extension/CUDA verification.
- For a custom dataset, adjust `DATASETS`, `MODEL.FCOS.NUM_CLASSES`, and possibly input/solver settings together.

## Model weights

The README documents external pretrained weights. Do not bundle weights in the skill. Use explicit local paths in `MODEL.WEIGHT` once weights are downloaded with user approval.
