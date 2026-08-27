---
name: model-architectures
description: "Instantiate, inspect, and debug fastMRI reconstruction model
  architectures safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# fastMRI Model Architectures

Use this sub-skill when an agent needs to choose, instantiate, inspect, smoke-test, or debug fastMRI reconstruction models without entering dataset loading, Lightning training loops, or metric/submission handling.

## Route

- Use raw `torch.nn.Module` classes from `fastmri.models` here: `Unet`, `NormUnet`, `VarNet`, `AdaptiveVarNet`, and policy/acquisition modules such as `LOUPEPolicy`.
- Use `Unet` for image-domain baseline reconstruction checks; use `VarNet` for multicoil k-space reconstruction with sensitivity-map estimation and cascaded data consistency.
- Use `NormUnet` as the complex-valued normalized U-Net block inside VarNet-style models, not as a drop-in replacement for image-domain `Unet` inputs.
- Treat `AdaptiveVarNet`, `LOUPEPolicy`, and feature/adaptive example families as advanced/experimental paths with version and environment caveats.
- For `SliceDataset`, masks, and data transforms, hand off to [data-loading](../data-loading/); for `UnetModule`, `VarNetModule`, training, validation, and test loops, hand off to [lightning-training](../lightning-training/).

## Bundled Guides

- Read [the model reference](references/model-reference.md) to get exact constructor signatures, input/output shapes, model-selection guidance, TorchScript evidence, and mask/low-frequency handling.
- Read [the offline pretrained inference guide](references/pretrained-inference.md) when adapting pretrained U-Net or VarNet inference while requiring a user-supplied local `state_dict` and avoiding hidden downloads.
- Read [the troubleshooting guide](references/troubleshooting.md) when diagnosing mask dtype/shape errors, pooling/crop failures, checkpoint mismatches, CUDA defaults, or adaptive/feature VarNet caveats.
- Run [the smoke shape script](scripts/smoke_model_shapes.py) to perform tiny CPU-only U-Net, `NormUnet`, VarNet, `AdaptiveVarNet`, and `LOUPEPolicy` instantiation/shape checks before touching real HDF5 data.

## Safe Defaults

- Start with `python scripts/smoke_model_shapes.py --model all --device cpu` from a copy or working directory where `fastmri` and `torch` are importable.
- Keep pretrained inference offline by requiring `--state_dict_file` or equivalent local checkpoint input; do not silently download model weights.
- Prefer explicit `num_low_frequencies` for VarNet smoke/debug runs when the mask's dense center region is known.
- Use exact mask class names when routing data questions: `EquiSpacedMaskFunc` and `EquispacedMaskFractionFunc` are distinct names in fastMRI.
